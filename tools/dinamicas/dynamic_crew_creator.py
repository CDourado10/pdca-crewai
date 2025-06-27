#!/usr/bin/env python
"""
Ferramenta para criação dinâmica de crews.

Esta ferramenta permite criar crews dinamicamente, especificando
seus agentes, tarefas e configurações.
"""

import ast
import astor
from typing import List, Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from pathlib import Path

# Dicionário de descrições para substituir a função get_description
DESCRIPTIONS = {
    "AgentReference.name": "Nome do agente a ser referenciado",
    "AgentReference.config_key": "Chave de configuração do agente no arquivo agents.yaml",
    "AgentReference.tools": "Lista de ferramentas a serem utilizadas pelo agente",
    "AgentReference.llm": "Modelo de linguagem a ser utilizado pelo agente",
    "AgentReference.verbose": "Se o agente deve exibir logs detalhados",
    "AgentReference.allow_code_execution": "Se o agente tem permissão para executar código",
    "TaskDefinition.name": "Nome da tarefa a ser executada",
    "TaskDefinition.config_key": "Chave de configuração da tarefa no arquivo tasks.yaml",
    "TaskDefinition.agent_name": "Nome do agente responsável pela execução da tarefa",
    "TaskDefinition.context_tasks": "Lista de tarefas cujos resultados serão utilizados como contexto",
    "TaskDefinition.llm": "Modelo de linguagem a ser utilizado para a tarefa",
    "CrewDefinition.name": "Nome da equipe (crew) a ser criada",
    "CrewDefinition.description": "Descrição da equipe e seu propósito",
    "CrewDefinition.agents": "Lista de agentes que compõem a equipe",
    "CrewDefinition.tasks": "Lista de tarefas a serem executadas pela equipe",
    "CrewDefinition.process_type": "Tipo de processo a ser utilizado (sequential, hierarchical, etc.)",
    "CrewDefinition.verbose": "Se a equipe deve exibir logs detalhados",
    "CrewDefinition.planning": "Se a equipe deve realizar planejamento automático",
    "CrewDefinition.output_log_file": "Arquivo para registro de logs da equipe",
    "CrewDefinition.custom_imports": "Importações personalizadas a serem incluídas no arquivo da equipe",
    "DynamicCrewCreator.description": "Ferramenta para criar dinamicamente equipes (crews) no CrewAI"
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


class AgentReference(BaseModel):
    """Referência a um agente para uso em um Crew."""
    model_config = {
        'arbitrary_types_allowed': True,
        'validate_assignment': True
    }

    name: str = Field(
        ...,
        description=get_description("AgentReference.name")
    )
    config_key: str = Field(
        ...,
        description=get_description("AgentReference.config_key")
    )
    tools: List[str] = Field(
        default=[],
        description=get_description("AgentReference.tools")
    )
    llm: str = Field(
        default="azure/gpt-4o-mini",
        description=get_description("AgentReference.llm")
    )
    verbose: bool = Field(
        default=True,
        description=get_description("AgentReference.verbose")
    )
    allow_code_execution: bool = Field(
        default=False,
        description=get_description("AgentReference.allow_code_execution")
    )

class TaskDefinition(BaseModel):
    """Definição de uma tarefa para ser executada por um agente no Crew."""
    model_config = {
        'arbitrary_types_allowed': True,
        'validate_assignment': True
    }

    name: str = Field(
        ...,
        description=get_description("TaskDefinition.name")
    )
    config_key: str = Field(
        ...,
        description=get_description("TaskDefinition.config_key")
    )
    agent_name: str = Field(
        ...,
        description=get_description("TaskDefinition.agent_name")
    )
    context_tasks: List[str] = Field(
        default=[],
        description=get_description("TaskDefinition.context_tasks")
    )
    llm: str = Field(
        default="azure/gpt-4o-mini",
        description=get_description("TaskDefinition.llm")
    )

class CrewDefinition(BaseModel):
    """Especificação para criar um novo Crew no CrewAI."""
    name: str = Field(
        ..., 
        description=get_description("CrewDefinition.name")
    )
    description: str = Field(
        ..., 
        description=get_description("CrewDefinition.description")
    )
    agents: List[AgentReference] = Field(
        ...,
        description=get_description("CrewDefinition.agents")
    )
    tasks: List[TaskDefinition] = Field(
        ...,
        description=get_description("CrewDefinition.tasks")
    )
    process_type: str = Field(
        default="sequential",
        description=get_description("CrewDefinition.process_type")
    )
    verbose: bool = Field(
        default=True,
        description=get_description("CrewDefinition.verbose")
    )
    planning: bool = Field(
        default=True,
        description=get_description("CrewDefinition.planning")
    )
    output_log_file: Optional[str] = Field(
        default=None,
        description=get_description("CrewDefinition.output_log_file")
    )
    custom_imports: List[str] = Field(
        default=[],
        description=get_description("CrewDefinition.custom_imports")
    )

class CrewASTBuilder:
    """Construtor de AST para Crews do CrewAI."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tree = ast.Module(body=[], type_ignores=[])
        
    def add_imports(self, imports: List[str]) -> None:
        """Adiciona imports ao início do arquivo."""
        # Imports padrão
        all_imports = [
            "from crewai import Agent, Task, Crew, Process",
            "from crewai.project import CrewBase, agent, task, crew",
            "from typing import Dict, List, Optional",
            "import os",
            "import yaml",
            "from dotenv import load_dotenv"
        ] + imports
        
        # Remove duplicatas mantendo a ordem
        unique_imports = []
        seen = set()
        for imp in all_imports:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)
        
        # Adiciona os imports ao AST
        for imp in unique_imports:
            self.tree.body.append(ast.parse(imp).body[0])
        
        # Adiciona chamada para load_dotenv
        self.tree.body.append(
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="load_dotenv", ctx=ast.Load()),
                    args=[],
                    keywords=[]
                )
            )
        )
    
    def create_crew_class(self, crew_def: CrewDefinition) -> None:
        """Cria a classe CrewBase para o Crew."""
        class_body = []
        
        # Adiciona docstring à classe
        class_body.append(
            ast.Expr(
                ast.Constant(
                    value=crew_def.description
                )
            )
        )
        
        # Cria os métodos para os agentes
        for agent_ref in crew_def.agents:
            agent_method = self._create_agent_method(agent_ref)
            class_body.append(agent_method)
        
        # Cria os métodos para as tarefas
        task_methods = {}
        for task_def in crew_def.tasks:
            task_method = self._create_task_method(task_def)
            class_body.append(task_method)
            task_methods[task_def.name] = task_def
        
        # Cria o método crew
        crew_method = self._create_crew_method(crew_def)
        class_body.append(crew_method)
        
        # Cria a classe com o decorador CrewBase
        class_def = ast.ClassDef(
            name=f"{self.name.replace(' ', '')}Crew",
            bases=[],
            keywords=[],
            body=class_body,
            decorator_list=[ast.Name(id="CrewBase", ctx=ast.Load())]
        )
        
        self.tree.body.append(class_def)
        
        # Adiciona um bloco if __name__ == "__main__" para testar o crew
        main_block = self._create_main_block(crew_def)
        self.tree.body.append(main_block)
    
    def _create_agent_method(self, agent_ref: AgentReference) -> ast.FunctionDef:
        """Cria um método decorado com @agent para um agente."""
        # Prepara as ferramentas, se houver
        tools_value = None
        if agent_ref.tools:
            tools_list = []
            for tool in agent_ref.tools:
                tools_list.append(
                    ast.Call(
                        func=ast.Name(id=tool, ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    )
                )
            
            tools_value = ast.List(
                elts=tools_list,
                ctx=ast.Load()
            )
        
        # Cria o corpo do método
        method_body = [
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id="Agent", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="config",
                            value=ast.Subscript(
                                value=ast.Attribute(
                                    value=ast.Name(id="self", ctx=ast.Load()),
                                    attr="agents_config",
                                    ctx=ast.Load()
                                ),
                                slice=ast.Constant(value=agent_ref.config_key),
                                ctx=ast.Load()
                            )
                        ),
                        ast.keyword(
                            arg="verbose",
                            value=ast.Constant(value=agent_ref.verbose)
                        ),
                        ast.keyword(
                            arg="llm",
                            value=ast.Constant(value=agent_ref.llm)
                        ),
                        ast.keyword(
                            arg="allow_code_execution",
                            value=ast.Constant(value=agent_ref.allow_code_execution)
                        )
                    ] + ([ast.keyword(arg="tools", value=tools_value)] if tools_value else [])
                )
            )
        ]
        
        # Cria o método com o decorador @agent
        agent_method = ast.FunctionDef(
            name=agent_ref.name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="self", annotation=None)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None
            ),
            body=method_body,
            decorator_list=[
                ast.Name(id="agent", ctx=ast.Load())
            ],
            returns=None
        )
        
        return agent_method
    
    def _create_task_method(self, task_def: TaskDefinition) -> ast.FunctionDef:
        """Cria um método decorado com @task para uma tarefa."""
        # Prepara as tarefas de contexto, se houver
        context_tasks_value = None
        if task_def.context_tasks:
            context_tasks_list = []
            for context_task in task_def.context_tasks:
                context_tasks_list.append(
                    ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="self", ctx=ast.Load()),
                            attr=context_task,
                            ctx=ast.Load()
                        ),
                        args=[],
                        keywords=[]
                    )
                )
            
            context_tasks_value = ast.List(
                elts=context_tasks_list,
                ctx=ast.Load()
            )
        
        # Cria o corpo do método
        method_body = [
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id="Task", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="config",
                            value=ast.Subscript(
                                value=ast.Attribute(
                                    value=ast.Name(id="self", ctx=ast.Load()),
                                    attr="tasks_config",
                                    ctx=ast.Load()
                                ),
                                slice=ast.Constant(value=task_def.config_key),
                                ctx=ast.Load()
                            )
                        ),
                        ast.keyword(
                            arg="agent",
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="self", ctx=ast.Load()),
                                    attr=task_def.agent_name,
                                    ctx=ast.Load()
                                ),
                                args=[],
                                keywords=[]
                            )
                        )
                    ] + ([ast.keyword(arg="context", value=context_tasks_value)] if context_tasks_value else [])
                )
            )
        ]
        
        # Cria o método com o decorador @task
        task_method = ast.FunctionDef(
            name=task_def.name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="self", annotation=None)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None
            ),
            body=method_body,
            decorator_list=[
                ast.Name(id="task", ctx=ast.Load())
            ],
            returns=None
        )
        
        return task_method
    
    def _create_crew_method(self, crew_def: CrewDefinition) -> ast.FunctionDef:
        """Cria o método crew para a classe."""
        # Cria o corpo do método
        method_body = [
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id="Crew", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="name",
                            value=ast.Constant(value=crew_def.name)
                        ),
                        ast.keyword(
                            arg="agents",
                            value=ast.Attribute(
                                value=ast.Name(id="self", ctx=ast.Load()),
                                attr="agents",
                                ctx=ast.Load()
                            )
                        ),
                        ast.keyword(
                            arg="tasks",
                            value=ast.Attribute(
                                value=ast.Name(id="self", ctx=ast.Load()),
                                attr="tasks",
                                ctx=ast.Load()
                            )
                        ),
                        ast.keyword(
                            arg="verbose",
                            value=ast.Constant(value=crew_def.verbose)
                        ),
                        ast.keyword(
                            arg="process",
                            value=ast.Attribute(
                                value=ast.Name(id="Process", ctx=ast.Load()),
                                attr=crew_def.process_type.lower(),
                                ctx=ast.Load()
                            )
                        ),
                        ast.keyword(
                            arg="planning",
                            value=ast.Constant(value=crew_def.planning)
                        )
                    ] + ([
                        ast.keyword(
                            arg="output_log_file",
                            value=ast.Constant(value=crew_def.output_log_file)
                        )
                    ] if crew_def.output_log_file else [])
                )
            )
        ]
        
        # Adiciona docstring ao método
        method_body.insert(0, 
            ast.Expr(
                ast.Constant(
                    value=f"Run the {crew_def.name} crew"
                )
            )
        )
        
        # Cria o método com o decorador @crew
        crew_method = ast.FunctionDef(
            name="crew",
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="self", annotation=None)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None
            ),
            body=method_body,
            decorator_list=[
                ast.Name(id="crew", ctx=ast.Load())
            ],
            returns=ast.Name(id="Crew", ctx=ast.Load())
        )
        
        return crew_method
    
    def _create_main_block(self, crew_def: CrewDefinition) -> ast.If:
        """Cria um bloco if __name__ == "__main__" para testar o crew."""
        # Cria o corpo do bloco if
        if_body = [
            # Cria uma instância da classe
            ast.Assign(
                targets=[ast.Name(id="crew_instance", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id=f"{self.name.replace(' ', '')}Crew", ctx=ast.Load()),
                    args=[],
                    keywords=[]
                )
            ),
            # Obtém o crew
            ast.Assign(
                targets=[ast.Name(id="crew", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="crew_instance", ctx=ast.Load()),
                        attr="crew",
                        ctx=ast.Load()
                    ),
                    args=[],
                    keywords=[]
                )
            ),
            # Executa o crew
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="crew", ctx=ast.Load()),
                        attr="kickoff",
                        ctx=ast.Load()
                    ),
                    args=[],
                    keywords=[]
                )
            )
        ]
        
        # Cria o bloco if
        if_block = ast.If(
            test=ast.Compare(
                left=ast.Name(id="__name__", ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value="__main__")]
            ),
            body=if_body,
            orelse=[]
        )
        
        return if_block
    
    def generate_code(self) -> str:
        """Gera o código Python a partir da AST."""
        return astor.to_source(self.tree)


class DynamicCrewCreator(BaseTool):
    """Uma ferramenta para criar novos Crews no CrewAI dinamicamente."""

    model_config = {
        'arbitrary_types_allowed': True,
        'validate_assignment': True
    }

    name: str = "Dynamic Crew Creator"
    description: str = get_description("DynamicCrewCreator.description")
    args_schema: Type[BaseModel] = CrewDefinition

    def _verify_and_install_packages(self, custom_imports: List[str]) -> None:
        """Verifica e instala pacotes necessários."""
        # Versão simplificada que apenas imprime os pacotes que seriam instalados
        required_packages = set()
        
        for import_statement in custom_imports:
            package = self.get_package_name(import_statement)
            if package:
                required_packages.add(package)
        
        if required_packages:
            print(f"Pacotes que seriam instalados: {', '.join(required_packages)}")
    
    @staticmethod
    def get_package_name(import_statement: str) -> Optional[str]:
        """Extrai o nome do pacote de uma declaração de importação."""
        # Trata casos simples como "import numpy" ou "from numpy import array"
        parts = import_statement.split()
        if len(parts) >= 2 and parts[0] == "import":
            return parts[1].split(".")[0]
        elif len(parts) >= 4 and parts[0] == "from" and parts[2] == "import":
            return parts[1].split(".")[0]
        return None

    def _run(self, 
            name: str, 
            description: str, 
            agents: List[AgentReference],
            tasks: List[TaskDefinition],
            process_type: str = "sequential",
            verbose: bool = True,
            planning: bool = True,
            output_log_file: Optional[str] = None,
            custom_imports: List[str] = []):
        """Cria e salva um novo Crew."""
        register_tool_usage(
            tool_name="DynamicCrewCreator",
            params={
                "name": name,
                "agents_count": len(agents),
                "tasks_count": len(tasks),
                "process_type": process_type
            },
            metadata={
                "custom_imports_count": len(custom_imports)
            }
        )
        
        # Verifica e instala pacotes necessários
        self._verify_and_install_packages(custom_imports)
        
        # Cria o diretório para o crew
        crews_dir = Path("crews")
        crews_dir.mkdir(exist_ok=True)
        
        # Normaliza o nome do diretório da crew (usando snake_case)
        crew_dir_name = name.lower().replace(" ", "_")
        crew_dir = crews_dir / crew_dir_name
        crew_dir.mkdir(exist_ok=True)
        
        # Cria o diretório de configuração
        config_dir = crew_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Cria o construtor de AST
        builder = CrewASTBuilder(name, description)
        
        # Adiciona os imports
        builder.add_imports(custom_imports)
        
        # Cria a classe do crew
        crew_def = CrewDefinition(
            name=name,
            description=description,
            agents=agents,
            tasks=tasks,
            process_type=process_type,
            verbose=verbose,
            planning=planning,
            output_log_file=output_log_file,
            custom_imports=custom_imports
        )
        
        builder.create_crew_class(crew_def)
        
        # Gera o código
        code = builder.generate_code()
        
        # Salva o código em um arquivo com o nome padronizado (snake_case)
        crew_file = crew_dir / f"{crew_dir_name}_crew.py"
        with open(crew_file, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Cria um arquivo __init__.py no diretório da crew
        init_file = crew_dir / "__init__.py"
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f"# {name} Crew\n")
            f.write(f"from .{crew_dir_name}_crew import {name.replace(' ', '')}Crew\n")
        
        return {
            "status": "success",
            "message": f"Crew '{name}' criado com sucesso",
            "file_path": str(crew_file),
            "crew_dir": str(crew_dir)
        }


if __name__ == "__main__":
    # Exemplo de uso do DynamicCrewCreator
    creator = DynamicCrewCreator()
    
    # Verifica se a FerramentaExemplo foi criada pelo dynamic_tool_creator.py
    ferramenta_path = Path("crews/pdca/tools/exemplo_dinamico/ferramentaexemplo_tool.py")
    if not ferramenta_path.exists():
        print("AVISO: Execute primeiro o dynamic_tool_creator.py para criar a FerramentaExemplo")
        print("Continuando com ferramentas simuladas...")
    else:
        print(f"Ferramenta encontrada em: {ferramenta_path}")
    
    result = creator.run(
        name="ExemploCrew",
        description="Equipe de exemplo para demonstrar o fluxo de ferramentas dinâmicas",
        agents=[
            AgentReference(
                name="agente_processador",
                config_key="agente_processador",
                tools=["FerramentaExemploTool"],
                allow_code_execution=True
            ),
            AgentReference(
                name="agente_analisador",
                config_key="agente_analisador",
                tools=[]
            )
        ],
        tasks=[
            TaskDefinition(
                name="processar_texto_task",
                config_key="processar_texto_task",
                agent_name="agente_processador"
            ),
            TaskDefinition(
                name="analisar_resultado_task",
                config_key="analisar_resultado_task",
                agent_name="agente_analisador",
                context_tasks=["processar_texto_task"]
            )
        ],
        process_type="sequential",
        verbose=True,
        planning=True,
        output_log_file="pdca_cycle_20250401_065612.log",
        custom_imports=[
            "import os",
            "import sys",
            "from crews.pdca.tools.exemplo_dinamico.ferramentaexemplo_tool import FerramentaExemploTool"
        ]
    )
    
    print(f"Resultado: {result}")
    print(f"Crew criado em: {result.get('file_path', 'caminho não disponível')}")
    print(f"Diretório do crew: {result.get('crew_dir', 'caminho não disponível')}")
