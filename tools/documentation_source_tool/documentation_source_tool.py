"""
Ferramenta para obtenção de documentação de diversas fontes.

Esta ferramenta encapsula a funcionalidade do DocumentationSourceTool e
a disponibiliza para uso por agentes em uma interface simplificada.
"""

from typing import Type, List, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging
import os
import json
from pathlib import Path
import tempfile
import shutil

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importações do Docling
try:
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter
    from docling.exceptions import ConversionError
    from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
    from docling_core.types.doc.document import DoclingDocument

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Diretório de resultados
RESULTS_DIR = os.path.join("crews", "pdca", "resultados", "documentacao", "sources")

# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "DocumentationSourceToolInput.sources": "Lista de fontes de documentação (URLs, caminhos de arquivos locais, repositórios). URLs devem começar com http:// ou https://.",
    
    "DocumentationSourceToolInput.output_format": "Formato de saída desejado: 'markdown', 'html', 'json' ou 'text'.",
    
    "DocumentationSourceToolInput.save_results": "Define se os resultados serão salvos em arquivos para uso posterior.",
    
    "DocumentationSourceToolInput.name": "Nome opcional para identificar esta documentação nos arquivos de saída.",
    
    "DocumentationSourceToolWrapper.description": """Obtém e processa documentação de diversas fontes como URLs, repositórios de código e arquivos locais.
Suporta múltiplos formatos incluindo PDF, HTML, DOCX, Markdown e muitos outros.
A documentação é processada e pode ser salva em formatos de saída como markdown, HTML ou JSON.
Ideal para obter informações técnicas de APIs, frameworks, ou documentação de usuário para uso pelos agentes."""
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

class DocumentationSourceToolInput(BaseModel):
    """Esquema de entrada para a ferramenta DocumentationSourceToolWrapper."""
    
    sources: List[str] = Field(
        ..., 
        description=get_description("DocumentationSourceToolInput.sources")
    )
    
    output_format: str = Field(
        default="markdown",
        description=get_description("DocumentationSourceToolInput.output_format")
    )
    
    save_results: bool = Field(
        default=True,
        description=get_description("DocumentationSourceToolInput.save_results")
    )
    
    name: Optional[str] = Field(
        default=None,
        description=get_description("DocumentationSourceToolInput.name")
    )

