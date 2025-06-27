#!/usr/bin/env python
"""
Tool para avaliação inteligente e criação de ferramentas.

Esta tool encapsula a FerramentasInteligentesCrew, permitindo que seja
utilizada como uma ferramenta CrewAI por outros agentes quando precisarem
criar, adaptar ou encontrar ferramentas específicas para suas necessidades.
"""

from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging
import os
import sys

# Adicionar diretório raiz do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../")))

# Importar a equipe especializada em avaliação e criação de ferramentas
from crews.tool_creation_crew.tool_creation_crew import ToolCreationCrew

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "IntelligentToolsInput.necessidade": "Descrição da necessidade de ferramenta do agente solicitante.",
    "IntelligentToolsInput.contexto": "Contexto em que a ferramenta será utilizada.",
    "IntelligentToolsInput.funcionalidades_requeridas": "Lista de funcionalidades requeridas, separadas por vírgula.",
    "IntelligentToolsInput.parametros_esperados": "Lista de parâmetros esperados, separados por vírgula.",
    "IntelligentToolsInput.tipo_resultado_esperado": "Descrição do conteúdo semântico que a ferramenta deve produzir em formato text-based para os agentes (ex: 'relatório estruturado de análise de código', 'listagem formatada de arquivos com descrições', 'resultados de operações financeiras com detalhes', 'status de deploys com links').",
    "IntelligentToolsInput.urgencia": "Nível de urgência da necessidade (baixa, média, alta).",
    "IntelligentToolsTool.description": "Tool especializada para avaliação inteligente e criação de ferramentas. Analisa a necessidade de ferramentas e: \n1. Recomenda ferramentas existentes que atendam à necessidade\n2. Adapta ferramentas existentes para melhor atender aos requisitos\n3. Cria novas ferramentas personalizadas quando necessário\n4. Fornece documentação e exemplos de uso para as ferramentas"
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

class IntelligentToolsInput(BaseModel):
    """Schema de entrada para a tool de Avaliação e Criação Inteligente de Ferramentas."""
    necessidade: str = Field(..., description=get_description("IntelligentToolsInput.necessidade"))
    contexto: str = Field(..., description=get_description("IntelligentToolsInput.contexto"))
    funcionalidades_requeridas: str = Field(..., description=get_description("IntelligentToolsInput.funcionalidades_requeridas"))
    parametros_esperados: str = Field(..., description=get_description("IntelligentToolsInput.parametros_esperados"))
    tipo_resultado_esperado: str = Field(..., description=get_description("IntelligentToolsInput.tipo_resultado_esperado"))
    urgencia: str = Field(default="média", description=get_description("IntelligentToolsInput.urgencia"))

class IntelligentToolsTool(BaseTool):
    """
    Tool para avaliação inteligente e criação de ferramentas personalizadas.
    
    Esta tool utiliza uma equipe especializada para analisar necessidades de ferramentas,
    verificar se ferramentas existentes podem atender à demanda e, quando necessário, projetar
    e implementar novas ferramentas ou adaptações para necessidades específicas.
    """
    
    name: str = Field(default="IntelligentToolsTool")
    description: str = Field(default=get_description("IntelligentToolsTool.description"))
    args_schema: Type[BaseModel] = IntelligentToolsInput

    def _run(self, 
             necessidade: str, 
             contexto: str, 
             funcionalidades_requeridas: str,
             parametros_esperados: str,
             tipo_resultado_esperado: str,
             urgencia: str = "média") -> Dict[str, Any]:
        """Executa a tool de avaliação e criação inteligente de ferramentas."""
        try:
            logger.info("Iniciando processo de avaliação e criação de ferramentas")
            
            # Preparar os inputs para a equipe
            inputs = {
                "necessidade": necessidade,
                "contexto": contexto,
                "funcionalidades_requeridas": funcionalidades_requeridas,
                "parametros_esperados": parametros_esperados,
                "tipo_resultado_esperado": tipo_resultado_esperado,
                "urgencia": urgencia
            }
            
            # Criar e executar a equipe especializada
            logger.info("Criando e executando a equipe de Ferramentas Inteligentes")
            crew = ToolCreationCrew()
            resultado = crew.crew().kickoff(inputs=inputs)
            
            logger.info(f"Processo concluído com decisão: {resultado}")
            return resultado
            
        except Exception as e:
            error_msg = f"Erro ao executar o processo de avaliação e criação de ferramentas: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "erro",
                "mensagem": error_msg,
                "decisao": "falha",
                "ferramenta": {},
                "justificativa": f"Falha na execução: {str(e)}"
            }

if __name__ == '__main__':
    # Exemplo de uso da tool
    tool = IntelligentToolsTool()
    resultado = tool.run(
        necessidade="Preciso de uma ferramenta que gere documentação completa em markdown para uma codebase Python",
        contexto="Estamos desenvolvendo um sistema PDCA baseado em CrewAI com múltiplos agentes e equipes. Precisamos de documentação técnica detalhada para facilitar a manutenção e onboarding de novos desenvolvedores. A documentação deve abranger toda a arquitetura, fluxos, modelos de dados e integrações.",
        funcionalidades_requeridas="análise automática de estrutura de código, extração de docstrings, geração de diagramas de classes e fluxos, documentação de APIs, indexação e busca",
        parametros_esperados="diretório_raiz, padrões_exclusão, nível_detalhamento, formato_saída, incluir_métricas",
        tipo_resultado_esperado="Arquivos markdown estruturados com um índice principal, incluindo diagramas de classes/fluxos e documentação de API com links de navegação entre os arquivos",
        urgencia="média"
    )
    
    print("\nResultado da avaliação e criação de ferramenta:")
    print(f"Decisão: {resultado['decisao']}")
    print(f"Justificativa: {resultado['justificativa']}")
    print("\nDetalhes da ferramenta:")
    for chave, valor in resultado['ferramenta'].items():
        print(f"  {chave}: {valor}")
