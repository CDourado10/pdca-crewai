#!/usr/bin/env python
import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from crews.pdca.pdca_models import PlanoAcao

# Add project root directory to sys.path
#project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
#sys.path.append(project_root)

# Load environment variables
load_dotenv()

@CrewBase
class PlanejarCrew:
    """
    Equipe especializada na fase PLAN (Planejar) do ciclo PDCA.
    
    Esta equipe realiza uma análise hermenêutica profunda do problema ou oportunidade,
    identificando causas raízes, estabelecendo metas e desenvolvendo um plano de ação
    detalhado para guiar a implementação.
    """

    @agent
    def analista_problema(self) -> Agent:
        """Especialista em identificação e definição de problemas/oportunidades"""
        return Agent(
            config=self.agents_config['analista_problema'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def analista_contexto(self) -> Agent:
        """Especialista em análise do estado atual e diagnóstico contextual"""
        return Agent(
            config=self.agents_config['analista_contexto'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def analista_causas(self) -> Agent:
        """Especialista em análise de causas raízes"""
        return Agent(
            config=self.agents_config['analista_causas'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def definidor_metas(self) -> Agent:
        """Especialista em estabelecimento de metas e objetivos"""
        return Agent(
            config=self.agents_config['definidor_metas'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def planejador_acao(self) -> Agent:
        """Especialista em desenvolvimento de planos de ação"""
        return Agent(
            config=self.agents_config['planejador_acao'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def integrador_plano(self) -> Agent:
        """Especialista em integração e síntese do plano completo"""
        return Agent(
            config=self.agents_config['integrador_plano'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )

    @task
    def definir_problema_task(self) -> Task:
        """Tarefa de identificação e definição do problema/oportunidade"""
        return Task(
            config=self.tasks_config['definir_problema_task'],
            agent=self.analista_problema(),
            output_file="crews/pdca/resultados/planejar/definicao_problema.txt",
            create_directory=True
        )

    @task
    def analisar_contexto_task(self) -> Task:
        """Tarefa de análise do estado atual e diagnóstico contextual"""
        return Task(
            config=self.tasks_config['analisar_contexto_task'],
            agent=self.analista_contexto(),
            context=[self.definir_problema_task()],
            output_file="crews/pdca/resultados/planejar/analise_contexto.txt",
            create_directory=True
        )

    @task
    def identificar_causas_task(self) -> Task:
        """Tarefa de análise de causas raízes"""
        return Task(
            config=self.tasks_config['identificar_causas_task'],
            agent=self.analista_causas(),
            context=[self.definir_problema_task(), self.analisar_contexto_task()],
            output_file="crews/pdca/resultados/planejar/analise_causas.txt",
            create_directory=True
        )

    @task
    def estabelecer_metas_task(self) -> Task:
        """Tarefa de estabelecimento de metas e objetivos"""
        return Task(
            config=self.tasks_config['estabelecer_metas_task'],
            agent=self.definidor_metas(),
            context=[self.definir_problema_task(), self.identificar_causas_task()],
            output_file="crews/pdca/resultados/planejar/metas_objetivos.txt",
            create_directory=True
        )

    @task
    def desenvolver_plano_task(self) -> Task:
        """Tarefa de desenvolvimento do plano de ação"""
        return Task(
            config=self.tasks_config['desenvolver_plano_task'],
            agent=self.planejador_acao(),
            context=[self.estabelecer_metas_task(), self.identificar_causas_task()],
            output_file="crews/pdca/resultados/planejar/plano_acao.txt",
            create_directory=True
        )

    @task
    def integrar_plano_final_task(self) -> Task:
        """Tarefa de integração e síntese do plano completo"""
        return Task(
            config=self.tasks_config['integrar_plano_final_task'],
            agent=self.integrador_plano(),
            context=[
                self.definir_problema_task(),
                self.analisar_contexto_task(),
                self.identificar_causas_task(),
                self.estabelecer_metas_task(),
                self.desenvolver_plano_task()
            ],
            output_file="crews/pdca/resultados/planejar/plano_completo.json",
            output_pydantic=PlanoAcao,
            create_directory=True
        )

    @crew
    def crew(self) -> Crew:
        """Executa a equipe de planejamento PDCA"""
        crew = Crew(
            name="Equipe de Planejamento PDCA",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=True,
            output_log_file="crews/pdca/resultados/planejar/planejar_crew_log.txt"
        )
        return crew

if __name__ == "__main__":
    # Exemplo de uso da equipe
    crew = PlanejarCrew()
    '''
    resultados = crew.crew().kickoff(inputs={
        "problema": "Baixa produtividade na linha de montagem",
        "contexto": "Empresa de manufatura com 50 funcionários, operando há 10 anos",
        "objetivo": "Aumentar a produtividade em 30% nos próximos 6 meses",
        "restricoes": ["Orçamento limitado", "Não pode interromper produção"],
        "prazo": "6 meses",
        "recursos": ["Equipe atual", "Sistema de gestão existente", "Consultoria externa"],
        "definicao_problema": "Baixa produtividade na linha de montagem afetando os resultados financeiros",
        # Variáveis de template necessárias como placeholders
        "causas_identificadas": "Serão identificadas durante a análise",
        "metas_estabelecidas": "Serão estabelecidas durante o planejamento",
        "plano_acao": "Será desenvolvido durante o planejamento",
        "analise_contexto": "Será desenvolvida durante a análise"
    })
    '''

    resultados = crew.crew().kickoff(inputs={
        "problema": "falta de CRM para gerenciar clientes",
        "contexto": "Contrutora de condominios, que vende lotes.",
        "objetivo": "CRM de clientes, com emissao de boletos e envios de mensagems via whatsapp",
        "restricoes": "falta de pessoal, todo o sistema deve ser criado e gerenciado de forma automatizada, por agentes do crewai",
        "prazo": "6 meses",
        "recursos": "sem recursos para o projeto",
        "definicao_problema": "Falta de CRM para gerenciar clientes",
        # Variáveis de template necessárias como placeholders
        "causas_identificadas": "Serão identificadas durante a análise",
        "metas_estabelecidas": "Serão estabelecidas durante o planejamento",
        "plano_acao": "Será desenvolvido durante o planejamento",
        "analise_contexto": "Será desenvolvida durante a análise"
    })

    print("Resultado da execução:")
    print(f"Tipo de resultado: {type(resultados)}")
    
    if hasattr(resultados, 'pydantic'):
        print("\nResultado em formato Pydantic:")
        plano = resultados.pydantic
        print(plano)
    else:
        print("\nResultado bruto:")
        print(resultados)