class DocumentationSourceTool(BaseTool):
    """Ferramenta para processamento interno de documentação."""
    
    name: str = "DocumentationSourceTool_Internal"
    description: str = "Ferramenta interna para processamento de documentação"
    args_schema: Type[BaseModel] = DocumentationSourceToolInput
    
    def __init__(self):
        super().__init__()
        if not DOCLING_AVAILABLE:
            raise ImportError(
                "O pacote docling é necessário para usar esta ferramenta. "
                "Instale-o usando: pip install docling"
            )
        
        # Garantir que o diretório de resultados exista
        os.makedirs(RESULTS_DIR, exist_ok=True)
    
    def _run(
        self, 
        sources: List[str],
        output_format: str = "markdown",
        save_results: bool = True,
        name: Optional[str] = None
    ) -> str:
        """Processa documentação de várias fontes."""
        try:
            # Verificar se há fontes
            if not sources or len(sources) == 0:
                return "Erro: Nenhuma fonte de documentação fornecida."
            
            # Criar diretório temporário para trabalho
            with tempfile.TemporaryDirectory() as temp_dir:
                # Processar cada fonte
                chunks = []
                processed_sources = []
                
                for source in sources:
                    try:
                        # Converter para caminho absoluto se for caminho local
                        if not source.startswith(("http://", "https://")):
                            if os.path.exists(source):
                                source = os.path.abspath(source)
                            else:
                                logger.warning(f"Fonte não encontrada: {source}")
                                continue
                        
                        # Usar o DocumentConverter do Docling
                        converter = DocumentConverter(allowed_formats=[
                            InputFormat.MD, InputFormat.PDF, InputFormat.DOCX,
                            InputFormat.HTML, InputFormat.IMAGE, InputFormat.XLSX
                        ])
                        
                        # Converter documento
                        try:
                            # Para URLs, criar um arquivo temporário
                            source_path = source
                            
                            # Converter o documento
                            result = next(converter.convert_all([source_path]))
                            doc = result.document
                            
                            # Dividir em chunks para processamento
                            chunker = HierarchicalChunker()
                            doc_chunks = [chunk.text for chunk in chunker.chunk(doc)]
                            chunks.extend(doc_chunks)
                            processed_sources.append(source)
                            
                        except Exception as e:
                            logger.error(f"Erro ao processar fonte {source}: {str(e)}")
                    except Exception as source_error:
                        logger.error(f"Erro com fonte {source}: {str(source_error)}")
                
                # Verificar se temos resultados
                if not chunks:
                    return "Nenhum conteúdo foi extraído das fontes fornecidas."
                
                # Organizar resultados
                results = {
                    "meta": {
                        "total_sources": len(processed_sources),
                        "total_chunks": len(chunks),
                        "sources": processed_sources,
                        "format": output_format
                    },
                    "chunks": chunks
                }
                
                # Salvar resultados se solicitado
                if save_results:
                    timestamp = self._get_timestamp()
                    base_name = f"{name or 'doc'}-{timestamp}" if name else f"documentation-{timestamp}"
                    
                    # Salvar metadados
                    meta_file = os.path.join(RESULTS_DIR, f"{base_name}-meta.json")
                    with open(meta_file, 'w', encoding='utf-8') as f:
                        json.dump(results["meta"], f, indent=2, ensure_ascii=False)
                    
                    # Salvar conteúdo no formato especificado
                    content_file = os.path.join(RESULTS_DIR, f"{base_name}.{output_format}")
                    
                    with open(content_file, 'w', encoding='utf-8') as f:
                        f.write("# Documentação Processada\n\n")
                        f.write(f"Total de fontes: {len(processed_sources)}\n")
                        f.write(f"Total de chunks: {len(chunks)}\n\n")
                        
                        f.write("## Fontes\n\n")
                        for i, source in enumerate(processed_sources):
                            f.write(f"{i+1}. `{source}`\n")
                        
                        f.write("\n## Conteúdo\n\n")
                        for i, chunk in enumerate(chunks):
                            f.write(f"### Chunk {i+1}\n\n")
                            f.write(f"{chunk}\n\n")
                            f.write("---\n\n")
                    
                    # Formatar resumo com informações de arquivos
                    return self._format_summary(results, {
                        "meta": meta_file,
                        "content": content_file
                    })
                else:
                    # Apenas resumo
                    return self._format_summary(results)
                    
        except Exception as e:
            logger.error(f"Erro no processamento: {str(e)}")
            return f"Erro ao processar documentação: {str(e)}"
    
    def _format_summary(self, results, saved_files=None):
        """Formata um resumo dos resultados."""
        summary = f"""## Resultado do Processamento de Documentação

**Fontes processadas:** {results['meta']['total_sources']}
**Chunks extraídos:** {results['meta']['total_chunks']}

### Fontes:
"""
        
        for i, source in enumerate(results['meta']['sources']):
            summary += f"{i+1}. `{source}`\n"
        
        if saved_files:
            summary += f"\n### Arquivos Salvos:\n"
            for file_type, file_path in saved_files.items():
                pretty_path = file_path.replace("\\", "/")
                summary += f"- **{file_type.capitalize()}:** {pretty_path}\n"
        
        # Amostra do conteúdo
        summary += f"\n### Amostra do Conteúdo:\n"
        num_chunks_to_show = min(3, len(results['chunks']))
        
        for i in range(num_chunks_to_show):
            chunk = results['chunks'][i]
            preview = chunk[:300] + "..." if len(chunk) > 300 else chunk
            summary += f"\n**Chunk {i+1}:**\n```\n{preview}\n```\n"
        
        if num_chunks_to_show < len(results['chunks']):
            summary += f"\n... mais {len(results['chunks']) - num_chunks_to_show} chunks disponíveis nos arquivos salvos."
        
        return summary
    
    def _get_timestamp(self):
        """Retorna um timestamp formatado."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d-%H%M%S")


class DocumentationSourceToolWrapper(BaseTool):
    """Ferramenta para obtenção e processamento de documentação de diversas fontes."""
    
    name: str = "DocumentationSourceTool"
    description: str = get_description("DocumentationSourceToolWrapper.description")
    args_schema: Type[BaseModel] = DocumentationSourceToolInput

    def _run(
        self,
        sources: List[str],
        output_format: str = "markdown",
        save_results: bool = True,
        name: Optional[str] = None
    ) -> str:
        """Executa o processo de obtenção e processamento de documentação.
        
        Args:
            sources: Lista de fontes de documentação (URLs, caminhos de arquivos)
            output_format: Formato de saída desejado
            save_results: Se deve salvar os resultados em arquivos
            name: Nome opcional para identificar esta documentação
            
        Returns:
            Resumo do processamento ou mensagem de erro
        """
        try:
            logger.info(f"Iniciando obtenção de documentação de {len(sources)} fontes")
            
            # Criar instância da ferramenta interna
            tool = DocumentationSourceTool()
            
            # Executar a ferramenta
            resultado = tool._run(
                sources=sources,
                output_format=output_format,
                save_results=save_results,
                name=name
            )
            
            logger.info("Documentação obtida com sucesso")
            
            return resultado
            
        except Exception as e:
            error_msg = f"Erro ao obter documentação: {str(e)}"
            logger.error(error_msg)
            return f"""
## ❌ Erro na Obtenção de Documentação

**Detalhes do erro:** {error_msg}

**Verifique:**
1. Se as URLs fornecidas são válidas e acessíveis
2. Se os caminhos de arquivo existem e possuem permissão de leitura
3. Se o Docling está instalado corretamente no ambiente
"""

if __name__ == '__main__':
    # Exemplo de uso da ferramenta
    tool = DocumentationSourceToolWrapper()
    
    # Exemplo: Obter documentação da página do CrewAI
    resultado = tool.run(
        sources=["https://docs.crewai.com/introduction"],
        output_format="markdown",
        save_results=True,
        name="crewai-docs"
    )
    
    print(resultado)
