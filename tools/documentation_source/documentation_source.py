#!/usr/bin/env python
"""
Ferramenta para obtenção e processamento de documentação.

Esta ferramenta utiliza o Docling para obter e processar documentação
de diversas fontes (URLs, GitHub, arquivos locais) e disponibilizá-la
para uso pelos agentes.
"""

from typing import Type, List, Dict, Any, Optional
import os
import json
from urllib.parse import urlparse
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

try:
    # Importar Docling e suas dependências
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter
    from docling.exceptions import ConversionError
    from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
    from docling_core.types.doc.document import DoclingDocument
    from crewai.knowledge.source.crew_docling_source import CrewDoclingSource

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Diretório de resultados
RESULTS_DIR = "crews/pdca/resultados/documentacao/sources"


class DocumentationSourceInput(BaseModel):
    """Schema de entrada para a ferramenta DocumentationSourceTool."""
    
    sources: List[str] = Field(
        ..., 
        description="Lista de fontes de documentação (URLs, caminhos de arquivos locais, repositórios GitHub). URLs devem começar com http:// ou https://. Caminhos locais devem ser relativos ao diretório do projeto."
    )
    
    output_format: str = Field(
        default="markdown",
        description="Formato de saída desejado para a documentação: 'markdown', 'html', 'json' ou 'text'."
    )
    
    save_results: bool = Field(
        default=True,
        description="Se True, salva os resultados em arquivos para uso posterior. Se False, apenas retorna um resumo."
    )
    
    name: Optional[str] = Field(
        default=None,
        description="Nome opcional para identificar esta documentação nos arquivos de saída."
    )


