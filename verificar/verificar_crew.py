#!/usr/bin/env python
import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

# Add project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

# Importar o modelo Pydantic para o resultado da verificação
from crews.pdca.pdca_models import ResultadoVerificacao

@CrewBase
class VerificarCrew:
    """
    Equipe especializada na fase CHECK (Verificar) do ciclo PDCA.
    
    Esta equipe analisa criticamente os resultados obtidos após a implementação,
    comparando-os com as metas estabelecidas, identificando desvios e suas causas,
    e avaliando a eficácia das ações implementadas.
    """

    @agent
    def analista_dados(self) -> Agent:
        """Especialista em análise de dados coletados"""
        return Agent(
            config=self.agents_config['analista_dados'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def avaliador_resultados(self) -> Agent:
        """Especialista em avaliação de resultados versus metas"""
        return Agent(
            config=self.agents_config['avaliador_resultados'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def analista_desvios(self) -> Agent:
        """Especialista em identificação e análise de desvios"""
        return Agent(
            config=self.agents_config['analista_desvios'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def avaliador_eficacia(self) -> Agent:
        """Especialista em avaliação da eficácia das ações implementadas"""
        return Agent(
            config=self.agents_config['avaliador_eficacia'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def visualizador_dados(self) -> Agent:
        """Especialista em visualização e comunicação de resultados"""
        return Agent(
            config=self.agents_config['visualizador_dados'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def sintetizador_verificacao(self) -> Agent:
        """Especialista em síntese e integração da verificação completa"""
        return Agent(
            config=self.agents_config['sintetizador_verificacao'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )

    @task
    def analisar_dados_task(self) -> Task:
        """Tarefa de análise dos dados coletados"""
        return Task(
            config=self.tasks_config['analisar_dados_task'],
            agent=self.analista_dados(),
            output_file="crews/pdca/resultados/verificar/analise_dados.txt",
            create_directory=True
        )

    @task
    def comparar_resultados_metas_task(self) -> Task:
        """Tarefa de comparação dos resultados com as metas estabelecidas"""
        return Task(
            config=self.tasks_config['comparar_resultados_metas_task'],
            agent=self.avaliador_resultados(),
            context=[self.analisar_dados_task()],
            output_file="crews/pdca/resultados/verificar/comparacao_resultados_metas.txt",
            create_directory=True
        )

    @task
    def identificar_analisar_desvios_task(self) -> Task:
        """Tarefa de identificação e análise de desvios"""
        return Task(
            config=self.tasks_config['identificar_analisar_desvios_task'],
            agent=self.analista_desvios(),
            context=[self.comparar_resultados_metas_task()],
            output_file="crews/pdca/resultados/verificar/analise_desvios.txt",
            create_directory=True
        )

    @task
    def avaliar_eficacia_acoes_task(self) -> Task:
        """Tarefa de avaliação da eficácia das ações implementadas"""
        return Task(
            config=self.tasks_config['avaliar_eficacia_acoes_task'],
            agent=self.avaliador_eficacia(),
            context=[self.identificar_analisar_desvios_task()],
            output_file="crews/pdca/resultados/verificar/avaliacao_eficacia.txt",
            create_directory=True
        )

    @task
    def criar_visualizacoes_task(self) -> Task:
        """Tarefa de criação de visualizações dos resultados"""
        return Task(
            config=self.tasks_config['criar_visualizacoes_task'],
            agent=self.visualizador_dados(),
            context=[
                self.analisar_dados_task(),
                self.comparar_resultados_metas_task(),
                self.identificar_analisar_desvios_task()
            ],
            output_file="crews/pdca/resultados/verificar/visualizacoes_resultados.txt",
            create_directory=True
        )

    @task
    def sintetizar_verificacao_task(self) -> Task:
        """Tarefa de síntese e integração da verificação completa"""
        return Task(
            config=self.tasks_config['sintetizar_verificacao_task'],
            agent=self.sintetizador_verificacao(),
            context=[
                self.analisar_dados_task(),
                self.comparar_resultados_metas_task(),
                self.identificar_analisar_desvios_task(),
                self.avaliar_eficacia_acoes_task(),
                self.criar_visualizacoes_task()
            ],
            output_file="crews/pdca/resultados/verificar/relatorio_verificacao.json",
            output_pydantic=ResultadoVerificacao,
            create_directory=True
        )

    @crew
    def crew(self) -> Crew:
        """Executa a equipe de verificação PDCA"""
        crew = Crew(
            name="Equipe de Verificação PDCA",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=True,
            output_log_file="crews/pdca/resultados/verificar/verificar_crew_log.txt"
        )
        return crew

if __name__ == "__main__":
    # Exemplo de uso da equipe
    crew = VerificarCrew()
    
    # Criar exemplos de dados no formato que o PDCAFlow envia
    plano_acao = {
        "objetivos": "Implementar CRM básico, Automatizar emissão de boletos, Integrar com WhatsApp",
        "atividades": "1. Pesquisar e analisar fornecedores de CRM - Prazo: Mês 1, Prioridade: Alta. 2. Configurar o CRM e integrar aos sistemas existentes - Prazo: Mês 2, Prioridade: Alta.",
        "cronograma": "Início: 01-05-2025, Fim: 01-11-2025, Marcos: Configuração do CRM concluída no final do Mês 2",
        "recursos_necessarios": "Orçamento para aquisição do CRM, Infraestrutura tecnológica para suporte do CRM",
        "responsaveis": "Pesquisar e analisar fornecedores de CRM: Equipe de TI",
        "metricas": "Taxa de utilização do CRM: Proporção de usuários que utilizam o CRM após implementação - Meta: 75 por cento"
    }
    
    resultado_execucao = {
        "atividades_concluidas": "Pesquisar e analisar fornecedores de CRM",
        "dados_coletados": "Fornecedores analisados: Salesforce, Pipedrive, Zoho CRM. Decisão: Zoho CRM escolhido por melhor custo-benefício.",
        "obstaculos_encontrados": "Dificuldades em obter informações compatíveis sobre a infraestrutura para o Zoho CRM.",
        "ajustes_realizados": "Reunião extra com o departamento de TI para validar a compatibilidade do CRM.",
        "documentacao": "O processo de implementação do CRM começou em 01-05-2025 e inclui a pesquisa de fornecedores e integração das ferramentas necessárias."
    }
    
    # Inputs no formato esperado pelo PDCAFlow
    resultados = crew.crew().kickoff(inputs={
        "plano_acao": plano_acao,
        "resultado_execucao": resultado_execucao,
        "objetivo": "CRM de clientes, com emissao de boletos e envios de mensagens via WhatsApp",
        "metricas": "Taxa de utilização do CRM: Proporção de usuários que utilizam o CRM após implementação - Meta: 75 por cento"
    })
    
    print("Resultado da verificação:")
    print(f"Tipo de resultado: {type(resultados)}")
    
    if hasattr(resultados, 'pydantic'):
        print("\nResultado em formato Pydantic:")
        print(resultados.pydantic)
    else:
        print("\nResultado bruto:")
        print(resultados)
