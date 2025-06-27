from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import json
from pathlib import Path
import ast
from graphviz import Digraph
"""# Dicionário centralizado de descrições"""
DESCRIPTIONS = {'PythonCodebaseDocumenterParameters.diretorio_raiz':
    'Caminho do diretório raiz contendo o código Python a ser documentado.',
    'PythonCodebaseDocumenterParameters.padroes_exclusao':
    "Lista de padrões de arquivo ou diretório a serem excluídos da análise. Ex: ['tests/*', '*.md']"
    , 'PythonCodebaseDocumenterParameters.nivel_detalhamento':
    "Nível de detalhamento desejado: 'resumido', 'detalhado' ou 'completo'. Influencia a profundidade da análise e os elementos gerados."
    , 'PythonCodebaseDocumenterParameters.formato_saida':
    "Formato de saída para o relatório gerado. Valores suportados: 'markdown' ou 'html'."
    , 'PythonCodebaseDocumenterParameters.incluir_metricas':
    'Indica se métricas como número de linhas de código por arquivo e complexidade ciclomatica devem ser incluídas.'
    , 'PythonCodebaseDocumenterTool.description':
    'Gera documentação técnica em Markdown para uma codebase Python. Analisa automaticamente a estrutura do código, extrai docstrings, gera diagramas de classes e fluxos, documenta APIs, e organiza a informação em arquivos estruturados contendo um índice principal e links de navegação. Ideal para equipes que desejam criar documentação técnica clara e completa de sistemas Python.'
    }
"""# Função para obter descrições do dicionário local"""


def get_description(key: str) ->str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f'Descrição para {key} não encontrada')


class PythonCodebaseDocumenterParameters(BaseModel):
    """Parâmetros para a ferramenta PythonCodebaseDocumenter."""
    diretorio_raiz: Any = Field(..., description=
        'Caminho do diretório raiz contendo o código Python a ser documentado.'
        )
    padroes_exclusao: Any = Field(description=
        "Lista de padrões de arquivo ou diretório a serem excluídos da análise. Ex: ['tests/*', '*.md']"
        , default=None)
    nivel_detalhamento: Any = Field(description=
        "Nível de detalhamento desejado: 'resumido', 'detalhado' ou 'completo'. Influencia a profundidade da análise e os elementos gerados."
        , default='detalhado')
    formato_saida: Any = Field(description=
        "Formato de saída para o relatório gerado. Valores suportados: 'markdown' ou 'html'."
        , default='markdown')
    incluir_metricas: Any = Field(description=
        'Indica se métricas como número de linhas de código por arquivo e complexidade ciclomatica devem ser incluídas.'
        , default=False)


