from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import ast
import inspect
import json
import graphviz
import matplotlib.pyplot as plt
from radon.complexity import cc_visit
from collections import defaultdict
"""# Dicionário centralizado de descrições"""
DESCRIPTIONS = {'DocMakerPythonParameters.diretorio_raiz':
    'Path do diretório raiz contendo o codebase Python a ser documentado.',
    'DocMakerPythonParameters.padroes_exclusao':
    "Lista de padrões para exclusão de arquivos ou diretórios. Exemplo: ['tests/', 'venv/']"
    , 'DocMakerPythonParameters.nivel_detalhamento':
    'Nível de granularidade da documentação: 1 (básico), 2 (intermediário), 3 (detalhado).'
    , 'DocMakerPythonParameters.formato_saida':
    "Formato dos diagramas gerados pela ferramenta ('png' ou 'svg').",
    'DocMakerPythonParameters.incluir_metricas':
    'Se definido como True, inclui métricas adicionais (como complexidade ciclômica) na documentação.'
    , 'DocMakerPythonTool.description':
    'Gera documentação técnica consolidada em formato Markdown para codebases Python. A ferramenta analisa automaticamente a estrutura do código, extrai docstrings, gera diagramas de classes e fluxos, e documenta APIs internas e externas, criando arquivos Markdown completos e estruturados com índice e links navegáveis.'
    }
"""# Função para obter descrições do dicionário local"""


def get_description(key: str) ->str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f'Descrição para {key} não encontrada')


class DocMakerPythonParameters(BaseModel):
    """Parâmetros para a ferramenta DocMakerPython."""
    diretorio_raiz: str = Field(..., description=
        'Path do diretório raiz contendo o codebase Python a ser documentado.')
    padroes_exclusao: Any = Field(description=
        "Lista de padrões para exclusão de arquivos ou diretórios. Exemplo: ['tests/', 'venv/']"
        , default=[])
    nivel_detalhamento: int = Field(description=
        'Nível de granularidade da documentação: 1 (básico), 2 (intermediário), 3 (detalhado).'
        , default=2)
    formato_saida: str = Field(..., description=
        "Formato dos diagramas gerados pela ferramenta ('png' ou 'svg').")
    incluir_metricas: bool = Field(description=
        'Se definido como True, inclui métricas adicionais (como complexidade ciclômica) na documentação.'
        , default=False)


class DocMakerPythonTool(BaseTool):
    """Gera documentação técnica consolidada em formato Markdown para codebases Python. A ferramenta analisa automaticamente a estrutura do código, extrai docstrings, gera diagramas de classes e fluxos, e documenta APIs internas e externas, criando arquivos Markdown completos e estruturados com índice e links navegáveis."""
    model_config = {'arbitrary_types_allowed': True, 'validate_assignment':
        True}
    name: str = 'DocMakerPython'
    description: str = get_description('DocMakerPythonTool.description')
    args_schema: Type[BaseModel] = DocMakerPythonParameters

    def gerar_documentacao(self, diretorio_raiz, padroes_exclusao,
        nivel_detalhamento, formato_saida, incluir_metricas):
        """Gera documentação consolidada em Markdown para o diretório raiz fornecido."""
        try:
            if not os.path.exists(diretorio_raiz):
                raise FileNotFoundError(
                    f"O diretório '{diretorio_raiz}' não foi encontrado.")
            doc_data = self.analisar_codebase(diretorio_raiz, padroes_exclusao)
            diagramas = self.gerar_diagramas(doc_data, formato_saida)
            markdown = self.criar_markdown(doc_data, diagramas,
                nivel_detalhamento, incluir_metricas)
            markdown_path = os.path.join(diretorio_raiz, 'DOCUMENTATION.md')
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            return f'Documentação gerada com sucesso em: {markdown_path}'
        except Exception as e:
            return f'Erro ao gerar documentação: {str(e)}'

    def analisar_codebase(self, diretorio_raiz, padroes_exclusao):
        """Analisa o código Python no diretório raiz e retorna a estrutura com docstrings, classes e métodos."""
        estrutura = defaultdict(list)
        for root, dirs, files in os.walk(diretorio_raiz):
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in
                padroes_exclusao]
            files = [f for f in files if f.endswith('.py')]
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())
                    estrutura[file_path].extend([node for node in tree.body if
                        isinstance(node, (ast.FunctionDef, ast.ClassDef))])
                except Exception as e:
                    estrutura[file_path].append(
                        f'Erro ao analisar arquivo: {str(e)}')
        return estrutura

    def gerar_diagramas(self, estrutura, formato_saida):
        """Gera diagramas de classes e fluxos baseado na estrutura extraída."""
        diagrams = {}
        try:
            for caminho, elementos in estrutura.items():
                dot = graphviz.Digraph(format=formato_saida)
                dot.attr('node', shape='rectangle')
                for elemento in elementos:
                    if isinstance(elemento, ast.ClassDef):
                        dot.node(elemento.name, label=elemento.name)
                diagram_path = caminho.replace('.py',
                    f'_diagram.{formato_saida}')
                dot.render(diagram_path)
                diagrams[caminho] = diagram_path
        except Exception as e:
            diagrams['Erro'] = str(e)
        return diagrams

    def criar_markdown(self, estrutura, diagramas, nivel_detalhamento,
        incluir_metricas):
        """Cria o arquivo Markdown documentado com base nos dados fornecidos."""
        markdown = '# Documentação da Codebase\n\n'
        for path, elementos in estrutura.items():
            markdown += f'## Arquivo: {os.path.basename(path)}\n\n'
            for elemento in elementos:
                if isinstance(elemento, ast.ClassDef):
                    markdown += f'### Classe: {elemento.name}\n\n'
                    markdown += f'Docstring: {ast.get_docstring(elemento)}\n\n'
                if isinstance(elemento, ast.FunctionDef):
                    markdown += f'### Método/Function: {elemento.name}\n\n'
                    markdown += f'Docstring: {ast.get_docstring(elemento)}\n\n'
            if path in diagramas:
                markdown += (
                    f'![Diagrama](./{os.path.basename(diagramas[path])})\n\n')
        return markdown

    def _run(self, diretorio_raiz: str, padroes_exclusao: Any,
        nivel_detalhamento: int=[], formato_saida: str=2, incluir_metricas:
        bool=False):
        return self.gerar_documentacao(diretorio_raiz, padroes_exclusao,
            nivel_detalhamento, formato_saida, incluir_metricas)


if __name__ == '__main__':
    tool = DocMakerPythonTool()
    result = tool.run(diretorio_raiz='exemplo', padroes_exclusao=[],
        nivel_detalhamento=2, formato_saida='exemplo', incluir_metricas=False)
    print(result)
