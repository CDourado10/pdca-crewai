#!/usr/bin/env python
"""
Equipe especializada em criação de documentação técnica.

Esta equipe projeta, desenvolve, valida e finaliza documentação
técnica para diferentes componentes e públicos-alvo.
"""

# Importações só do necessário para a classe
import os
import sys

from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

# Importações para Knowledge
from crewai.knowledge.source.crew_docling_source import CrewDoclingSource

# Adicionar diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(project_root)

# Importar ferramentas necessárias
from crews.pdca.tools.knowledge_file_writer import KnowledgeFileWriterTool  # noqa: E402
from crews.pdca.tools.markdown_formatter import MarkdownFormatterTool  # noqa: E402
from crews.pdca.tools.documentacao_writer import DocumentacaoWriterTool  # noqa: E402

# Importar modelos
from crews.pdca.pdca_models import DocumentacaoOutput  # noqa: E402

# Carregar variáveis de ambiente
load_dotenv()

# Configurar as fontes de conhecimento usando docling para arquivos Markdown
# Nota: O CrewAI busca automaticamente na pasta 'knowledge', então usamos caminhos relativos

# Conhecimento específico para o arquiteto
arquiteto_knowledge = CrewDoclingSource(
    file_paths=[
        "documentacao/padroes_estrutura_documentacao.md",
        "documentacao/boas_praticas_arquitetura_docs.md"
    ]
)

# Conhecimento específico para o redator
redator_knowledge = CrewDoclingSource(
    file_paths=[
        "documentacao/tecnicas_escrita_tecnica.md",
        "documentacao/exemplos_documentacao.md"
    ]
)

# Conhecimento específico para o especialista em validação
validacao_knowledge = CrewDoclingSource(
    file_paths=[
        "documentacao/criterios_qualidade_docs.md",
        "documentacao/checklists_validacao.md"
    ]
)

@CrewBase
class DocumentacaoCrew:
    """
    Equipe especializada em criação de documentação técnica.
    
    Esta equipe tem como responsabilidade:
    1. Projetar a estrutura da documentação com base em requisitos detalhados
    2. Criar conteúdo técnico claro, preciso e bem estruturado
    3. Validar a qualidade, precisão e usabilidade da documentação
    4. Finalizar o pacote de documentação para entrega
    """

    @agent
    def arquiteto_documentacao(self) -> Agent:
        """Arquiteto especializado em estruturação de documentação"""
        return Agent(
            config=self.agents_config['arquiteto_documentacao'],
            verbose=True,
            tools=[KnowledgeFileWriterTool()],
            llm="azure/gpt-4o",
            knowledge_sources=[arquiteto_knowledge]
        )
    
    @agent
    def redator_tecnico(self) -> Agent:
        """Redator especializado em criação de conteúdo técnico"""
        return Agent(
            config=self.agents_config['redator_tecnico'],
            verbose=True,
            tools=[MarkdownFormatterTool()],
            llm="azure/gpt-4o",
            knowledge_sources=[redator_knowledge]
        )
    
    @agent
    def especialista_validacao(self) -> Agent:
        """Especialista em validação de qualidade da documentação"""
        return Agent(
            config=self.agents_config['especialista_validacao'],
            verbose=True,
            tools=[],
            llm="azure/gpt-4o",
            knowledge_sources=[validacao_knowledge]
        )
    
    @task
    def projetar_estrutura_documentacao_task(self) -> Task:
        """Tarefa de projeto da estrutura de documentação"""
        return Task(
            config=self.tasks_config['projetar_estrutura_documentacao_task'],
            agent=self.arquiteto_documentacao(),
            output_file="crews/pdca/resultados/documentacao/estrutura_documentacao.txt",
            create_directory=True
        )
    
    @task
    def criar_conteudo_documentacao_task(self) -> Task:
        """Tarefa de criação do conteúdo da documentação"""
        return Task(
            config=self.tasks_config['criar_conteudo_documentacao_task'],
            agent=self.redator_tecnico(),
            context=[self.projetar_estrutura_documentacao_task()],
            output_file="crews/pdca/resultados/documentacao/conteudo_documentacao.md",
            create_directory=True
        )
    
    @task
    def validar_documentacao_task(self) -> Task:
        """Tarefa de validação da documentação"""
        return Task(
            config=self.tasks_config['validar_documentacao_task'],
            agent=self.especialista_validacao(),
            context=[
                self.projetar_estrutura_documentacao_task(),
                self.criar_conteudo_documentacao_task()
            ],
            output_file="crews/pdca/resultados/documentacao/validacao_documentacao.txt",
            create_directory=True
        )
    
    @task
    def finalizar_documentacao_task(self) -> Task:
        """Tarefa de finalização e preparação do pacote de documentação"""
        return Task(
            config=self.tasks_config['finalizar_documentacao_task'],
            agent=self.redator_tecnico(),
            context=[
                self.projetar_estrutura_documentacao_task(),
                self.criar_conteudo_documentacao_task(),
                self.validar_documentacao_task()
            ],
            tools=[DocumentacaoWriterTool()],
            output_file="crews/pdca/resultados/documentacao/documentacao_final.json",
            output_pydantic=DocumentacaoOutput,
            create_directory=True
        )
    
    @crew
    def crew(self) -> Crew:
        """Executa a equipe de criação de documentação"""
        crew = Crew(
            name="Equipe de Documentação Técnica",
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            planning=False,
            planning_llm="azure/gpt-4o",
            output_log_file="crews/pdca/resultados/documentacao/log_documentacao.txt"
        )
        return crew

if __name__ == "__main__":
    # Criação da equipe
    crew = DocumentacaoCrew()
    
    # Exemplo de uso
    inputs_api = {
        # Informações sobre o tipo e contexto da documentação
        "tipo_documentacao": "Documentação de API REST",
        "contexto_projeto": "Sistema de gerenciamento de tarefas do PDCA com múltiplas equipes especializadas",
        "publico_alvo": "Desenvolvedores que precisam integrar ou estender o sistema",
        
        # Detalhes específicos
        "finalidade": "Permitir que desenvolvedores entendam e utilizem as APIs do sistema de forma eficiente",
        "componentes_tecnicos": "Endpoints de API, estruturas de dados, exemplos de requisições, códigos de resposta, autenticação",
        "nivel_detalhamento": "Detalhado, com exemplos completos de requisição e resposta para cada endpoint",
        "requisitos_especiais": "Incluir diagramas de sequência para fluxos complexos e postman collection para testes",
        "formatos_entrega": "Markdown para GitHub, HTML para portal de documentação, e PDF para distribuição offline"
    }
    
    # Executar a equipe com os inputs de exemplo
    resultado = crew.crew().kickoff(inputs=inputs_api)
    print(resultado)
