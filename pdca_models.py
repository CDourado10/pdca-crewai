#!/usr/bin/env python
"""
Modelos de dados para o ciclo PDCA

Este módulo define os modelos de dados utilizados no ciclo PDCA,
incluindo estruturas para planos de ação, resultados de execução,
resultados de verificação e ações corretivas.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PDCAFase(str, Enum):
    """Fases do ciclo PDCA"""
    PLANEJAR = "planejar"
    FAZER = "fazer"
    VERIFICAR = "verificar"
    AGIR = "agir"
    CONCLUIDO = "concluido"


class PDCAStatus(str, Enum):
    """Status possíveis do ciclo PDCA"""
    NAO_INICIADO = "nao_iniciado"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    ERRO = "erro"
    PAUSADO = "pausado"


# Modelos de dados para o estado do PDCA
class PlanoAcao(BaseModel):
    """Modelo para o plano de ação gerado na fase de planejamento"""
    objetivos: List[str] = Field(default_factory=list)
    atividades: List[Dict[str, Any]] = Field(default_factory=list)
    cronograma: Dict[str, Any] = Field(default_factory=dict)
    recursos_necessarios: List[str] = Field(default_factory=list)
    responsaveis: Dict[str, List[str]] = Field(default_factory=dict)
    metricas: List[Dict[str, Any]] = Field(default_factory=list)
    
class ResultadoExecucao(BaseModel):
    """Modelo para os resultados da fase de execução"""
    atividades_concluidas: List[str] = Field(default_factory=list)
    dados_coletados: Dict[str, Any] = Field(default_factory=dict)
    obstaculos_encontrados: List[str] = Field(default_factory=list)
    ajustes_realizados: List[Dict[str, Any]] = Field(default_factory=list)
    documentacao: str = ""
    
class ResultadoVerificacao(BaseModel):
    """Modelo para os resultados da fase de verificação"""
    metricas_analisadas: Dict[str, Any] = Field(default_factory=dict)
    desvios_identificados: List[Dict[str, Any]] = Field(default_factory=list)
    causas_desvios: Dict[str, List[str]] = Field(default_factory=dict)
    sucessos_identificados: List[str] = Field(default_factory=list)
    relatorio: str = ""
    
class AcaoCorretiva(BaseModel):
    """Modelo para as ações corretivas da fase de agir"""
    solucoes_propostas: List[Dict[str, Any]] = Field(default_factory=list)
    padronizacoes: List[Dict[str, Any]] = Field(default_factory=list)
    acoes_corretivas: List[Dict[str, Any]] = Field(default_factory=list)
    licoes_aprendidas: List[str] = Field(default_factory=list)
    recomendacoes_proximo_ciclo: Dict[str, Any] = Field(default_factory=dict)

class PDCAState(BaseModel):
    """Modelo para o estado completo do ciclo PDCA"""
    ciclo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome_ciclo: str = ""
    descricao: str = ""
    data_inicio: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_atualizacao: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_conclusao: Optional[str] = None
    status: PDCAStatus = PDCAStatus.NAO_INICIADO
    fase_atual: PDCAFase = PDCAFase.PLANEJAR
    problema: str = ""
    contexto: str = ""
    objetivo: str = ""
    definicao_problema: str = ""
    restricoes: List[str] = Field(default_factory=list)
    prazo: str = ""
    recursos: List[str] = Field(default_factory=list)
    analise_contexto: Optional[str] = None
    plano_acao: Optional[PlanoAcao] = None
    resultado_execucao: Optional[ResultadoExecucao] = None
    resultado_verificacao: Optional[ResultadoVerificacao] = None
    acao_corretiva: Optional[AcaoCorretiva] = None
    fingerprints: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    historico: List[Dict[str, Any]] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    
    def registrar_evento(self, evento: str, detalhes: Optional[Dict[str, Any]] = None):
        """Registra um evento no histórico do ciclo"""
        self.historico.append({
            "evento": evento,
            "timestamp": datetime.now().isoformat(),
            "detalhes": detalhes or {}
        })
        self.data_atualizacao = datetime.now().isoformat()

class FerramentaOutput(BaseModel):
    """Modelo Pydantic para a saída da equipe de ferramentas inteligentes"""
    decisao: str = Field(..., description="Decisão tomada: usar_existente, adaptar ou criar_nova")
    ferramenta: Dict[str, Any] = Field(..., description="Detalhes da ferramenta a ser utilizada")
    justificativa: str = Field(..., description="Justificativa para a decisão tomada")
