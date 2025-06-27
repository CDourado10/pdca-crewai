from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import logging
import os
import sys

# Adicionar diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

from crews.tool_creation_crew.tool_creation_crew import ToolCreationCrew

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "ToolCreationInput.necessidade": "Descrição clara da necessidade ou problema que a ferramenta deve resolver.",
    
    "ToolCreationInput.contexto": "Contexto de aplicação onde a ferramenta será utilizada, incluindo detalhes sobre o sistema, usuários ou fluxos de trabalho.",
    
    "ToolCreationInput.funcionalidades_requeridas": "Lista de funcionalidades técnicas específicas que a ferramenta deve implementar, separadas por vírgula.",
    
    "ToolCreationInput.parametros_esperados": "Lista de parâmetros que a ferramenta deve aceitar, incluindo nomes e propósitos.",
    
    "ToolCreationInput.tipo_resultado_esperado": "Descrição do formato e conteúdo esperado no resultado da ferramenta.",
    
    "ToolCreationInput.urgencia": "Nível de urgência para a criação da ferramenta: 'baixa', 'média', 'alta' ou 'crítica'.",
    
    "ToolCreationCrewTool.description": """Cria novas ferramentas personalizadas para o sistema CrewAI através de uma equipe especializada.
Utiliza um processo completo de engenharia de software que inclui:
1. Design arquitetural da ferramenta
2. Implementação completa do código
3. Documentação detalhada para utilização
4. Preparação do pacote final de entrega
Retorna a ferramenta pronta para uso com todos os recursos necessários."""
}


# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

class ToolCreationInput(BaseModel):
    """Esquema de entrada para a ferramenta ToolCreationCrewTool."""
    
    necessidade: str = Field(
        ..., 
        description=get_description("ToolCreationInput.necessidade")
    )
    
    contexto: str = Field(
        ..., 
        description=get_description("ToolCreationInput.contexto")
    )
    
    funcionalidades_requeridas: str = Field(
        ..., 
        description=get_description("ToolCreationInput.funcionalidades_requeridas")
    )
    
    parametros_esperados: str = Field(
        ..., 
        description=get_description("ToolCreationInput.parametros_esperados")
    )
    
    tipo_resultado_esperado: str = Field(
        ..., 
        description=get_description("ToolCreationInput.tipo_resultado_esperado")
    )
    
    urgencia: str = Field(
        default="média", 
        description=get_description("ToolCreationInput.urgencia")
    )

class ToolCreationCrewTool(BaseTool):
    """Ferramenta para criação dinâmica de novas ferramentas através de uma equipe especializada."""
    
    name: str = "ToolCreationCrewTool"
    description: str = get_description("ToolCreationCrewTool.description")
    args_schema: Type[BaseModel] = ToolCreationInput

    def _run(
        self,
        necessidade: str,
        contexto: str,
        funcionalidades_requeridas: str,
        parametros_esperados: str,
        tipo_resultado_esperado: str,
        urgencia: str = "média"
    ) -> str:
        """Executa o processo de criação de uma nova ferramenta.
        
        Args:
            necessidade: Descrição da necessidade a ser atendida
            contexto: Contexto de aplicação da ferramenta
            funcionalidades_requeridas: Funcionalidades técnicas necessárias
            parametros_esperados: Parâmetros que a ferramenta deve aceitar
            tipo_resultado_esperado: Formato do resultado esperado
            urgencia: Nível de urgência da criação
            
        Returns:
            Detalhes sobre a ferramenta criada ou mensagem de erro
        """
        try:
            logger.info(f"Iniciando criação de ferramenta para: {necessidade}")
            
            # Prepara os inputs para a equipe
            inputs = {
                "necessidade": necessidade,
                "contexto": contexto,
                "funcionalidades_requeridas": funcionalidades_requeridas,
                "parametros_esperados": parametros_esperados,
                "tipo_resultado_esperado": tipo_resultado_esperado,
                "urgencia": urgencia
            }
            
            # Criar e executar a equipe de criação de ferramentas
            crew = ToolCreationCrew()
            resultado = crew.crew().kickoff(inputs=inputs)
            
            logger.info(f"Ferramenta criada com sucesso: {resultado}")
            
            # Formatando a resposta para ser mais legível
            resposta = resultado
            
            return resposta
            
        except Exception as e:
            error_msg = f"Erro ao criar ferramenta: {str(e)}"
            logger.error(error_msg)
            return f"""
## ❌ Erro na Criação da Ferramenta

**Detalhes do erro:** {error_msg}

**Verifique:**
1. Se todos os parâmetros foram preenchidos corretamente
2. Se o sistema possui todas as dependências necessárias
3. Se os diretórios de resultado existem e têm permissão de escrita
"""

if __name__ == '__main__':
    # Exemplo de uso da ferramenta
    tool = ToolCreationCrewTool()
    
    # Exemplo de parâmetros para criar uma ferramenta de análise de logs
    resultado = tool.run(
        necessidade="Ferramenta para analisar arquivos de log e extrair padrões, erros e estatísticas",
        contexto="Sistema distribuído que gera diversos arquivos de log em formatos diferentes",
        funcionalidades_requeridas="parse de diferentes formatos de log, identificação de erros, agregação por períodos",
        parametros_esperados="caminho_logs, formato, nivel_filtro, periodo_analise",
        tipo_resultado_esperado="Relatório detalhado com seções para erros críticos, avisos e uso de recursos",
        urgencia="alta"
    )
    
    print(resultado)
