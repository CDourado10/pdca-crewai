#!/usr/bin/env python
"""
Ferramenta para criação dinâmica de configurações de tarefas.

Esta ferramenta permite criar configurações YAML para tarefas, especificando
suas descrições, saídas esperadas e campos adicionais.
"""

from typing import Dict, Optional, Type
from pydantic import BaseModel, Field
from pathlib import Path
from crewai.tools import BaseTool

# Dicionário de descrições para substituir a função get_description
DESCRIPTIONS = {
    "TaskConfig.description": "Descrição detalhada da tarefa a ser executada",
    "TaskConfig.expected_output": "Resultado esperado após a conclusão da tarefa",
    "TaskYAMLConfigInput.crew_name": "Nome da equipe (crew) para a qual as tarefas serão configuradas",
    "TaskYAMLConfigInput.tasks_config": "Configurações das tarefas a serem incluídas no arquivo YAML",
    "TaskYAMLConfigInput.multiline_style": "Estilo de formatação para strings multilinhas no YAML (folded, block, literal)",
    "TaskYAMLConfigWriter.name": "Criador de Configuração YAML para Tarefas",
    "TaskYAMLConfigWriter.description": "Ferramenta para escrever configurações de tarefas no arquivo tasks.yaml de uma crew específica"
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário local."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

# Função simplificada para registrar uso da ferramenta (apenas para logging)
def register_tool_usage(tool_name: str, params: Dict, metadata: Dict = None):
    """Registra o uso da ferramenta (versão simplificada que apenas imprime informações)."""
    print(f"Ferramenta {tool_name} utilizada com parâmetros: {params}")
    if metadata:
        print(f"Metadados: {metadata}")


class TaskConfig(BaseModel):
    """Configuração de uma tarefa para o arquivo YAML."""
    description: str = Field(
        ...,
        description=get_description("TaskConfig.description")
    )
    expected_output: str = Field(
        ...,
        description=get_description("TaskConfig.expected_output")
    )
    # Removemos o campo additional_fields que não deve ser usado


class TaskYAMLConfigInput(BaseModel):
    """Parâmetros de entrada para a ferramenta TaskYAMLConfigWriter."""
    crew_name: str = Field(
        ...,
        description=get_description("TaskYAMLConfigInput.crew_name")
    )
    tasks_config: Dict[str, TaskConfig] = Field(
        ...,
        description=get_description("TaskYAMLConfigInput.tasks_config")
    )
    multiline_style: str = Field(
        default="block",
        description=get_description("TaskYAMLConfigInput.multiline_style")
    )


class TaskYAMLConfigWriter(BaseTool):
    """Ferramenta para escrever configurações de tarefas no arquivo tasks.yaml."""

    model_config = {
        'arbitrary_types_allowed': True,
        'validate_assignment': True
    }

    name: str = Field(default=get_description("TaskYAMLConfigWriter.name"))
    description: str = Field(default=get_description("TaskYAMLConfigWriter.description"))
    args_schema: Type[BaseModel] = TaskYAMLConfigInput

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

    def _prepare_task_config(self, config: Dict[str, TaskConfig], style: str) -> Dict:
        """Prepara o dicionário de configuração para tarefas com formatação adequada."""
        result = {}
        for key, task in config.items():
            task_config = {
                "description": self._format_multiline_string(task.description, style),
                "expected_output": self._format_multiline_string(task.expected_output, style)
            }
            
            # Removemos o processamento de campos adicionais
            
            result[key] = task_config
        return result

    def _custom_yaml_dump(self, data: Dict) -> str:
        """Realiza dump personalizado de YAML para preservar formatação de strings multilinhas."""
        result = []
        
        for task_key, task_data in data.items():
            result.append(f"{task_key}:")
            
            desc_text = task_data['description']
            if desc_text.startswith("*>*"):
                desc_lines = desc_text.replace("*>*", "").strip().split("\n")
                result.append("  description: |")
                for line in desc_lines:
                    result.append(f"    {line}")
            else:
                result.append(f"  description: {desc_text}")
            
            output_text = task_data['expected_output']
            if output_text.startswith("*>*"):
                output_lines = output_text.replace("*>*", "").strip().split("\n")
                result.append("  expected_output: |")
                for line in output_lines:
                    result.append(f"    {line}")
            else:
                result.append(f"  expected_output: {output_text}")
            
            # Removemos o processamento de campos adicionais
            
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

    def _run(self, crew_name: str, tasks_config: Dict[str, TaskConfig], multiline_style: str = "block"):
        """Escreve as configurações no arquivo tasks.yaml do crew especificado."""
        register_tool_usage(
            tool_name="TaskYAMLConfigWriter",
            params={
                "crew_name": crew_name,
                "tasks_config": str(list(tasks_config.keys())),
                "multiline_style": multiline_style
            },
            metadata={
                "task_count": len(tasks_config),
                "config_type": "tasks"
            }
        )
        
        crew_dir = self._find_crew_directory(crew_name)
        if crew_dir is None:
            return f"Erro: Não foi possível encontrar o crew '{crew_name}'."
        
        config_dir = crew_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        tasks_yaml_path = config_dir / "tasks.yaml"
        
        formatted_config = self._prepare_task_config(tasks_config, multiline_style)
        
        with open(tasks_yaml_path, 'w', encoding='utf-8') as f:
            f.write(self._custom_yaml_dump(formatted_config))
        
        return f"Arquivo tasks.yaml criado com sucesso em {tasks_yaml_path}"


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
    
    writer = TaskYAMLConfigWriter()
    result = writer.run(
        crew_name="exemplocrew",
        tasks_config={
            "processar_texto_task": TaskConfig(
                description="Processar um texto de entrada utilizando a FerramentaExemplo para gerar resultados úteis para análise posterior.",
                expected_output="Texto processado com as transformações aplicadas pela FerramentaExemplo."
            ),
            "analisar_resultado_task": TaskConfig(
                description="Analisar os resultados do processamento de texto e extrair insights relevantes sobre o conteúdo processado.",
                expected_output="Relatório de análise com insights sobre o texto processado e recomendações para melhorias."
                # Removemos os campos adicionais
            )
        }
    )
    
    print(result)
