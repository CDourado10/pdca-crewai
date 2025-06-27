#!/usr/bin/env python
"""
Ferramenta para criação dinâmica de configurações de agentes.

Esta ferramenta permite criar configurações YAML para agentes, especificando
seus papéis, objetivos e histórias de fundo.
"""

from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from pathlib import Path
from crewai.tools import BaseTool

# Dicionário de descrições para substituir a função get_description
DESCRIPTIONS = {
    "AgentConfig.role": "Papel do agente na equipe, descrevendo sua função principal",
    "AgentConfig.goal": "Objetivo principal que o agente deve alcançar",
    "AgentConfig.backstory": "História de fundo do agente que explica sua experiência e conhecimento",
    "AgentYAMLConfigInput.crew_name": "Nome da equipe (crew) para a qual os agentes serão configurados",
    "AgentYAMLConfigInput.agents_config": "Configurações dos agentes a serem incluídos no arquivo YAML",
    "AgentYAMLConfigInput.multiline_style": "Estilo de formatação para strings multilinhas no YAML (folded, block, literal)",
    "AgentYAMLConfigWriter.name": "Criador de Configuração YAML para Agentes",
    "AgentYAMLConfigWriter.description": "Ferramenta para escrever configurações de agentes no arquivo agents.yaml de uma crew específica"
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário local."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

# Função simplificada para registrar uso da ferramenta (apenas para logging)
def register_tool_usage(tool_name: str, params: Dict[str, Any], metadata: Dict[str, Any] = None):
    """Registra o uso da ferramenta (versão simplificada que apenas imprime informações)."""
    print(f"Ferramenta {tool_name} utilizada com parâmetros: {params}")
    if metadata:
        print(f"Metadados: {metadata}")


class AgentConfig(BaseModel):
    """Configuração para um agente no arquivo agents.yaml."""
    role: str = Field(
        ...,
        description=get_description("AgentConfig.role")
    )
    goal: str = Field(
        ...,
        description=get_description("AgentConfig.goal")
    )
    backstory: str = Field(
        ...,
        description=get_description("AgentConfig.backstory")
    )


class AgentYAMLConfigInput(BaseModel):
    """Parâmetros de entrada para a ferramenta AgentYAMLConfigWriter."""
    crew_name: str = Field(
        ...,
        description=get_description("AgentYAMLConfigInput.crew_name")
    )
    agents_config: Dict[str, AgentConfig] = Field(
        ...,
        description=get_description("AgentYAMLConfigInput.agents_config")
    )
    multiline_style: str = Field(
        default="folded",
        description=get_description("AgentYAMLConfigInput.multiline_style")
    )


class AgentYAMLConfigWriter(BaseTool):
    """Ferramenta para escrever configurações de agentes no arquivo agents.yaml."""

    model_config = {
        'arbitrary_types_allowed': True,
        'validate_assignment': True
    }

    name: str = Field(default=get_description("AgentYAMLConfigWriter.name"))
    description: str = Field(default=get_description("AgentYAMLConfigWriter.description"))
    args_schema: Type[BaseModel] = AgentYAMLConfigInput

    def _format_multiline_string(self, text: str, style: str) -> str:
        """Formata strings multilinhas de acordo com o estilo especificado."""
        text = text.strip()
        
        if style == "block":
            # Apenas marca o texto para processamento posterior
            return f"*>*\n{text}"
        elif style == "folded":
            # Apenas marca o texto para processamento posterior
            return f"*>*\n{text}"
        elif style == "literal":
            # Apenas marca o texto para processamento posterior
            return f"*>*\n{text}"
        else:
            return text

    def _prepare_agent_config(self, config: Dict[str, AgentConfig], style: str) -> Dict:
        """Prepara o dicionário de configuração para agentes com formatação adequada."""
        result = {}
        for key, agent in config.items():
            result[key] = {
                "role": self._format_multiline_string(agent.role, style),
                "goal": self._format_multiline_string(agent.goal, style),
                "backstory": self._format_multiline_string(agent.backstory, style)
            }
        return result

    def _custom_yaml_dump(self, data: Dict) -> str:
        """Realiza dump personalizado de YAML para preservar formatação de strings multilinhas."""
        result = []
        
        for agent_key, agent_data in data.items():
            result.append(f"{agent_key}:")
            
            role_text = agent_data['role']
            if role_text.startswith("*>*"):
                role_lines = role_text.replace("*>*", "").strip().split("\n")
                result.append("  role: |")
                for line in role_lines:
                    result.append(f"    {line}")
            else:
                result.append(f"  role: {role_text}")
            
            goal_text = agent_data['goal']
            if goal_text.startswith("*>*"):
                goal_lines = goal_text.replace("*>*", "").strip().split("\n")
                result.append("  goal: |")
                for line in goal_lines:
                    result.append(f"    {line}")
            else:
                result.append(f"  goal: {goal_text}")
            
            backstory_text = agent_data['backstory']
            if backstory_text.startswith("*>*"):
                backstory_lines = backstory_text.replace("*>*", "").strip().split("\n")
                result.append("  backstory: |")
                for line in backstory_lines:
                    result.append(f"    {line}")
            else:
                result.append(f"  backstory: {backstory_text}")
            
            result.append("")
        
        return "\n".join(result)

    def _find_crew_directory(self, crew_name: str) -> Optional[Path]:
        """Localiza o diretório da crew com base no nome."""
        crews_dir = Path("crews")
        
        if not crews_dir.exists():
            return None
        
        normalized_name = crew_name.lower().replace(" ", "_")
        
        direct_match = crews_dir / normalized_name
        if direct_match.exists() and direct_match.is_dir():
            return direct_match
        
        for subdir in crews_dir.iterdir():
            if subdir.is_dir():
                if subdir.name.lower().replace("_", "") == normalized_name.replace("_", ""):
                    return subdir
        
        return None

    def _run(self, crew_name: str, agents_config: Dict[str, AgentConfig], multiline_style: str = "block"):
        """Escreve as configurações no arquivo agents.yaml do crew especificado."""
        register_tool_usage(
            tool_name="AgentYAMLConfigWriter",
            params={
                "crew_name": crew_name,
                "agents_config": str(list(agents_config.keys())),
                "multiline_style": multiline_style
            },
            metadata={
                "agent_count": len(agents_config),
                "config_type": "agents"
            }
        )
        
        crew_dir = self._find_crew_directory(crew_name)
        if crew_dir is None:
            return f"Erro: Não foi possível encontrar o crew '{crew_name}'."
        
        config_dir = crew_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        agents_yaml_path = config_dir / "agents.yaml"
        
        formatted_config = self._prepare_agent_config(agents_config, multiline_style)
        
        with open(agents_yaml_path, 'w', encoding='utf-8') as f:
            f.write(self._custom_yaml_dump(formatted_config))
        
        return f"Arquivo agents.yaml criado com sucesso em {agents_yaml_path}"


if __name__ == "__main__":
    # Verifica se o ExemploCrew foi criado pelo dynamic_crew_creator.py
    exemplo_crew_dir = Path("crews/exemplocrew")
    if not exemplo_crew_dir.exists():
        print("AVISO: Execute primeiro o dynamic_crew_creator.py para criar o ExemploCrew")
        print("Criando diretório de exemplo para demonstração...")
        exemplo_crew_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"ExemploCrew encontrado em: {exemplo_crew_dir}")
    
    # Cria o diretório de configuração se não existir
    config_dir = exemplo_crew_dir / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Exemplo de uso
    writer = AgentYAMLConfigWriter()
    result = writer.run(
        crew_name="exemplocrew",
        agents_config={
            "agente_processador": AgentConfig(
                role="Processador de Texto",
                goal="Processar textos utilizando a FerramentaExemplo para gerar resultados úteis",
                backstory="Especialista em processamento de texto com vasta experiência em manipulação e transformação de dados textuais."
            ),
            "agente_analisador": AgentConfig(
                role="Analisador de Resultados",
                goal="Analisar os resultados do processamento de texto e extrair insights relevantes",
                backstory="Analista com experiência em interpretação de dados e identificação de padrões em textos processados."
            )
        }
    )
    
    print(result)
