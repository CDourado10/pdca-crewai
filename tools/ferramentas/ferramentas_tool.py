#!/usr/bin/env python
"""
Ferramenta para criação dinâmica de recursos PDCA.

Esta ferramenta utiliza a FerramentasCrew para criar dinamicamente agentes, tarefas,
equipes e ferramentas específicas para cada fase do ciclo PDCA.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, Type, List
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ferramentas_tool.log")
    ]
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

# Importar FerramentasCrew
from crews.pdca.ferramentas.ferramentas_crew import FerramentasCrew  # noqa: E402

# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "FerramentasInput.fase": "Nome da fase do ciclo PDCA (planejar, fazer, verificar, agir)",
    "FerramentasInput.problema": "Descrição detalhada do problema a ser resolvido",
    "FerramentasInput.contexto": "Contexto do problema e da organização onde será aplicado",
    "FerramentasInput.tipo_ferramentas": "Tipos específicos de ferramentas necessárias (ex: análise de causa raiz, estabelecimento de metas)",
    "FerramentasInput.complexidade": "Nível de complexidade desejado para as ferramentas (simples, médio, avançado)",
    "FerramentasInput.prazo": "Prazo disponível para implementação (curto, médio, longo)",
    "FerramentasInput.recursos_disponiveis": "Lista de recursos disponíveis para implementação",
    "FerramentasInput.restricoes": "Lista de restrições para a criação e implementação",
    "FerramentasTool.description": "Cria dinamicamente agentes, tarefas, equipes e ferramentas específicas para cada fase do ciclo PDCA, adaptando-se ao contexto do problema e às necessidades específicas de cada situação."
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

class FerramentasInput(BaseModel):
    """
    Modelo de entrada para a ferramenta de criação dinâmica de recursos PDCA.
    """
    fase: str = Field(
        description=get_description("FerramentasInput.fase")
    )
    problema: str = Field(
        description=get_description("FerramentasInput.problema")
    )
    contexto: str = Field(
        description=get_description("FerramentasInput.contexto")
    )
    tipo_ferramentas: Optional[List[str]] = Field(
        default=None,
        description=get_description("FerramentasInput.tipo_ferramentas")
    )
    complexidade: Optional[str] = Field(
        default=None,
        description=get_description("FerramentasInput.complexidade")
    )
    prazo: Optional[str] = Field(
        default=None,
        description=get_description("FerramentasInput.prazo")
    )
    recursos_disponiveis: Optional[List[str]] = Field(
        default=None,
        description=get_description("FerramentasInput.recursos_disponiveis")
    )
    restricoes: Optional[List[str]] = Field(
        default=None,
        description=get_description("FerramentasInput.restricoes")
    )

class FerramentasTool(BaseTool):
    """
    Ferramenta para criação dinâmica de recursos PDCA.
    
    Esta ferramenta cria dinamicamente agentes, tarefas, equipes e ferramentas
    específicas para cada fase do ciclo PDCA, adaptando-se ao contexto do problema
    e às necessidades específicas de cada situação.
    """
    name: str = "Ferramenta de Criação Dinâmica de Recursos PDCA"
    description: str = get_description("FerramentasTool.description")
    args_schema: Type[BaseModel] = FerramentasInput
    
    # Não estamos usando o modelo Pydantic para ferramentas_crew, então não precisamos declará-lo como campo
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa a ferramenta de criação dinâmica de recursos.
        
        Args:
            config_path: Caminho opcional para arquivo de configuração personalizado
        """
        super().__init__()
        # Inicializar a equipe como atributo da classe
        self._ferramentas_crew = FerramentasCrew()
        logger.info("FerramentasTool inicializada com sucesso")
    
    def _run(
        self, 
        fase: str,
        problema: str,
        contexto: str,
        tipo_ferramentas: Optional[List[str]] = None,
        complexidade: Optional[str] = None,
        prazo: Optional[str] = None,
        recursos_disponiveis: Optional[List[str]] = None,
        restricoes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executa a ferramenta de criação dinâmica de recursos com os dados fornecidos.
        
        Args:
            fase: Nome da fase do ciclo PDCA (planejar, fazer, verificar, agir)
            problema: Descrição detalhada do problema a ser resolvido
            contexto: Contexto do problema e da organização
            tipo_ferramentas: Tipos específicos de ferramentas necessárias
            complexidade: Nível de complexidade desejado para as ferramentas
            prazo: Prazo disponível para implementação
            recursos_disponiveis: Recursos disponíveis para implementação
            restricoes: Restrições para a criação e implementação
            
        Returns:
            Dicionário contendo os recursos criados (agentes, tarefas, equipe, ferramentas)
        """
        # Preparar requisitos específicos
        requisitos = {}
        if tipo_ferramentas:
            requisitos["tipo_ferramentas"] = tipo_ferramentas
        if complexidade:
            requisitos["complexidade"] = complexidade
        if prazo:
            requisitos["prazo"] = prazo
        if recursos_disponiveis:
            requisitos["recursos_disponiveis"] = recursos_disponiveis
        if restricoes:
            requisitos["restricoes"] = restricoes
        
        try:
            # Executar a equipe de criação de ferramentas
            logger.info(f"Iniciando criação de recursos para a fase {fase}")
            
            # Preparar os dados de entrada para a equipe
            input_data = {
                "problema": problema,
                "contexto": contexto,
                "fase_pdca": fase,
                "requisitos": requisitos
            }
            
            # Executar a equipe de criação de ferramentas
            resultado = self._ferramentas_crew.crew().kickoff(inputs=input_data)
            
            # Processar e retornar os resultados
            return self._processar_resultado(resultado.raw_output)
        
        except Exception as e:
            logger.error(f"Erro durante a criação de recursos: {str(e)}")
            return {
                "erro": str(e),
                "status": "falha",
                "mensagem": "Ocorreu um erro durante a criação dos recursos"
            }
    
    def _processar_resultado(self, resultado: Any) -> Dict[str, Any]:
        """
        Processa o resultado da execução da equipe.
        
        Args:
            resultado: Resultado bruto da execução da equipe
            
        Returns:
            Dicionário processado com os recursos criados
        """
        # Se já for um dicionário, retornar diretamente
        if isinstance(resultado, dict):
            return resultado
        
        # Tentar processar como JSON
        try:
            if isinstance(resultado, str):
                return json.loads(resultado)
        except json.JSONDecodeError:
            pass
        
        # Processar arquivos de saída
        return {
            "agentes": self._ler_arquivo_saida("agentes_criados.yaml"),
            "tarefas": self._ler_arquivo_saida("tarefas_criadas.yaml"),
            "equipe": self._ler_arquivo_saida("equipe_criada.yaml"),
            "ferramentas": self._ler_arquivo_saida("ferramentas_criadas.py"),
            "recursos_integrados": self._ler_arquivo_saida("recursos_integrados.json")
        }
    
    def _ler_arquivo_saida(self, nome_arquivo: str) -> str:
        """
        Lê o conteúdo de um arquivo de saída, se existir.
        
        Args:
            nome_arquivo: Nome do arquivo a ser lido
            
        Returns:
            Conteúdo do arquivo ou mensagem de erro
        """
        try:
            with open(nome_arquivo, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            return f"Arquivo {nome_arquivo} não encontrado"
        except Exception as e:
            return f"Erro ao ler {nome_arquivo}: {str(e)}"

if __name__ == "__main__":
    # Exemplo de uso da ferramenta
    tool = FerramentasTool()
    resultado = tool.run(
        fase="planejar",
        problema="Baixa produtividade na linha de montagem",
        contexto="Empresa de manufatura com 50 funcionários, operando há 10 anos",
        tipo_ferramentas=["análise de causa raiz", "estabelecimento de metas"],
        complexidade="média",
        prazo="curto"
    )
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
