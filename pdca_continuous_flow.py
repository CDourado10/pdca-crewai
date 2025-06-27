#!/usr/bin/env python
"""
PDCA Continuous Flow - Implementação do ciclo PDCA contínuo usando ferramentas dinâmicas

Este módulo estende o PDCAFlow para criar uma versão contínua e adaptativa do ciclo PDCA,
integrando ferramentas dinâmicas para criação de agentes, equipes, tarefas e ferramentas
específicas para cada contexto de problema.

O fluxo PDCA contínuo permite:
- Adaptação automática de equipes baseada nos resultados de ciclos anteriores
- Busca de conhecimento relevante em ciclos passados
- Geração de ferramentas específicas para cada contexto
- Criação automática de novos ciclos a partir das recomendações do ciclo atual
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from crewai.flow.flow import Flow, listen, start

# Adicionar diretório raiz do projeto ao sys.path antes de importar módulos locais
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importações locais - noqa: E402 (suprimir aviso de importação não estar no topo do arquivo)
from crews.pdca.pdca_flow import PDCAFlow, PDCAState, PDCAStatus  # noqa: E402
from crews.pdca.ferramentas.ferramentas_crew import FerramentasCrew  # noqa: E402
from crews.pdca.tools.dynamic_agent_creator import AgentYAMLConfigWriter, AgentConfig  # noqa: E402
from crews.pdca.tools.dynamic_task_creator import TaskYAMLConfigWriter  # noqa: E402
from crews.pdca.tools.dynamic_crew_creator import DynamicCrewCreator  # noqa: E402
from crews.pdca.tools.dynamic_tool_creator import DynamicToolCreator, ToolParameter  # noqa: E402

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDirectorySearchTool:
    """Versão simplificada da ferramenta de busca em diretórios"""
    def run(self, query: str, directory: str) -> str:
        logger.info(f"Buscando por '{query}' no diretório {directory}")
        return f"Resultados simulados para a busca por '{query}'"

class PDCAContinuousFlow(Flow[PDCAState]):
    """Implementação de um fluxo PDCA contínuo que utiliza ferramentas dinâmicas
    para adaptar-se a cada ciclo e contexto.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o fluxo PDCA contínuo.
        
        Args:
            config: Configurações opcionais para o fluxo
        """
        # Inicializar atributos antes de chamar o construtor da classe pai
        self._current_state = None  # Atributo interno para armazenar o estado
        self.config = config or {}
        self.pdca_flow = PDCAFlow(self.config)
        self.ferramentas_crew = FerramentasCrew()
        self.ferramentas_dinamicas = self._inicializar_ferramentas_dinamicas()
        
        # Chamar o construtor da classe pai após inicializar nossos atributos
        super().__init__()
    
    def _inicializar_ferramentas_dinamicas(self) -> Dict[str, Any]:
        """
        Inicializa as ferramentas dinâmicas que serão utilizadas pelo fluxo.
        
        Returns:
            Dicionário com as ferramentas dinâmicas inicializadas
        """
        return {
            "agent_creator": AgentYAMLConfigWriter(),
            "task_creator": TaskYAMLConfigWriter(),
            "crew_creator": DynamicCrewCreator(),
            "tool_creator": DynamicToolCreator(),
            "directory_search": SimpleDirectorySearchTool()
        }
    
    @property
    def state(self) -> Optional[PDCAState]:
        """Getter para o estado atual do fluxo"""
        return self._current_state
        
    def set_state(self, new_state: PDCAState) -> None:
        """
        Método para atualizar o estado atual do fluxo.
        
        Args:
            new_state: Novo estado a ser definido
        """
        self._current_state = new_state
    
    @start()
    def iniciar_ciclo_pdca(self) -> PDCAState:
        """
        Inicia um novo ciclo PDCA com os dados fornecidos.
        
        Returns:
            Estado inicial do ciclo PDCA
        """
        logger.info("Iniciando ciclo PDCA contínuo")
        
        # No Flow do CrewAI, os dados iniciais são passados diretamente para o método kickoff
        # e são acessíveis através do atributo state
        if hasattr(self, 'state') and self.state:
            dados_iniciais = self.state
        else:
            # Caso não haja estado, criar um estado padrão
            logger.warning("Nenhum dado inicial fornecido, usando valores padrão")
            dados_iniciais = {
                "nome_ciclo": "Ciclo PDCA Padrão",
                "descricao": "Ciclo PDCA iniciado sem dados específicos",
                "problema": "Problema não especificado",
                "objetivo": "Objetivo não especificado",
                "contexto": "Contexto não especificado",
                "definicao_problema": "Problema não especificado"
            }
        
        # Garantir que definicao_problema esteja presente nos dados iniciais
        if isinstance(dados_iniciais, dict) and "definicao_problema" not in dados_iniciais:
            # Se não existir definicao_problema, mas existir problema, usar o valor de problema
            if "problema" in dados_iniciais:
                dados_iniciais["definicao_problema"] = dados_iniciais["problema"]
            else:
                dados_iniciais["definicao_problema"] = "Problema não especificado"
        
        # Criar estado inicial
        if not isinstance(dados_iniciais, PDCAState):
            state = PDCAState(**dados_iniciais)
        else:
            state = dados_iniciais
            # Garantir que definicao_problema esteja presente no PDCAState
            if not hasattr(state, "definicao_problema"):
                setattr(state, "definicao_problema", getattr(state, "problema", "Problema não especificado"))
        
        # Inicializar o ciclo usando o PDCAFlow
        state = self.pdca_flow.iniciar_ciclo(state)
        
        # Armazenar o estado no estado do fluxo usando o método set_state
        self.set_state(state)
        
        return state
    
    @listen(iniciar_ciclo_pdca)
    def fase_planejar(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de planejamento do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado após a fase de planejamento
        """
        logger.info(f"Executando fase PLANEJAR para o ciclo {state.ciclo_id}")
        
        # Gerar ferramentas específicas para a fase de planejamento
        self.gerar_ferramentas_especificas("planejar", state)
        
        # Executar a fase Planejar usando o método da classe PDCAFlow
        state = self.pdca_flow.fase_planejar(state)
        
        # Atualizar o estado do fluxo usando o método set_state
        self.set_state(state)
        
        return state
    
    @listen(fase_planejar)
    def fase_fazer(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de execução do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado após a fase de execução
        """
        logger.info(f"Executando fase FAZER para o ciclo {state.ciclo_id}")
        
        # Gerar ferramentas específicas para a fase de execução
        self.gerar_ferramentas_especificas("fazer", state)
        
        # Executar a fase Fazer usando o método da classe PDCAFlow
        state = self.pdca_flow.fase_fazer(state)
        
        # Atualizar o estado do fluxo usando o método set_state
        self.set_state(state)
        
        return state
    
    @listen(fase_fazer)
    def fase_verificar(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de verificação do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado após a fase de verificação
        """
        logger.info(f"Executando fase VERIFICAR para o ciclo {state.ciclo_id}")
        
        # Gerar ferramentas específicas para a fase de verificação
        self.gerar_ferramentas_especificas("verificar", state)
        
        # Executar a fase Verificar usando o método da classe PDCAFlow
        state = self.pdca_flow.fase_verificar(state)
        
        # Atualizar o estado do fluxo usando o método set_state
        self.set_state(state)
        
        return state
    
    @listen(fase_verificar)
    def fase_agir(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de ação do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado após a fase de ação
        """
        logger.info(f"Executando fase AGIR para o ciclo {state.ciclo_id}")
        
        # Gerar ferramentas específicas para a fase de ação
        self.gerar_ferramentas_especificas("agir", state)
        
        # Executar a fase Agir usando o método da classe PDCAFlow
        state = self.pdca_flow.fase_agir(state)
        
        # Adaptar a equipe baseado nos resultados se o ciclo foi concluído
        if state.status == PDCAStatus.CONCLUIDO:
            state = self.adaptar_equipe_baseado_em_resultados(state)
        
        # Atualizar o estado do fluxo usando o método set_state
        self.set_state(state)
        
        return state
    
    def gerar_ferramentas_especificas(self, fase: str, state: PDCAState) -> List[Any]:
        """
        Gera ferramentas específicas para uma determinada fase do ciclo PDCA.
        
        Args:
            fase: Nome da fase (planejar, fazer, verificar, agir)
            state: Estado atual do ciclo
            
        Returns:
            Lista de ferramentas geradas
        """
        logger.info(f"Gerando ferramentas específicas para a fase {fase}")
        
        # Extrair informações relevantes do estado atual
        problema = state.problema
        contexto = state.contexto
        
        # Definir requisitos específicos com base na fase e no estado atual
        requisitos = {
            "fase_pdca": fase,
            "objetivo": state.objetivo,
            "restricoes": state.restricoes if hasattr(state, 'restricoes') else [],
            "recursos": state.recursos if hasattr(state, 'recursos') else []
        }
        
        # Adicionar informações específicas de cada fase
        if fase == "planejar":
            requisitos["tipo_ferramentas"] = ["análise de causa raiz", "estabelecimento de metas"]
            requisitos["complexidade"] = "alta"
            
        elif fase == "fazer":
            requisitos["tipo_ferramentas"] = ["execução de tarefas", "monitoramento de progresso"]
            requisitos["complexidade"] = "média"
            if hasattr(state, 'plano_acao') and state.plano_acao:
                requisitos["plano_acao"] = state.plano_acao.dict()
                
        elif fase == "verificar":
            requisitos["tipo_ferramentas"] = ["análise de resultados", "identificação de desvios"]
            requisitos["complexidade"] = "alta"
            if hasattr(state, 'plano_acao') and state.plano_acao:
                requisitos["metricas"] = state.plano_acao.metricas
            if hasattr(state, 'resultado_execucao') and state.resultado_execucao:
                requisitos["dados_coletados"] = state.resultado_execucao.dados_coletados
                
        elif fase == "agir":
            requisitos["tipo_ferramentas"] = ["padronização de processos", "planejamento de melhorias"]
            requisitos["complexidade"] = "média"
            if hasattr(state, 'resultado_verificacao') and state.resultado_verificacao:
                requisitos["desvios"] = state.resultado_verificacao.desvios_identificados
                requisitos["sucessos"] = state.resultado_verificacao.sucessos_identificados
        
        # Usar a FerramentasCrew para gerar as ferramentas
        try:
            inputs = {
                "problema": problema,
                "contexto": contexto,
                "fase_pdca": fase,
                "requisitos": requisitos
            }
            ferramentas_geradas = self.ferramentas_crew.crew().kickoff(inputs=inputs)
            
            logger.info(f"Ferramentas geradas com sucesso para a fase {fase}")
            return ferramentas_geradas
            
        except Exception as e:
            logger.error(f"Erro ao gerar ferramentas para a fase {fase}: {e}")
            
            # Fallback para o método antigo de geração de ferramentas
            logger.info(f"Usando método alternativo para gerar ferramentas para a fase {fase}")
            
            # Exemplo simplificado (código original mantido como fallback)
            ferramentas = []
            
            if fase == "planejar":
                # Gerar ferramenta para análise de causa raiz
                ferramenta_causa_raiz = self.ferramentas_dinamicas["tool_creator"]._run(
                    name="AnaliseCausaRaiz",
                    description="Ferramenta para análise de causa raiz do problema",
                    parameters=[
                        ToolParameter(name="problema", type="string", description="Descrição do problema"),
                        ToolParameter(name="contexto", type="string", description="Contexto do problema")
                    ],
                    implementation="""
                        # Implementação simplificada para análise de causa raiz
                        logger.info(f"Analisando causas raiz para o problema: {problema}")
                        return {
                            "causas_identificadas": ["Causa 1", "Causa 2", "Causa 3"],
                            "recomendacoes": ["Recomendação 1", "Recomendação 2"]
                        }
                    """
                )
                ferramentas.append(ferramenta_causa_raiz)
                
            elif fase == "fazer":
                # Gerar ferramenta para execução de tarefas
                ferramenta_execucao = self.ferramentas_dinamicas["tool_creator"]._run(
                    name="ExecutarTarefa",
                    description="Ferramenta para execução de tarefas do plano de ação",
                    parameters=[
                        ToolParameter(name="tarefa", type="string", description="Descrição da tarefa"),
                        ToolParameter(name="responsavel", type="string", description="Responsável pela tarefa")
                    ],
                    implementation="""
                        # Implementação simplificada para execução de tarefas
                        logger.info(f"Executando tarefa: {tarefa} (Responsável: {responsavel})")
                        return {
                            "status": "concluido",
                            "observacoes": "Tarefa executada com sucesso"
                        }
                    """
                )
                ferramentas.append(ferramenta_execucao)
                
            elif fase == "verificar":
                # Gerar ferramenta para análise de resultados
                ferramenta_analise = self.ferramentas_dinamicas["tool_creator"]._run(
                    name="AnalisarResultados",
                    description="Ferramenta para análise dos resultados obtidos",
                    parameters=[
                        ToolParameter(name="dados", type="object", description="Dados coletados"),
                        ToolParameter(name="metricas", type="array", description="Métricas para avaliação")
                    ],
                    implementation="""
                        # Implementação simplificada para análise de resultados
                        logger.info(f"Analisando resultados com {len(metricas)} métricas")
                        return {
                            "analise": "Análise dos resultados concluída",
                            "desvios": ["Desvio 1", "Desvio 2"],
                            "sucessos": ["Sucesso 1", "Sucesso 2"]
                        }
                    """
                )
                ferramentas.append(ferramenta_analise)
                
            elif fase == "agir":
                # Gerar ferramenta para padronização
                ferramenta_padronizacao = self.ferramentas_dinamicas["tool_creator"]._run(
                    name="PadronizarProcesso",
                    description="Ferramenta para padronização de processos",
                    parameters=[
                        ToolParameter(name="processo", type="string", description="Processo a ser padronizado"),
                        ToolParameter(name="melhorias", type="array", description="Melhorias a serem implementadas")
                    ],
                    implementation="""
                        # Implementação simplificada para padronização de processos
                        logger.info(f"Padronizando processo: {processo} com {len(melhorias)} melhorias")
                        return {
                            "processo_padronizado": processo,
                            "melhorias_implementadas": melhorias,
                            "status": "concluido"
                        }
                    """
                )
                ferramentas.append(ferramenta_padronizacao)
            
            return ferramentas
    
    def adaptar_equipe_baseado_em_resultados(self, state: PDCAState) -> PDCAState:
        """
        Adapta a equipe baseado nos resultados do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado com a equipe adaptada
        """
        logger.info(f"Adaptando equipe baseado nos resultados do ciclo {state.ciclo_id}")
        
        # Aqui seria implementada a lógica para adaptar a equipe baseada
        # nos resultados do ciclo, como adicionar novos agentes ou modificar
        # os existentes
        
        # Exemplo simplificado
        if hasattr(state, 'resultado_verificacao') and state.resultado_verificacao:
            # Se houver desvios identificados, adicionar um especialista em resolução de problemas
            if hasattr(state.resultado_verificacao, 'desvios_identificados') and state.resultado_verificacao.desvios_identificados:
                logger.info("Desvios identificados, adicionando especialista em resolução de problemas")
                
                # Criar configuração para o novo agente
                config = AgentConfig(
                    name="EspecialistaResolucaoProblemas",
                    role="Especialista em resolução de problemas complexos",
                    goal="Identificar soluções eficazes para os desvios encontrados",
                    backstory="Profissional com vasta experiência em resolver problemas complexos em diversos contextos"
                )
                
                # Criar o agente usando a ferramenta dinâmica
                self.ferramentas_dinamicas["agent_creator"].write_agent_config(config)
                
                # Registrar no estado que a equipe foi adaptada
                if not hasattr(state, 'adaptacoes_equipe'):
                    state.adaptacoes_equipe = []
                
                state.adaptacoes_equipe.append({
                    "timestamp": datetime.now().isoformat(),
                    "tipo": "adicao_agente",
                    "agente": "EspecialistaResolucaoProblemas",
                    "motivo": "Desvios identificados na fase de verificação"
                })
        
        return state
    
    def executar_ciclos_continuos(self, dados_iniciais: Dict[str, Any], max_ciclos: int = 3) -> List[PDCAState]:
        """
        Executa múltiplos ciclos PDCA de forma contínua, cada um baseado nos resultados do anterior.
        
        Args:
            dados_iniciais: Dados iniciais para o primeiro ciclo PDCA
            max_ciclos: Número máximo de ciclos a executar
            
        Returns:
            Lista de estados finais de cada ciclo executado
        """
        ciclos_executados = []
        dados_ciclo_atual = dados_iniciais
        
        for i in range(max_ciclos):
            logger.info(f"Iniciando ciclo PDCA contínuo #{i+1}")
            
            try:
                # Executar um ciclo completo usando o fluxo
                # Antes de chamar kickoff, definimos o estado inicial usando set_state
                # para garantir que o estado esteja disponível para o método iniciar_ciclo_pdca
                if i == 0:  # Apenas para o primeiro ciclo
                    # Para o primeiro ciclo, definimos o estado inicial diretamente
                    if isinstance(dados_ciclo_atual, dict):
                        initial_state = PDCAState(**dados_ciclo_atual)
                        self.set_state(initial_state)
                    else:
                        self.set_state(dados_ciclo_atual)
                
                state_final = self.kickoff(dados_ciclo_atual)
                ciclos_executados.append(state_final)
                
                # Verificar se há recomendações para um novo ciclo
                tem_recomendacoes = (
                    hasattr(state_final, 'acao_corretiva') and 
                    state_final.acao_corretiva is not None and
                    hasattr(state_final.acao_corretiva, 'recomendacoes_proximo_ciclo') and 
                    state_final.acao_corretiva.recomendacoes_proximo_ciclo
                )
                
                if tem_recomendacoes:
                    # Preparar os dados para o próximo ciclo
                    recomendacoes = state_final.acao_corretiva.recomendacoes_proximo_ciclo
                    dados_ciclo_atual = {
                        "nome_ciclo": f"{state_final.nome_ciclo} - Continuação #{i+1}",
                        "descricao": "Continuação do ciclo anterior baseado nas recomendações",
                        "problema": recomendacoes.get('problema_foco', state_final.problema),
                        "definicao_problema": recomendacoes.get('problema_foco', state_final.problema),
                        "contexto": f"Ciclo anterior: {state_final.ciclo_id}\n\n{recomendacoes.get('contexto_atualizado', '')}",
                        "objetivo": recomendacoes.get('objetivo_atualizado', state_final.objetivo),
                        "ciclo_anterior_id": state_final.ciclo_id
                    }
                    
                    # Adicionar restrições e recursos se disponíveis
                    if 'restricoes_atualizadas' in recomendacoes:
                        dados_ciclo_atual["restricoes"] = recomendacoes['restricoes_atualizadas']
                    else:
                        dados_ciclo_atual["restricoes"] = state_final.restricoes if hasattr(state_final, 'restricoes') else []
                    
                    if 'recursos_atualizados' in recomendacoes:
                        dados_ciclo_atual["recursos"] = recomendacoes['recursos_atualizados']
                    else:
                        dados_ciclo_atual["recursos"] = state_final.recursos if hasattr(state_final, 'recursos') else []
                else:
                    # Se não há recomendações específicas, usar o mesmo estado com ajustes mínimos
                    dados_ciclo_atual = {
                        "nome_ciclo": f"{state_final.nome_ciclo} - Continuação #{i+1}",
                        "descricao": "Continuação do ciclo anterior para aprofundar melhorias",
                        "problema": state_final.problema,
                        "definicao_problema": state_final.problema,
                        "contexto": f"Ciclo anterior: {state_final.ciclo_id}\n\n{state_final.contexto}",
                        "objetivo": state_final.objetivo,
                        "restricoes": state_final.restricoes if hasattr(state_final, 'restricoes') else [],
                        "recursos": state_final.recursos if hasattr(state_final, 'recursos') else [],
                        "ciclo_anterior_id": state_final.ciclo_id
                    }
                
                # Preparar o estado para o próximo ciclo
                if i < max_ciclos - 1:  # Se não for o último ciclo
                    next_state = PDCAState(**dados_ciclo_atual)
                    self.set_state(next_state)
            except Exception as e:
                logger.error(f"Erro durante a execução dos ciclos PDCA contínuos: {e}")
                import traceback
                logger.error(traceback.format_exc())
                break
        
        return ciclos_executados


def criar_pdca_continuous_flow(config: Optional[Dict[str, Any]] = None) -> PDCAContinuousFlow:
    """
    Função auxiliar para criar uma instância do PDCAContinuousFlow.
    
    Args:
        config: Configurações opcionais para o fluxo
        
    Returns:
        Instância do PDCAContinuousFlow
    """
    return PDCAContinuousFlow(config)


if __name__ == "__main__":
    """
    Exemplo de uso do PDCAContinuousFlow para um caso real de construção civil.
    Este exemplo demonstra como iniciar um ciclo PDCA para resolver um problema
    de qualidade do concreto em uma obra.
    """
    print("\n" + "=" * 80)
    print("INICIANDO CICLO PDCA CONTÍNUO PARA CONSTRUÇÃO CIVIL")
    print("=" * 80)
    
    # Definir dados iniciais para o problema de qualidade do concreto
    dados_iniciais = {
        "nome_ciclo": "Melhoria da Qualidade do Concreto",
        "descricao": "Ciclo PDCA para resolver problemas de qualidade do concreto na obra do Edifício Residencial Jardim das Flores",
        "problema": "O concreto utilizado na construção apresenta resistência abaixo do especificado em projeto, causando atrasos e retrabalho",
        "objetivo": "Aumentar a resistência do concreto para atender às especificações do projeto em 100% das amostras em 30 dias",
        "contexto": """
            A obra do Edifício Residencial Jardim das Flores está na fase de estrutura do 5º pavimento.
            Nos últimos 3 pavimentos, os testes de resistência do concreto mostraram valores 15% abaixo
            do especificado em projeto. Isso tem causado atrasos no cronograma e custos adicionais com
            reforços estruturais. A concreteira é a mesma desde o início da obra, mas houve mudança
            recente no fornecedor de cimento.
        """,
        "definicao_problema": """
            Problema de qualidade do concreto:
            - Resistência à compressão 15% abaixo do especificado (25 MPa vs 30 MPa exigidos)
            - Afeta 60% das amostras coletadas nos últimos 3 pavimentos
            - Impacto: atraso de 15 dias no cronograma e custo adicional de R$ 120.000,00 em reforços
        """,
        "restricoes": [
            "Não é possível trocar de concreteira devido a contrato vigente",
            "O cronograma não pode atrasar mais de 7 dias adicionais",
            "Orçamento limitado a R$ 50.000,00 para resolução do problema"
        ],
        "prazo": "30 dias",
        "recursos": [
            "Equipe técnica de 3 engenheiros",
            "Laboratório para testes de concreto",
            "Acesso aos registros de qualidade da concreteira",
            "Consultoria especializada em tecnologia do concreto"
        ],
        # Adicionando análise de contexto para evitar erro de variável faltante
        "analise_contexto": """
            Análise do contexto atual:
            - A obra está na fase de estrutura do 5º pavimento de um total de 15
            - O problema começou a ser detectado a partir do 3º pavimento
            - Houve mudança no fornecedor de cimento da concreteira há 2 meses
            - As condições climáticas têm sido estáveis (sem chuvas excessivas)
            - O processo de cura do concreto segue o padrão da construtora
            - Os testes de qualidade são realizados por laboratório certificado
            - A equipe de obra não sofreu alterações significativas
        """
    }
    
    print("\nDADOS INICIAIS DO CICLO PDCA:")
    for chave, valor in dados_iniciais.items():
        if isinstance(valor, list):
            print(f"  {chave}:")
            for item in valor:
                print(f"    - {item}")
        elif chave in ["contexto", "definicao_problema", "analise_contexto"]:
            print(f"  {chave}: [Texto longo]")
        else:
            print(f"  {chave}: {valor}")
    
    # Criar e executar o fluxo PDCA contínuo
    try:
        # Criar instância do PDCAContinuousFlow
        pdca_flow = criar_pdca_continuous_flow()
        
        # Executar ciclos PDCA contínuos (máximo de 3 ciclos)
        ciclos_executados = pdca_flow.executar_ciclos_continuos(dados_iniciais, max_ciclos=3)
        
        # Exibir resumo dos ciclos executados
        print("\n" + "=" * 80)
        print("RESUMO DOS CICLOS EXECUTADOS")
        print("=" * 80)
        
        for i, ciclo in enumerate(ciclos_executados):
            print(f"\nCICLO #{i+1} - ID: {ciclo.ciclo_id}")
            print(f"Status: {ciclo.status}")
            print(f"Fase final: {ciclo.fase_atual}")
            
            # Mostrar recomendações para o próximo ciclo, se houver
            if hasattr(ciclo, 'acao_corretiva') and ciclo.acao_corretiva and hasattr(ciclo.acao_corretiva, 'recomendacoes_proximo_ciclo'):
                print("\nRecomendações para o próximo ciclo:")
                for chave, valor in ciclo.acao_corretiva.recomendacoes_proximo_ciclo.items():
                    if isinstance(valor, list):
                        print(f"  {chave}:")
                        for item in valor:
                            print(f"    - {item}")
                    else:
                        print(f"  {chave}: {valor}")
        
        print("\n" + "=" * 80)
        print("CICLO PDCA CONTÍNUO PARA CONSTRUÇÃO CIVIL CONCLUÍDO COM SUCESSO")
        print("=" * 80)
        
    except Exception as e:
        print(f"ERRO: {str(e)}")
        import traceback
        print(traceback.format_exc())
