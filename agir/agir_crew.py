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

# Importar o modelo Pydantic para o resultado da ação corretiva
from crews.pdca.pdca_models import AcaoCorretiva

@CrewBase
class AgirCrew:
    """
    Equipe especializada na fase ACT (Agir) do ciclo PDCA.
    
    Esta equipe desenvolve soluções para os problemas identificados na fase de verificação,
    padroniza as melhorias bem-sucedidas, corrige desvios, documenta lições aprendidas
    e prepara recomendações para o próximo ciclo PDCA.
    """

    @agent
    def solucionador_problemas(self) -> Agent:
        """Especialista em desenvolvimento de soluções para problemas identificados"""
        return Agent(
            config=self.agents_config['solucionador_problemas'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def padronizador_melhorias(self) -> Agent:
        """Especialista em padronização e institucionalização de melhorias"""
        return Agent(
            config=self.agents_config['padronizador_melhorias'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def corretor_desvios(self) -> Agent:
        """Especialista em correção de desvios e ajustes de curso"""
        return Agent(
            config=self.agents_config['corretor_desvios'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def documentador_licoes(self) -> Agent:
        """Especialista em documentação de lições aprendidas"""
        return Agent(
            config=self.agents_config['documentador_licoes'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )
    
    @agent
    def preparador_proximo_ciclo(self) -> Agent:
        """Especialista em preparação para o próximo ciclo PDCA"""
        return Agent(
            config=self.agents_config['preparador_proximo_ciclo'],
            verbose=True,
            llm="azure/gpt-4o-mini"
        )

    @task
    def desenvolver_solucoes_task(self) -> Task:
        """Tarefa de desenvolvimento de soluções para problemas identificados"""
        return Task(
            config=self.tasks_config['desenvolver_solucoes_task'],
            agent=self.solucionador_problemas(),
            output_file="crews/pdca/resultados/agir/solucoes_desenvolvidas.txt",
            create_directory=True
        )

    @task
    def padronizar_melhorias_task(self) -> Task:
        """Tarefa de padronização e institucionalização de melhorias"""
        return Task(
            config=self.tasks_config['padronizar_melhorias_task'],
            agent=self.padronizador_melhorias(),
            context=[self.desenvolver_solucoes_task()],
            output_file="crews/pdca/resultados/agir/padronizacao_melhorias.txt",
            create_directory=True
        )

    @task
    def corrigir_desvios_task(self) -> Task:
        """Tarefa de correção de desvios e ajustes de curso"""
        return Task(
            config=self.tasks_config['corrigir_desvios_task'],
            agent=self.corretor_desvios(),
            context=[self.desenvolver_solucoes_task()],
            output_file="crews/pdca/resultados/agir/acoes_corretivas.txt",
            create_directory=True
        )

    @task
    def documentar_licoes_task(self) -> Task:
        """Tarefa de documentação de lições aprendidas"""
        return Task(
            config=self.tasks_config['documentar_licoes_task'],
            agent=self.documentador_licoes(),
            context=[
                self.desenvolver_solucoes_task(),
                self.padronizar_melhorias_task(),
                self.corrigir_desvios_task()
            ],
            output_file="crews/pdca/resultados/agir/licoes_aprendidas.txt",
            create_directory=True
        )

    @task
    def preparar_proximo_ciclo_task(self) -> Task:
        """Tarefa de preparação para o próximo ciclo PDCA"""
        return Task(
            config=self.tasks_config['preparar_proximo_ciclo_task'],
            agent=self.preparador_proximo_ciclo(),
            context=[
                self.desenvolver_solucoes_task(),
                self.padronizar_melhorias_task(),
                self.corrigir_desvios_task(),
                self.documentar_licoes_task()
            ],
            output_file="crews/pdca/resultados/agir/recomendacoes_proximo_ciclo.json",
            output_pydantic=AcaoCorretiva,
            create_directory=True
        )

    @crew
    def crew(self) -> Crew:
        """Executa a equipe de ação corretiva PDCA"""
        crew = Crew(
            name="Equipe de Ação Corretiva PDCA",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=True,
            output_log_file="crews/pdca/resultados/agir/agir_crew_log.txt"
        )
        return crew

if __name__ == "__main__":
    # Exemplo de uso da equipe
    crew = AgirCrew()
    
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
    
    resultado_verificacao = {
        "metricas_analisadas": "Metas iniciais não atingidas. Apenas a pesquisa de fornecedores foi concluída.",
        "desvios_identificados": "Automação da emissão de boletos e integração com WhatsApp não foram abordadas.",
        "causas_desvios": "Falta de foco nas funções críticas e dificuldades na coleta de informações.",
        "sucessos_identificados": "Pesquisa e análise de fornecedores concluídas com sucesso. Escolha do Zoho CRM baseada em custo-benefício.",
        "relatorio": "A implementação do CRM atualmente apresenta um equilíbrio entre conquistas e desafios. É necessário redirecionar esforços para as funcionalidades pendentes."
    }
    
    # Inputs no formato esperado pelo PDCAFlow
    resultados = crew.crew().kickoff(inputs={
        "plano_acao": plano_acao,
        "resultado_execucao": resultado_execucao,
        "resultado_verificacao": resultado_verificacao,
        "objetivo": "CRM de clientes, com emissao de boletos e envios de mensagens via WhatsApp",
        "problema": "Falta de CRM para gerenciar clientes"
    })
    
    print("Resultado da ação corretiva:")
    print(f"Tipo de resultado: {type(resultados)}")
    
    if hasattr(resultados, 'pydantic'):
        print("\nResultado em formato Pydantic:")
        print(resultados.pydantic)
    else:
        print("\nResultado bruto:")
        print(resultados)
