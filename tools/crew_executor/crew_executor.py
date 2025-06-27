#!/usr/bin/env python
"""
Ferramenta genérica para execução de crews.

Esta ferramenta permite executar qualquer crew, fornecendo os inputs necessários
e retornando os resultados da execução.
"""

import os
import sys
import json
import importlib
import logging
from typing import Dict, Any, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("crew_executor.log")
    ]
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
sys.path.append(project_root)

class CrewExecutorInput(BaseModel):
    """
    Modelo de entrada para a ferramenta de execução de crews.
    """
    crew_path: str = Field(
        description="Caminho para o módulo da crew (ex: 'crews.pdca.planejar.planejar_crew')"
    )
    crew_class: str = Field(
        description="Nome da classe da crew (ex: 'PlanejarCrew')"
    )
    inputs: Dict[str, Any] = Field(
        description="Dicionário com os inputs necessários para a execução da crew"
    )

class CrewExecutor(BaseTool):
    """
    Ferramenta genérica para execução de crews.
    
    Esta ferramenta permite executar qualquer crew, fornecendo os inputs necessários
    e retornando os resultados da execução. É útil para testar e integrar crews
    criadas dinamicamente.
    """
    name: str = "Executor de Crews"
    description: str = (
        "Executa uma crew específica, fornecendo os inputs necessários e retornando "
        "os resultados da execução. Útil para testar e integrar crews criadas dinamicamente."
    )
    args_schema: Type[BaseModel] = CrewExecutorInput
    
    def _run(
        self, 
        crew_path: str,
        crew_class: str,
        inputs: Dict[str, Any]
    ) -> Any:
        """
        Executa uma crew específica com os inputs fornecidos.
        
        Args:
            crew_path: Caminho para o módulo da crew
            crew_class: Nome da classe da crew
            inputs: Dicionário com os inputs necessários para a execução
            
        Returns:
            Resultado da execução da crew
        """
        try:
            # Converter o caminho do módulo em caminho de arquivo
            logger.info(f"Preparando para executar crew: {crew_path}.{crew_class}")
            
            # Salvar o sys.path atual e adicionar o diretório raiz do projeto
            # para garantir que todas as importações relativas funcionem
            original_path = list(sys.path)
            sys.path.insert(0, project_root)
            
            try:
                # Importar o módulo da crew
                logger.info(f"Importando módulo da crew: {crew_path}")
                crew_module = importlib.import_module(crew_path)
                
                # Obter a classe da crew
                logger.info(f"Obtendo classe da crew: {crew_class}")
                crew_cls = getattr(crew_module, crew_class)
                
                # Instanciar a crew
                logger.info(f"Instanciando a crew: {crew_class}")
                crew_instance = crew_cls()
                
                # Obter o objeto Crew
                logger.info("Obtendo objeto Crew")
                crew_obj = crew_instance.crew()
                
                # Executar a crew
                logger.info(f"Executando a crew com inputs: {json.dumps(inputs, default=str)}")
                result = crew_obj.kickoff(inputs=inputs)
                
                return result
            finally:
                # Restaurar o sys.path original
                sys.path = original_path
            
            # O resultado já foi retornado no bloco try
        
        except Exception as e:
            error_msg = f"Erro durante a execução da crew: {str(e)}"
            logger.error(error_msg)
            return f"\u274c Erro ao executar a crew {crew_class}: {str(e)}"

if __name__ == "__main__":
    # Exemplo de inputs para a equipe ToolCreationCrew (que sabemos que funciona)
    crew_inputs = {
        "necessidade": "Precisamos de uma ferramenta para analisar codigo Python",
        "contexto": "Estamos trabalhando em um sistema de autofix de bugs",
        "funcionalidades_requeridas": "Analisar AST, identificar bugs comuns, sugerir correcoes",
        "parametros_esperados": "caminho_arquivo, nivel_analise, formato_saida",
        "tipo_resultado_esperado": "Lista de problemas encontrados com sugestoes de correcao",
        "urgencia": "alta"
    }
    
    # Exemplo de uso da ferramenta com uma crew que não requer imports complexos
    executor = CrewExecutor()
    resultado = executor.run(
        crew_path="crews.tool_creation_crew.tool_creation_crew",
        crew_class="ToolCreationCrew",
        inputs=crew_inputs
    )
    
    print("\nResultado da execução da ToolCreationCrew:")
    print(resultado)
    