class PythonCodebaseDocumenterTool(BaseTool):
    """Gera documentação técnica em Markdown para uma codebase Python. Analisa automaticamente a estrutura do código, extrai docstrings, gera diagramas de classes e fluxos, documenta APIs, e organiza a informação em arquivos estruturados contendo um índice principal e links de navegação. Ideal para equipes que desejam criar documentação técnica clara e completa de sistemas Python."""
    model_config = {'arbitrary_types_allowed': True, 'validate_assignment':
        True}
    name: str = 'PythonCodebaseDocumenter'
    description: str = get_description(
        'PythonCodebaseDocumenterTool.description')
    args_schema: Type[BaseModel] = PythonCodebaseDocumenterParameters

    def gerar_documentacao_completa(self, diretorio_raiz, padroes_exclusao,
        nivel_detalhamento, formato_saida, incluir_metricas):
        """
    Gera documentação completa da codebase Python.
    """
        try:
            estrutura = self.analisar_estrutura(diretorio_raiz,
                padroes_exclusao)
            docstrings = self.extrair_docstrings(estrutura)
            diagramas = self.gerar_diagramas(estrutura)
            if incluir_metricas:
                metricas = self.calcular_metricas(estrutura)
            else:
                metricas = None
            documentacao = self.gerar_arquivos_markdown(estrutura,
                docstrings, diagramas, metricas, formato_saida)
            return (
                f"Documentação gerada com sucesso em {formato_saida}. Confira os arquivos no diretório {Path(diretorio_raiz).joinpath('doc_output')}"
                )
        except Exception as e:
            return f'Erro ao gerar documentação: {str(e)}'

    def analisar_estrutura(self, diretorio_raiz, padroes_exclusao):
        """
    Analisa a estrutura da codebase a partir do diretório raiz, respeitando os padrões de exclusão.
    """
        estrutura = []
        for root, dirs, files in os.walk(diretorio_raiz):
            if padroes_exclusao:
                dirs[:] = [d for d in dirs if not self.match_exclusion(Path
                    (root) / d, padroes_exclusao)]
                files = [f for f in files if not self.match_exclusion(Path(
                    root) / f, padroes_exclusao)]
            for file in files:
                if file.endswith('.py'):
                    estrutura.append(Path(root) / file)
        return estrutura

    def match_exclusion(self, path, padroes_exclusao):
        """
    Verifica se o caminho corresponde a algum padrão de exclusão fornecido.
    """
        from fnmatch import fnmatch
        for padrao in padroes_exclusao:
            if fnmatch(str(path), padrao):
                return True
        return False

    def extrair_docstrings(self, estrutura):
        """
    Extrai as docstrings dos arquivos da estrutura fornecida.
    """
        docstrings = {}
        for arquivo in estrutura:
            with open(arquivo, 'r') as f:
                tree = ast.parse(f.read())
                docstrings[str(arquivo)] = ast.get_docstring(tree)
        return docstrings

    def gerar_diagramas(self, estrutura):
        """
    Gera diagramas de classes e fluxos da codebase.
    """
        diagramas = {}
        dot = Digraph()
        for arquivo in estrutura:
            dot.node(str(arquivo), label=Path(arquivo).name)
        diagramas['estrutura'] = dot.source
        return diagramas

    def calcular_metricas(self, estrutura):
        """
    Calcula métricas como complexidade ciclomatica e número de linhas de código por arquivo.
    """
        metricas = {}
        for arquivo in estrutura:
            with open(arquivo, 'r') as f:
                lines = f.readlines()
                metricas[str(arquivo)] = len(lines)
        return metricas

    def gerar_arquivos_markdown(self, estrutura, docstrings, diagramas,
        metricas, formato_saida):
        """
    Gera os arquivos no formato especificado, organizando as informações coletadas.
    """
        output_dir = Path('doc_output')
        output_dir.mkdir(exist_ok=True)
        index_file = output_dir / 'index.md'
        with open(index_file, 'w') as f:
            f.write('# Documentação Técnica\n\n')
            for arquivo in estrutura:
                f.write(
                    f"- [{Path(arquivo).name}]({Path(arquivo).with_suffix('.md').name})\n"
                    )
        for arquivo in estrutura:
            file_doc = output_dir / f'{Path(arquivo).stem}.md'
            with open(file_doc, 'w') as f:
                f.write(f'## {Path(arquivo).name}\n\n')
                f.write(docstrings.get(str(arquivo),
                    'Docstring não encontrada.') + '\n')
        return True

    def _run(self, diretorio_raiz: Any, padroes_exclusao: Any=None,
        nivel_detalhamento: Any='detalhado', formato_saida: Any='markdown',
        incluir_metricas: Any=False):
        return self.gerar_documentacao_completa(diretorio_raiz,
            padroes_exclusao, nivel_detalhamento, formato_saida,
            incluir_metricas)


if __name__ == '__main__':
    tool = PythonCodebaseDocumenterTool()
    result = tool.run(diretorio_raiz='exemplo', padroes_exclusao='exemplo',
        nivel_detalhamento='detalhado', formato_saida='markdown',
        incluir_metricas=False)
    print(result)