class DocumentationSourceTool(BaseTool):
    """
    Ferramenta para obter documentação de diversas fontes.
    
    Esta ferramenta utiliza o Docling para processar documentação de várias fontes,
    incluindo URLs, repositórios GitHub e arquivos locais, tornando-a disponível 
    para uso pelos agentes em formato adequado.
    """
    
    name: str = "DocumentationSourceTool"
    description: str = (
        "Obtém e processa documentação de diversas fontes (URLs, GitHub, arquivos locais) "
        "tornando-a disponível para uso pelos agentes. Suporta múltiplos formatos como PDF, "
        "HTML, DOCX, Markdown e outros. O resultado pode ser salvo em arquivos para referência futura."
    )
    args_schema: Type[BaseModel] = DocumentationSourceInput
    
    def __init__(self):
        super().__init__()
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "O pacote docling é necessário para usar DocumentationSourceTool. "
                "Instale-o usando: pip install docling"
            )
        
        # Criar diretório de resultados se não existir
        os.makedirs(RESULTS_DIR, exist_ok=True)
    
    def _run(
        self, 
        sources: List[str],
        output_format: str = "markdown",
        save_results: bool = True,
        name: Optional[str] = None
    ) -> str:
        """
        Obtém e processa documentação de várias fontes.
        
        Args:
            sources: Lista de caminhos de arquivo ou URLs para obter documentação
            output_format: Formato de saída desejado ('markdown', 'html', 'json', 'text')
            save_results: Se deve salvar os resultados em arquivos
            name: Nome opcional para identificar esta documentação
            
        Returns:
            Resumo do conteúdo obtido e processado ou caminho para os arquivos salvos
        """
        try:
            # Verificar se há fontes
            if not sources or len(sources) == 0:
                return "Erro: Nenhuma fonte de documentação fornecida."
            
            # Validar formato de saída
            valid_formats = ["markdown", "html", "json", "text"]
            if output_format.lower() not in valid_formats:
                return f"Erro: Formato de saída '{output_format}' não suportado. Formatos válidos: {', '.join(valid_formats)}"
            
            # Usar o Docling para processar as fontes
            docling_source = CrewDoclingSource(file_paths=sources)
            docling_source.add()
            
            # Obter chunks processados
            chunks = docling_source.chunks
            total_chunks = len(chunks)
            total_sources = len(sources)
            
            if total_chunks == 0:
                return "Aviso: Nenhum conteúdo foi extraído das fontes fornecidas. Verifique se as fontes são válidas."
            
            # Organizar resultados
            results = {
                "meta": {
                    "total_sources": total_sources,
                    "total_chunks": total_chunks,
                    "sources": sources,
                    "format": output_format
                },
                "chunks": chunks
            }
            
            # Se solicitado, salvar resultados em arquivos
            if save_results:
                result_files = self._save_results(results, output_format, name)
                
                # Retornar resumo com informações sobre os arquivos salvos
                return self._format_summary(results, result_files)
            else:
                # Retornar apenas o resumo sem salvar arquivos
                return self._format_summary(results, None)
                
        except Exception as e:
            return f"Erro ao processar documentação: {str(e)}"
    
    def _save_results(self, results: Dict[str, Any], output_format: str, name: Optional[str] = None) -> Dict[str, str]:
        """
        Salva os resultados em arquivos no formato especificado.
        
        Args:
            results: Resultados a serem salvos
            output_format: Formato de saída
            name: Nome base para os arquivos (opcional)
            
        Returns:
            Dicionário com caminhos para os arquivos salvos
        """
        # Criar nome base para os arquivos
        timestamp = self._get_timestamp()
        base_name = f"{name or 'doc'}-{timestamp}" if name else f"documentation-{timestamp}"
        
        saved_files = {}
        
        # Salvar metadados sempre em JSON
        meta_file = os.path.join(RESULTS_DIR, f"{base_name}-meta.json")
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(results["meta"], f, indent=2, ensure_ascii=False)
        saved_files["meta"] = meta_file
        
        # Salvar conteúdo no formato especificado
        if output_format == "json":
            # Salvar como JSON (um arquivo por chunk)
            chunks_dir = os.path.join(RESULTS_DIR, f"{base_name}-chunks")
            os.makedirs(chunks_dir, exist_ok=True)
            
            for i, chunk in enumerate(results["chunks"]):
                chunk_file = os.path.join(chunks_dir, f"chunk-{i+1}.json")
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    json.dump({"content": chunk}, f, indent=2, ensure_ascii=False)
            
            saved_files["chunks_dir"] = chunks_dir
            
        elif output_format == "markdown" or output_format == "text":
            # Salvar como texto/markdown (um arquivo único)
            ext = ".md" if output_format == "markdown" else ".txt"
            content_file = os.path.join(RESULTS_DIR, f"{base_name}{ext}")
            
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(f"# Documentação Processada\n\n")
                f.write(f"Total de fontes: {results['meta']['total_sources']}\n")
                f.write(f"Total de chunks: {results['meta']['total_chunks']}\n\n")
                
                f.write("## Fontes\n\n")
                for i, source in enumerate(results['meta']['sources']):
                    f.write(f"{i+1}. `{source}`\n")
                
                f.write("\n## Conteúdo\n\n")
                for i, chunk in enumerate(results["chunks"]):
                    f.write(f"### Chunk {i+1}\n\n")
                    f.write(f"{chunk}\n\n")
                    f.write("---\n\n")
            
            saved_files["content"] = content_file
            
        elif output_format == "html":
            # Salvar como HTML
            html_file = os.path.join(RESULTS_DIR, f"{base_name}.html")
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentação Processada</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .meta {{ background: #f8f8f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .chunk {{ background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }}
        .source {{ font-family: monospace; background: #f0f0f0; padding: 5px; }}
    </style>
</head>
<body>
    <h1>Documentação Processada</h1>
    
    <div class="meta">
        <p><strong>Total de fontes:</strong> {results['meta']['total_sources']}</p>
        <p><strong>Total de chunks:</strong> {results['meta']['total_chunks']}</p>
        
        <h2>Fontes</h2>
        <ol>
""")
                
                for source in results['meta']['sources']:
                    f.write(f'            <li><span class="source">{source}</span></li>\n')
                
                f.write("""        </ol>
    </div>
    
    <h2>Conteúdo</h2>
""")
                
                for i, chunk in enumerate(results["chunks"]):
                    f.write(f"""    <div class="chunk">
        <h3>Chunk {i+1}</h3>
        <div>{chunk.replace('\n', '<br>')}</div>
    </div>
""")
                
                f.write("""</body>
</html>""")
            
            saved_files["html"] = html_file
        
        return saved_files
    
    def _format_summary(self, results: Dict[str, Any], saved_files: Optional[Dict[str, str]] = None) -> str:
        """
        Formata um resumo dos resultados processados.
        
        Args:
            results: Resultados processados
            saved_files: Informações sobre arquivos salvos (opcional)
            
        Returns:
            Resumo formatado
        """
        summary = f"""## Resultado do Processamento de Documentação

**Fontes processadas:** {results['meta']['total_sources']}
**Chunks extraídos:** {results['meta']['total_chunks']}

### Fontes:
"""
        
        for i, source in enumerate(results['meta']['sources']):
            summary += f"{i+1}. `{source}`\n"
        
        if saved_files:
            summary += f"""
### Arquivos Salvos:
"""
            for file_type, file_path in saved_files.items():
                pretty_path = file_path.replace("\\", "/")
                if file_type == "meta":
                    summary += f"- **Metadados:** {pretty_path}\n"
                elif file_type == "content":
                    summary += f"- **Conteúdo:** {pretty_path}\n"
                elif file_type == "html":
                    summary += f"- **HTML:** {pretty_path}\n"
                elif file_type == "chunks_dir":
                    summary += f"- **Diretório de chunks:** {pretty_path}\n"
        
        # Adicionar amostra do conteúdo
        summary += f"""
### Amostra do Conteúdo:
"""
        # Mostrar no máximo 3 chunks ou menos se houver menos
        num_chunks_to_show = min(3, len(results['chunks']))
        
        for i in range(num_chunks_to_show):
            chunk = results['chunks'][i]
            # Limitar o tamanho do chunk para não sobrecarregar a saída
            preview = chunk[:500] + "..." if len(chunk) > 500 else chunk
            summary += f"""
#### Chunk {i+1}:
```
{preview}
```
"""
        
        if num_chunks_to_show < len(results['chunks']):
            summary += f"\n... mais {len(results['chunks']) - num_chunks_to_show} chunks disponíveis nos arquivos salvos."
        
        return summary
    
    def _get_timestamp(self) -> str:
        """Retorna um timestamp formatado para uso em nomes de arquivo."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d-%H%M%S")
    
    def _validate_url(self, url: str) -> bool:
        """Valida se uma string é uma URL válida."""
        try:
            result = urlparse(url)
            return all([
                result.scheme in ("http", "https"),
                result.netloc,
            ])
        except Exception:
            return False


if __name__ == "__main__":
    # Exemplo de uso da ferramenta
    tool = DocumentationSourceTool()
    
    # Exemplo 1: Obter documentação de uma URL
    resultado1 = tool.run(
        sources=["https://docs.python.org/3/library/index.html"],
        output_format="markdown",
        save_results=True,
        name="python-docs"
    )
    
    print(resultado1)
    
    # Exemplo 2: Obter documentação de um repositório GitHub (README)
    resultado2 = tool.run(
        sources=["https://raw.githubusercontent.com/crewai/crewai/main/README.md"],
        output_format="html",
        save_results=True,
        name="crewai-readme"
    )
    
    print(resultado2)
