#!/usr/bin/env python
"""
PDCA Flow - Implementação do ciclo PDCA usando CrewAI Flows

Este módulo implementa uma versão robusta, escalável e flexível do ciclo PDCA
(Plan-Do-Check-Act) utilizando a arquitetura de Flows do CrewAI.

O fluxo PDCA é estruturado para permitir:
- Gerenciamento de estado entre as diferentes fases
- Transições condicionais entre etapas
- Rastreabilidade completa através de fingerprinting
- Persistência de estado para retomada de ciclos
- Execução assíncrona de tarefas quando apropriado
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from crewai.flow.flow import Flow, start, listen
from crews.pdca.pdca_models import (
    PDCAFase, PDCAStatus, PDCAState
)
from crews.pdca.planejar.planejar_crew import PlanejarCrew
from crews.pdca.fazer.fazer_crew import FazerCrew
from crews.pdca.verificar.verificar_crew import VerificarCrew
from crews.pdca.agir.agir_crew import AgirCrew

# Adicionar diretório raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(project_root)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"pdca_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Definir constantes
STORAGE_DIR = Path("./pdca_storage")
STORAGE_DIR.mkdir(exist_ok=True)

def sanitizar_input(input_data: Any) -> Any:
    """
    Sanitiza os inputs para remover caracteres especiais problemáticos.
    
    Args:
        input_data: Dados de entrada a serem sanitizados
        
    Returns:
        Dados sanitizados
    """
    if isinstance(input_data, str):
        # Substituir caracteres problemáticos
        sanitized = input_data
        sanitized = sanitized.replace("%", " por cento ")
        sanitized = sanitized.replace("{", " ")
        sanitized = sanitized.replace("}", " ")
        sanitized = sanitized.replace("(", " ")
        sanitized = sanitized.replace(")", " ")
        sanitized = sanitized.replace("/", "-")
        sanitized = sanitized.replace("\\", "-")
        sanitized = sanitized.replace("\"\"\"", "")
        sanitized = sanitized.replace("'", "")
        return sanitized
    elif isinstance(input_data, dict):
        # Sanitizar cada valor no dicionário
        return {k: sanitizar_input(v) for k, v in input_data.items()}
    elif isinstance(input_data, list):
        # Sanitizar cada item na lista
        return [sanitizar_input(item) for item in input_data]
    else:
        # Retornar outros tipos sem alteração
        return input_data

class PDCAFlow(Flow[PDCAState]):
    """
    Implementação do ciclo PDCA usando a arquitetura de Flows do CrewAI.
    
    Esta classe implementa um fluxo de trabalho completo para o ciclo PDCA,
    permitindo a execução estruturada e flexível de cada fase, com gerenciamento
    de estado, persistência, e rastreabilidade.
    """
    state_class = PDCAState
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o fluxo PDCA.
        
        Args:
            config: Configurações opcionais para o fluxo
        """
        super().__init__()
        self.config = config or {}
        logger.info("PDCAFlow inicializado")
        
    def salvar_estado(self, state: PDCAState):
        """
        Salva o estado atual do fluxo em um arquivo JSON.
        
        Args:
            state: O estado atual do fluxo
        """
        state_path = STORAGE_DIR / f"pdca_state_{state.ciclo_id}.json"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state.dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Estado do ciclo {state.ciclo_id} salvo em {state_path}")
        
    def carregar_estado(self, ciclo_id: str) -> Optional[PDCAState]:
        """
        Carrega o estado de um ciclo a partir de um arquivo JSON.
        
        Args:
            ciclo_id: ID do ciclo a ser carregado
            
        Returns:
            O estado do ciclo, ou None se não encontrado
        """
        state_path = STORAGE_DIR / f"pdca_state_{ciclo_id}.json"
        if not state_path.exists():
            logger.warning(f"Estado do ciclo {ciclo_id} não encontrado")
            return None
            
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state_dict = json.load(f)
            state = PDCAState(**state_dict)
            logger.info(f"Estado do ciclo {ciclo_id} carregado com sucesso")
            return state
        except Exception as e:
            logger.error(f"Erro ao carregar estado do ciclo {ciclo_id}: {e}")
            return None
            
    @start()
    def iniciar_ciclo(self, state: PDCAState) -> PDCAState:
        """
        Ponto de entrada do fluxo PDCA. Inicializa o ciclo e prepara o estado.
        
        Args:
            state: Estado inicial do ciclo
            
        Returns:
            Estado atualizado
        """
        logger.info(f"Iniciando ciclo PDCA {state.ciclo_id}")
        
        # Atualizar status e registrar evento
        state.status = PDCAStatus.EM_ANDAMENTO
        state.fase_atual = PDCAFase.PLANEJAR
        state.registrar_evento("ciclo_iniciado")
        
        # Salvar estado inicial
        self.salvar_estado(state)
        
        return state
        
    @listen(iniciar_ciclo)
    def fase_planejar(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de planejamento (Plan) do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado com os resultados do planejamento
        """
        logger.info(f"Executando fase PLANEJAR do ciclo {state.ciclo_id}")
        
        # Registrar evento de início da fase
        state.registrar_evento("fase_planejar_iniciada")
        
        try:
            # Criar e configurar a equipe de planejamento
            planejar_crew = PlanejarCrew()
            
            # Preparar dados de entrada para a equipe
            input_data = {
                "problema": sanitizar_input(state.problema),
                "contexto": sanitizar_input(state.contexto),
                "objetivo": sanitizar_input(state.objetivo),
                "restricoes": sanitizar_input(state.restricoes),
                "prazo": sanitizar_input(state.prazo),
                "recursos": sanitizar_input(state.recursos),
                "definicao_problema": sanitizar_input(state.definicao_problema)
            }
            
            # Adicionar analise_contexto se existir no estado
            if hasattr(state, "analise_contexto"):
                input_data["analise_contexto"] = sanitizar_input(state.analise_contexto)
            
            # Adicionar variáveis de template necessárias para evitar erros
            # Estas são variáveis que serão preenchidas durante a execução das tarefas
            # mas são necessárias como placeholders iniciais
            input_data.update({
                "causas_identificadas": "Serão identificadas durante a análise",
                "metas_estabelecidas": "Serão estabelecidas durante o planejamento",
                "plano_acao": "Será desenvolvido durante o planejamento",
                "analise_contexto": input_data.get("analise_contexto", "Será desenvolvida durante a análise")
            })
            
            # Executar a equipe de planejamento
            resultado = planejar_crew.crew().kickoff(inputs=input_data)
            
            # Registrar informações sobre a execução para rastreabilidade
            state.fingerprints["planejar"] = {
                "timestamp": datetime.now().isoformat(),
                "metadata": {"status": "concluído"}
            }
            
            # Atualizar o estado com o plano de ação
            # Como configuramos output_pydantic=PlanoAcao na task, o resultado já é um objeto PlanoAcao validado
            state.plano_acao = resultado.pydantic
            
            # Registrar evento de conclusão da fase
            state.registrar_evento("fase_planejar_concluida", {"plano_acao": state.plano_acao.dict()})
            
            # Atualizar fase atual
            state.fase_atual = PDCAFase.FAZER
            
            # Salvar estado
            self.salvar_estado(state)
            
            return state
            
        except Exception as e:
            # Registrar erro
            logger.error(f"Erro na fase PLANEJAR: {e}")
            state.registrar_evento("erro_fase_planejar", {"erro": str(e)})
            state.status = PDCAStatus.ERRO
            self.salvar_estado(state)
            raise
            
    @listen(fase_planejar)
    def fase_fazer(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de execução (Do) do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado com os resultados da execução
        """
        logger.info(f"Executando fase FAZER do ciclo {state.ciclo_id}")
        
        # Registrar evento de início da fase
        state.registrar_evento("fase_fazer_iniciada")
        
        try:
            # Verificar se existe um plano de ação
            if not state.plano_acao:
                raise ValueError("Não é possível executar a fase FAZER sem um plano de ação")
            
            # Criar e configurar a equipe de execução
            fazer_crew = FazerCrew()
            
            # Preparar dados de entrada para a equipe
            input_data = {
                "plano_acao": sanitizar_input(state.plano_acao.dict()),
                "contexto": sanitizar_input(state.contexto),
                "recursos": sanitizar_input(state.recursos)
            }
            
            # Executar a equipe de execução
            resultado = fazer_crew.crew().kickoff(inputs=input_data)
            
            # Registrar informações sobre a execução para rastreabilidade
            state.fingerprints["fazer"] = {
                "timestamp": datetime.now().isoformat(),
                "metadata": {"status": "concluído"}
            }
            
            # Atualizar o estado com o resultado da execução
            state.resultado_execucao = resultado.pydantic
            
            # Registrar evento de conclusão da fase
            state.registrar_evento("fase_fazer_concluida", {"resultado_execucao": state.resultado_execucao.dict()})
            
            # Atualizar fase atual
            state.fase_atual = PDCAFase.VERIFICAR
            
            # Salvar estado
            self.salvar_estado(state)
            
            return state
            
        except Exception as e:
            # Registrar erro
            logger.error(f"Erro na fase FAZER: {e}")
            state.registrar_evento("erro_fase_fazer", {"erro": str(e)})
            state.status = PDCAStatus.ERRO
            self.salvar_estado(state)
            raise
            
    @listen(fase_fazer)
    def fase_verificar(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de verificação (Check) do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado com os resultados da verificação
        """
        logger.info(f"Executando fase VERIFICAR do ciclo {state.ciclo_id}")
        
        # Registrar evento de início da fase
        state.registrar_evento("fase_verificar_iniciada")
        
        try:
            # Verificar se existem resultados de execução
            if not state.resultado_execucao:
                raise ValueError("Não é possível executar a fase VERIFICAR sem resultados de execução")
                
            # Verificar se existe um plano de ação
            if not state.plano_acao:
                raise ValueError("Não é possível executar a fase VERIFICAR sem um plano de ação")
            
            # Criar e configurar a equipe de verificação
            verificar_crew = VerificarCrew()
            
            # Preparar dados de entrada para a equipe
            input_data = {
                "plano_acao": sanitizar_input(state.plano_acao.dict()),
                "resultado_execucao": sanitizar_input(state.resultado_execucao.dict()),
                "objetivo": sanitizar_input(state.objetivo),
                "metricas": sanitizar_input(state.plano_acao.metricas)
            }
            
            # Executar a equipe de verificação
            resultado = verificar_crew.crew().kickoff(inputs=input_data)
            
            # Registrar informações sobre a execução para rastreabilidade
            state.fingerprints["verificar"] = {
                "timestamp": datetime.now().isoformat(),
                "metadata": {"status": "concluído"}
            }
            
            # Atualizar o estado com o resultado da verificação
            state.resultado_verificacao = resultado.pydantic
            
            # Registrar evento de conclusão da fase
            state.registrar_evento("fase_verificar_concluida", {"resultado_verificacao": state.resultado_verificacao.dict()})
            
            # Atualizar fase atual
            state.fase_atual = PDCAFase.AGIR
            
            # Salvar estado
            self.salvar_estado(state)
            
            return state
            
        except Exception as e:
            # Registrar erro
            logger.error(f"Erro na fase VERIFICAR: {e}")
            state.registrar_evento("erro_fase_verificar", {"erro": str(e)})
            state.status = PDCAStatus.ERRO
            self.salvar_estado(state)
            raise
            
    @listen(fase_verificar)
    def fase_agir(self, state: PDCAState) -> PDCAState:
        """
        Executa a fase de ação (Act) do ciclo PDCA.
        
        Args:
            state: Estado atual do ciclo
            
        Returns:
            Estado atualizado com os resultados da ação corretiva
        """
        logger.info(f"Executando fase AGIR do ciclo {state.ciclo_id}")
        
        # Registrar evento de início da fase
        state.registrar_evento("fase_agir_iniciada")
        
        try:
            # Verificar se existem resultados de verificação
            if not state.resultado_verificacao:
                raise ValueError("Não é possível executar a fase AGIR sem resultados de verificação")
                
            # Verificar se existem resultados de execução
            if not state.resultado_execucao:
                raise ValueError("Não é possível executar a fase AGIR sem resultados de execução")
                
            # Verificar se existe um plano de ação
            if not state.plano_acao:
                raise ValueError("Não é possível executar a fase AGIR sem um plano de ação")
            
            # Criar e configurar a equipe de ação
            agir_crew = AgirCrew()
            
            # Preparar dados de entrada para a equipe
            input_data = {
                "plano_acao": sanitizar_input(state.plano_acao.dict()),
                "resultado_execucao": sanitizar_input(state.resultado_execucao.dict()),
                "resultado_verificacao": sanitizar_input(state.resultado_verificacao.dict()),
                "objetivo": sanitizar_input(state.objetivo),
                "problema": sanitizar_input(state.problema)
            }
            
            # Executar a equipe de ação
            resultado = agir_crew.crew().kickoff(inputs=input_data)
            
            # Registrar informações sobre a execução para rastreabilidade
            state.fingerprints["agir"] = {
                "timestamp": datetime.now().isoformat(),
                "metadata": {"status": "concluído"}
            }
            
            # Atualizar o estado com o resultado da ação corretiva
            state.acao_corretiva = resultado.pydantic
            
            # Registrar evento de conclusão da fase
            state.registrar_evento("fase_agir_concluida", {"acao_corretiva": state.acao_corretiva.dict()})
            
            # Atualizar fase atual e status
            state.fase_atual = PDCAFase.CONCLUIDO
            state.status = PDCAStatus.CONCLUIDO
            state.data_conclusao = datetime.now().isoformat()
            
            # Salvar estado
            self.salvar_estado(state)
            
            return state
            
        except Exception as e:
            # Registrar erro
            logger.error(f"Erro na fase AGIR: {e}")
            state.registrar_evento("erro_fase_agir", {"erro": str(e)})
            state.status = PDCAStatus.ERRO
            self.salvar_estado(state)
            raise
            
    def executar_ciclo_completo(self, dados_iniciais: Dict[str, Any]) -> PDCAState:
        """
        Executa um ciclo PDCA completo de forma sequencial.
        
        Args:
            dados_iniciais: Dados iniciais para o ciclo PDCA
            
        Returns:
            Estado final do ciclo
        """
        logger.info("Iniciando execução sequencial do ciclo PDCA completo")
        
        # Criar estado inicial
        state = PDCAState(
            nome_ciclo=dados_iniciais.get("nome_ciclo", "Ciclo PDCA"),
            descricao=dados_iniciais.get("descricao", ""),
            problema=dados_iniciais.get("problema", ""),
            contexto=dados_iniciais.get("contexto", ""),
            objetivo=dados_iniciais.get("objetivo", ""),
            restricoes=dados_iniciais.get("restricoes", []),
            prazo=dados_iniciais.get("prazo", ""),
            recursos=dados_iniciais.get("recursos", []),
            definicao_problema=dados_iniciais.get("definicao_problema", ""),
            analise_contexto=dados_iniciais.get("analise_contexto", None)
        )
        
        # Executar cada fase do ciclo
        state = self.iniciar_ciclo(state)
        state = self.fase_planejar(state)
        state = self.fase_fazer(state)
        state = self.fase_verificar(state)
        state = self.fase_agir(state)
        
        logger.info(f"Ciclo PDCA {state.ciclo_id} concluído com sucesso")
        return state
        
    def obter_relatorio_ciclo(self, state: PDCAState) -> Dict[str, Any]:
        """
        Gera um relatório completo do ciclo PDCA.
        
        Args:
            state: Estado do ciclo
            
        Returns:
            Relatório do ciclo
        """
        return {
            "ciclo_id": state.ciclo_id,
            "nome_ciclo": state.nome_ciclo,
            "descricao": state.descricao,
            "data_inicio": state.data_inicio,
            "data_conclusao": state.data_conclusao,
            "status": state.status,
            "problema": state.problema,
            "objetivo": state.objetivo,
            "plano_acao": state.plano_acao.dict() if state.plano_acao else None,
            "resultado_execucao": state.resultado_execucao.dict() if state.resultado_execucao else None,
            "resultado_verificacao": state.resultado_verificacao.dict() if state.resultado_verificacao else None,
            "acao_corretiva": state.acao_corretiva.dict() if state.acao_corretiva else None,
            "eventos": len(state.historico),
            "duracao": (
                datetime.fromisoformat(state.data_conclusao) - datetime.fromisoformat(state.data_inicio)
            ).total_seconds() if state.data_conclusao else None
        }
        
    def reiniciar_ciclo(self, state: PDCAState, fase_inicial: PDCAFase = PDCAFase.PLANEJAR) -> PDCAState:
        """
        Reinicia um ciclo PDCA a partir de uma fase específica.
        
        Args:
            state: Estado do ciclo a ser reiniciado
            fase_inicial: Fase a partir da qual o ciclo será reiniciado
            
        Returns:
            Estado atualizado
        """
        logger.info(f"Reiniciando ciclo PDCA {state.ciclo_id} a partir da fase {fase_inicial}")
        
        # Registrar evento de reinício
        state.registrar_evento("ciclo_reiniciado", {"fase_inicial": fase_inicial})
        
        # Limpar resultados das fases a serem refeitas
        if fase_inicial == PDCAFase.PLANEJAR:
            state.plano_acao = None
            state.resultado_execucao = None
            state.resultado_verificacao = None
            state.acao_corretiva = None
        elif fase_inicial == PDCAFase.FAZER:
            state.resultado_execucao = None
            state.resultado_verificacao = None
            state.acao_corretiva = None
        elif fase_inicial == PDCAFase.VERIFICAR:
            state.resultado_verificacao = None
            state.acao_corretiva = None
        elif fase_inicial == PDCAFase.AGIR:
            state.acao_corretiva = None
            
        # Atualizar status e fase atual
        state.status = PDCAStatus.EM_ANDAMENTO
        state.fase_atual = fase_inicial
        state.data_conclusao = None
        
        # Salvar estado
        self.salvar_estado(state)
        
        return state


def criar_pdca_flow(config: Optional[Dict[str, Any]] = None) -> PDCAFlow:
    """
    Função auxiliar para criar uma instância do PDCAFlow.
    
    Args:
        config: Configurações opcionais para o fluxo
        
    Returns:
        Instância do PDCAFlow
    """
    return PDCAFlow(config)


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Criar uma instância do PDCAFlow
    pdca_flow = criar_pdca_flow()
    
    # Dados iniciais para o ciclo PDCA
    dados_iniciais = {
        "nome_ciclo": "Implementação de CRM",
        "descricao": "Ciclo PDCA para implementação de um sistema CRM para gerenciamento de clientes",
        "problema": "Falta de CRM para gerenciar clientes",
        "contexto": "Construtora de condomínios que vende lotes. Necessita de um CRM para gerenciar clientes, emitir boletos e enviar mensagens via WhatsApp.",
        "objetivo": "CRM de clientes, com emissao de boletos e envios de mensagens via WhatsApp",
        "restricoes": ["Falta de pessoal", "Todo o sistema deve ser criado e gerenciado de forma automatizada"],
        "prazo": "6 meses",
        "recursos": ["Equipe de TI", "Orçamento limitado para aquisição de software"],
        "definicao_problema": "Falta de CRM para gerenciar clientes"
    }
    
    try:
        # Executar o ciclo PDCA completo
        print("Iniciando ciclo PDCA completo...")
        estado_final = pdca_flow.executar_ciclo_completo(dados_iniciais)
        
        # Exibir informações sobre o ciclo concluído
        print("\nCiclo PDCA concluído com sucesso!")
        print(f"ID do ciclo: {estado_final.ciclo_id}")
        print(f"Status final: {estado_final.status}")
        print(f"Fase final: {estado_final.fase_atual}")
        print(f"Data de início: {estado_final.data_inicio}")
        print(f"Data de conclusão: {estado_final.data_conclusao}")
        
        # Exibir resultados de cada fase
        if estado_final.plano_acao:
            print("\nResultados do Planejamento:")
            print(f"Objetivos: {estado_final.plano_acao.objetivos}")
            print(f"Número de atividades: {len(estado_final.plano_acao.atividades)}")
        
        if estado_final.resultado_execucao:
            print("\nResultados da Execução:")
            print(f"Atividades concluídas: {estado_final.resultado_execucao.atividades_concluidas}")
            print(f"Obstáculos encontrados: {estado_final.resultado_execucao.obstaculos_encontrados}")
        
        if estado_final.resultado_verificacao:
            print("\nResultados da Verificação:")
            print(f"Desvios identificados: {estado_final.resultado_verificacao.desvios_identificados}")
            print(f"Sucessos identificados: {estado_final.resultado_verificacao.sucessos_identificados}")
        
        if estado_final.acao_corretiva:
            print("\nResultados da Ação Corretiva:")
            print(f"Soluções propostas: {estado_final.acao_corretiva.solucoes_propostas}")
            print(f"Lições aprendidas: {estado_final.acao_corretiva.licoes_aprendidas}")
        
        # Gerar relatório completo
        print("\nRelatório completo disponível em:")
        print(f"crews/pdca/estados/{estado_final.ciclo_id}.json")
        
    except Exception as e:
        print(f"Erro durante a execução do ciclo PDCA: {e}")
