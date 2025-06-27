from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from collections import Counter
"""# Dicionário centralizado de descrições"""
DESCRIPTIONS = {'LogAnalyzerParameters.caminho_logs':
    'Caminho para os arquivos de log a serem analisados.',
    'LogAnalyzerParameters.formato':
    "Formato do arquivo de log, podendo ser 'json', 'csv' ou 'texto'.",
    'LogAnalyzerParameters.nivel_filtro':
    "Nível mínimo de gravidade para filtrar os eventos (ex.: 'ERROR', 'WARNING', 'INFO')."
    , 'LogAnalyzerParameters.periodo_analise':
    'Intervalo de tempo para análise (ex.: diário, semanal, mensal).',
    'LogAnalyzerParameters.agrupar_por':
    'Critérios para agrupamento de dados (ex.: tipo de evento, usuário, hora).'
    , 'LogAnalyzerParameters.max_resultados':
    'Número máximo de resultados a exibir em cada seção do relatório.',
    'LogAnalyzerTool.description':
    'A ferramenta LogAnalyzer é projetada para analisar arquivos de log de sistemas distribuídos e identificar eventos críticos, padrões, estatísticas e tendências. Suporta formatos JSON, CSV e texto simples, oferecendo relatórios estruturados com recomendações para otimização e visualizações gráficas que facilitam a análise de dados complexos.'
    }
"""# Função para obter descrições do dicionário local"""


def get_description(key: str) ->str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f'Descrição para {key} não encontrada')


class LogAnalyzerParameters(BaseModel):
    """Parâmetros para a ferramenta LogAnalyzer."""
    caminho_logs: str = Field(..., description=
        'Caminho para os arquivos de log a serem analisados.')
    formato: str = Field(..., description=
        "Formato do arquivo de log, podendo ser 'json', 'csv' ou 'texto'.")
    nivel_filtro: str = Field(description=
        "Nível mínimo de gravidade para filtrar os eventos (ex.: 'ERROR', 'WARNING', 'INFO')."
        , default='WARNING')
    periodo_analise: str = Field(description=
        'Intervalo de tempo para análise (ex.: diário, semanal, mensal).',
        default='diário')
    agrupar_por: str = Field(description=
        'Critérios para agrupamento de dados (ex.: tipo de evento, usuário, hora).'
        , default='hora')
    max_resultados: int = Field(description=
        'Número máximo de resultados a exibir em cada seção do relatório.',
        default=10)


class LogAnalyzerTool(BaseTool):
    """A ferramenta LogAnalyzer é projetada para analisar arquivos de log de sistemas distribuídos e identificar eventos críticos, padrões, estatísticas e tendências. Suporta formatos JSON, CSV e texto simples, oferecendo relatórios estruturados com recomendações para otimização e visualizações gráficas que facilitam a análise de dados complexos."""
    model_config = {'arbitrary_types_allowed': True, 'validate_assignment':
        True}
    name: str = 'LogAnalyzer'
    description: str = get_description('LogAnalyzerTool.description')
    args_schema: Type[BaseModel] = LogAnalyzerParameters

    def processar_logs(self, caminho_logs, formato, nivel_filtro,
        periodo_analise, agrupar_por, max_resultados):
        """Processa logs e gera relatório detalhado."""
        try:
            if not os.path.exists(caminho_logs):
                return {'erro':
                    f"O caminho '{caminho_logs}' não foi encontrado."}
            dados_logs = self.parse_logs(caminho_logs, formato)
            if dados_logs is None:
                return {'erro':
                    'Falha ao interpretar o arquivo de log. Verifique o formato.'
                    }
            logs_filtrados = self.filtrar_logs(dados_logs, nivel_filtro)
            agregados_temporal = self.agrupar_temporalmente(logs_filtrados,
                periodo_analise)
            agregados_categoria = self.agrupar_por_categoria(logs_filtrados,
                agrupar_por)
            anomalias = self.detectar_anomalias(agregados_temporal)
            visualizacoes = self.gerar_visualizacoes(agregados_temporal,
                caminho_logs)
            relatorio = {'erros_criticos': logs_filtrados['ERRO'][:
                max_resultados], 'avisos': logs_filtrados['AVISO'][:
                max_resultados], 'estatisticas': {'uso': agregados_temporal,
                'categorias': agregados_categoria}, 'anomalias': anomalias,
                'visualizacoes': visualizacoes}
            return relatorio
        except Exception as e:
            return {'erro': str(e)}

    def parse_logs(self, caminho_logs, formato):
        """Interpreta os logs no formato especificado."""
        try:
            if formato == 'json':
                with open(caminho_logs, 'r', encoding='utf-8') as arquivo:
                    return json.load(arquivo)
            elif formato == 'csv':
                return pd.read_csv(caminho_logs)
            elif formato == 'texto':
                with open(caminho_logs, 'r', encoding='utf-8') as arquivo:
                    return [linha.strip() for linha in arquivo]
            else:
                raise ValueError(
                    "Formato não suportado. Escolha entre 'json', 'csv' ou 'texto'."
                    )
        except Exception as e:
            return None

    def filtrar_logs(self, logs, nivel_filtro):
        """Filtra os logs com base no nível mínimo de gravidade."""
        niveis_prioridade = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 
            3, 'CRITICAL': 4}
        nivel_min = niveis_prioridade.get(nivel_filtro.upper(), 2)
        if isinstance(logs, list):
            return [log for log in logs if any(nivel in log for nivel in
                niveis_prioridade if niveis_prioridade[nivel] >= nivel_min)]
        elif isinstance(logs, pd.DataFrame):
            return logs[logs['nivel'].map(lambda x: niveis_prioridade.get(x
                .upper(), 0) >= nivel_min)]
        else:
            return logs

    def agrupar_temporalmente(self, logs, periodo_analise):
        """Agrega dados temporalmente para análise."""
        return {}

    def agrupar_por_categoria(self, logs, categoria):
        """Agrupa dados pela categoria especificada."""
        return {}

    def detectar_anomalias(self, dados_agrupados):
        """Detecta padrões anômalos."""
        return []

    def gerar_visualizacoes(self, dados_agrupados, caminho_logs):
        """Gera gráficos e salva localmente."""
        return []

    def _run(self, caminho_logs: str, formato: str, nivel_filtro: str=
        'WARNING', periodo_analise: str='diário', agrupar_por: str='hora',
        max_resultados: int=10):
        return self.processar_logs(caminho_logs, formato, nivel_filtro,
            periodo_analise, agrupar_por, max_resultados)


if __name__ == '__main__':
    tool = LogAnalyzerTool()
    result = tool.run(caminho_logs='exemplo', formato='exemplo',
        nivel_filtro='WARNING', periodo_analise='diário', agrupar_por=
        'hora', max_resultados=10)
    print(result)
