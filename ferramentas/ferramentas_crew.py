#!/usr/bin/env python
"""
Implementação da FerramentasCrew - Equipe especializada em criação dinâmica de ferramentas.

Esta equipe é responsável por criar dinamicamente agentes, tarefas, equipes e ferramentas
específicas para cada fase do ciclo PDCA, adaptando-se ao contexto do problema.
"""

import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

# Adicionar diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

# Importar ferramentas dinâmicas
from crews.pdca.tools.dynamic_agent_creator import AgentYAMLConfigWriter  # noqa: E402
from crews.pdca.tools.dynamic_task_creator import TaskYAMLConfigWriter  # noqa: E402
from crews.pdca.tools.dynamic_crew_creator import DynamicCrewCreator  # noqa: E402
from crews.pdca.tools.dynamic_tool_creator import DynamicToolCreator  # noqa: E402
from crews.pdca.tools.crew_executor import CrewExecutor  # noqa: E402

# Carregar variáveis de ambiente
load_dotenv()

@CrewBase
class FerramentasCrew:
    """
    Equipe especializada na criação dinâmica de ferramentas para o ciclo PDCA.
    
    Esta equipe cria agentes, tarefas, equipes e ferramentas específicas para cada
    fase do ciclo PDCA, adaptando-se ao contexto do problema e às necessidades
    específicas de cada situação.
    """

    @agent
    def especialista_agentes(self) -> Agent:
        """Especialista em criação de agentes"""
        return Agent(
            config=self.agents_config['especialista_agentes'],
            verbose=True,
            tools=[AgentYAMLConfigWriter()],
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def especialista_tarefas(self) -> Agent:
        """Especialista em definição de tarefas"""
        return Agent(
            config=self.agents_config['especialista_tarefas'],
            verbose=True,
            tools=[TaskYAMLConfigWriter()],
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def especialista_equipes(self) -> Agent:
        """Especialista em formação de equipes"""
        return Agent(
            config=self.agents_config['especialista_equipes'],
            verbose=True,
            tools=[DynamicCrewCreator()],
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def especialista_ferramentas(self) -> Agent:
        """Especialista em criação de ferramentas"""
        return Agent(
            config=self.agents_config['especialista_ferramentas'],
            verbose=True,
            tools=[DynamicToolCreator()],
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def integrador_recursos(self) -> Agent:
        """Integrador de recursos"""
        return Agent(
            config=self.agents_config['integrador_recursos'],
            verbose=True,
            tools=[
                # Ferramenta para executar e testar as crews criadas
                CrewExecutor()
            ],
            llm="azure/gpt-4o-mini"
        )

    @task
    def criar_ferramentas_task(self) -> Task:
        """Tarefa de criação de ferramentas especializadas"""
        return Task(
            config=self.tasks_config['criar_ferramentas_task'],
            agent=self.especialista_ferramentas(),
            tools=[DynamicToolCreator()],
            output_file="ferramentas_criadas.py"
        )

    @task
    def criar_equipe_task(self) -> Task:
        """Tarefa de criação de estrutura de equipe otimizada"""
        return Task(
            config=self.tasks_config['criar_equipe_task'],
            agent=self.especialista_equipes(),
            tools=[DynamicCrewCreator()],
            context=[self.criar_ferramentas_task()],
            output_file="equipe_criada.yaml"
        )

    @task
    def criar_agentes_task(self) -> Task:
        """Tarefa de criação de agentes especializados"""
        return Task(
            config=self.tasks_config['criar_agentes_task'],
            agent=self.especialista_agentes(),
            tools=[AgentYAMLConfigWriter()],
            context=[self.criar_ferramentas_task(), self.criar_equipe_task()],
            output_file="agentes_criados.yaml"
        )

    @task
    def criar_tarefas_task(self) -> Task:
        """Tarefa de criação de tarefas bem estruturadas"""
        return Task(
            config=self.tasks_config['criar_tarefas_task'],
            agent=self.especialista_tarefas(),
            tools=[TaskYAMLConfigWriter()],
            context=[self.criar_ferramentas_task(), self.criar_equipe_task(), self.criar_agentes_task()],
            output_file="tarefas_criadas.yaml"
        )

    @task
    def integrar_recursos_task(self) -> Task:
        """Tarefa de integração de todos os recursos criados"""
        return Task(
            config=self.tasks_config['integrar_recursos_task'],
            agent=self.integrador_recursos(),
            tools=[
                # Ferramenta para executar e testar as crews criadas
                CrewExecutor()
            ],
            context=[
                self.criar_ferramentas_task(),
                self.criar_equipe_task(),
                self.criar_agentes_task(),
                self.criar_tarefas_task()
            ],
            output_file="recursos_integrados.json"
        )

    @crew
    def crew(self) -> Crew:
        """Executa a equipe de criação de ferramentas"""
        crew = Crew(
            name="Equipe de Criação de Ferramentas PDCA",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=False,  # Desativar planejamento automático para evitar erros
            output_log_file="ferramentas_crew_log.txt"
        )
        return crew

if __name__ == "__main__":
    crew = FerramentasCrew()

    inputs = {
        "problema": "Falta de pessoas para implementar e usar o CRM",
        "contexto": "Construtora de condomínios que vende lotes. Necessita de um CRM para gerenciar clientes, emitir boletos e enviar mensagens via WhatsApp. Necessita de agentes de LLM para implementar e usar o CRM",
        "fase_pdca": "Fase de planejamento",
        "requisitos": "Equipe de TI totalmente formada por agentes de LLM, orçamento limitado para aquisição de software"
    }

    resultado = crew.crew().kickoff(inputs=inputs)

    print(resultado)
    
