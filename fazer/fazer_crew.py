#!/usr/bin/env python
import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from crews.pdca.pdca_models import ResultadoExecucao

# Add project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

@CrewBase
class FazerCrew:
    """
    Equipe especializada na fase DO (Fazer) do ciclo PDCA.
    
    Esta equipe implementa o plano de ação desenvolvido na fase de planejamento,
    executando as atividades conforme o cronograma estabelecido, coletando dados
    durante a execução e documentando todo o processo.
    """

    @agent
    def coordenador_implementacao(self) -> Agent:
        """Especialista em coordenação de implementação de planos"""
        return Agent(
            config=self.agents_config['coordenador_implementacao'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def executor_tarefas(self) -> Agent:
        """Especialista em execução prática de tarefas"""
        return Agent(
            config=self.agents_config['executor_tarefas'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def coletor_dados(self) -> Agent:
        """Especialista em coleta e registro de dados durante a execução"""
        return Agent(
            config=self.agents_config['coletor_dados'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def gerenciador_recursos(self) -> Agent:
        """Especialista em gerenciamento de recursos durante a implementação"""
        return Agent(
            config=self.agents_config['gerenciador_recursos'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def monitor_progresso(self) -> Agent:
        """Especialista em monitoramento de progresso e identificação de desvios"""
        return Agent(
            config=self.agents_config['monitor_progresso'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def documentador_processo(self) -> Agent:
        """Especialista em documentação do processo de implementação"""
        return Agent(
            config=self.agents_config['documentador_processo'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )

    @task
    def preparar_implementacao_task(self) -> Task:
        """Tarefa de preparação para implementação do plano"""
        return Task(
            config=self.tasks_config['preparar_implementacao_task'],
            agent=self.coordenador_implementacao(),
            output_file="crews/pdca/resultados/fazer/preparacao_implementacao.txt",
            create_directory=True
        )

    @task
    def executar_atividades_task(self) -> Task:
        """Tarefa de execução das atividades planejadas"""
        return Task(
            config=self.tasks_config['executar_atividades_task'],
            agent=self.executor_tarefas(),
            context=[self.preparar_implementacao_task()],
            output_file="crews/pdca/resultados/fazer/execucao_atividades.txt",
            create_directory=True
        )

    @task
    def coletar_dados_task(self) -> Task:
        """Tarefa de coleta de dados durante a execução"""
        return Task(
            config=self.tasks_config['coletar_dados_task'],
            agent=self.coletor_dados(),
            context=[self.executar_atividades_task()],
            output_file="crews/pdca/resultados/fazer/dados_coletados.txt",
            create_directory=True
        )

    @task
    def gerenciar_recursos_task(self) -> Task:
        """Tarefa de gerenciamento de recursos durante a implementação"""
        return Task(
            config=self.tasks_config['gerenciar_recursos_task'],
            agent=self.gerenciador_recursos(),
            context=[self.executar_atividades_task()],
            output_file="crews/pdca/resultados/fazer/gerenciamento_recursos.txt",
            create_directory=True
        )

    @task
    def monitorar_progresso_task(self) -> Task:
        """Tarefa de monitoramento de progresso e identificação de desvios"""
        return Task(
            config=self.tasks_config['monitorar_progresso_task'],
            agent=self.monitor_progresso(),
            context=[self.executar_atividades_task(), self.coletar_dados_task()],
            output_file="crews/pdca/resultados/fazer/monitoramento_progresso.txt",
            create_directory=True
        )

    @task
    def documentar_implementacao_task(self) -> Task:
        """Tarefa de documentação do processo de implementação"""
        return Task(
            config=self.tasks_config['documentar_implementacao_task'],
            agent=self.documentador_processo(),
            context=[
                self.preparar_implementacao_task(),
                self.executar_atividades_task(),
                self.coletar_dados_task(),
                self.gerenciar_recursos_task(),
                self.monitorar_progresso_task()
            ],
            output_file="crews/pdca/resultados/fazer/documentacao_implementacao.json",
            output_pydantic=ResultadoExecucao,
            create_directory=True
        )

    @crew
    def crew(self) -> Crew:
        """Executa a equipe de implementação PDCA"""
        crew = Crew(
            name="Equipe de Implementação PDCA",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=True,
            output_log_file="crews/pdca/resultados/fazer/fazer_crew_log.txt"
        )
        return crew

if __name__ == "__main__":
    # Exemplo de uso da equipe
    crew = FazerCrew()
    
    # Criar um plano de ação no formato esperado pelo PDCAFlow
    plano_acao = {
        "objetivos": "Implementar CRM básico, Automatizar emissão de boletos, Integrar com WhatsApp",
        "atividades": "1. Pesquisar e analisar fornecedores de CRM - Prazo: Mês 1, Prioridade: Alta. Descrição: Realizar uma pesquisa detalhada de diferentes fornecedores de CRM disponíveis no mercado. 2. Configurar o CRM e integrar aos sistemas existentes - Prazo: Mês 2, Prioridade: Alta. Descrição: Realizar a configuração do sistema CRM e assegurar sua integração com os sistemas já utilizados.",
        "cronograma": "Início: 01-05-2025, Fim: 01-11-2025, Marcos: Configuração do CRM concluída no final do Mês 2",
        "recursos_necessarios": "Orçamento para aquisição do CRM, Infraestrutura tecnológica para suporte do CRM",
        "responsaveis": "Pesquisar e analisar fornecedores de CRM: Equipe de TI",
        "metricas": "Taxa de utilização do CRM: Proporção de usuários que utilizam o CRM após implementação - Meta: 75 por cento"
    }
    
    # Inputs no formato esperado pelo PDCAFlow
    resultados = crew.crew().kickoff(inputs={
        # Inputs principais esperados pelo PDCAFlow
        "plano_acao": plano_acao,
        "contexto": "Construtora de condomínios que vende lotes. Necessita de um CRM para gerenciar clientes, emitir boletos e enviar mensagens via WhatsApp.",
        "recursos": "Equipe de TI, orçamento limitado para aquisição de software",
        
        # Variáveis de template necessárias como placeholders
        "preparacao_implementacao": "Será desenvolvida durante a execução",
        "atividades_executadas": "Serão registradas durante a execução",
        "dados_coletados": "Serão coletados durante a execução",
        "recursos_gerenciados": "Serão gerenciados durante a execução",
        "progresso_monitorado": "Será monitorado durante a execução"
    })
    
    print("Resultado da execução:")
    print(f"Tipo de resultado: {type(resultados)}")
    
    if hasattr(resultados, 'pydantic'):
        print("\nResultado em formato Pydantic:")
        print(resultados.pydantic)
    else:
        print("\nResultado bruto:")
        print(resultados)
