from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import Counter
from sklearn.ensemble import IsolationForest
"""# Dicionário centralizado de descrições"""
DESCRIPTIONS = {'LogAnalyticsToolParameters.caminho_logs':
    'Path to the directory or specific log files to be analyzed.',
    'LogAnalyticsToolParameters.formato':
    'Format of the log files (JSON, text, CSV).',
    'LogAnalyticsToolParameters.nivel_filtro':
    "List of log levels to filter (e.g., ['ERROR', 'WARNING']).",
    'LogAnalyticsToolParameters.periodo_analise':
    "Dictionary specifying the start and end of the analysis period (e.g., {'inicio': '2023-01-01', 'fim': '2023-01-31'})."
    , 'LogAnalyticsToolParameters.agrupar_por':
    "Parameter for grouping logs (e.g., 'hour', 'type').",
    'LogAnalyticsToolParameters.max_resultados':
    'Maximum number of results to display.',
    'LogAnalyticsToolTool.description':
    'LogAnalyticsTool is designed to analyze log files from distributed systems, supporting multiple formats such as JSON, plain text, and CSV. It extracts and identifies critical errors, warnings, usage patterns, and operational anomalies efficiently, producing structured reports in Markdown format with visualizations for better decision-making and system optimization.'
    }
"""# Função para obter descrições do dicionário local"""


def get_description(key: str) ->str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f'Descrição para {key} não encontrada')


class LogAnalyticsToolParameters(BaseModel):
    """Parâmetros para a ferramenta LogAnalyticsTool."""
    caminho_logs: str = Field(..., description=
        'Path to the directory or specific log files to be analyzed.')
    formato: str = Field(..., description=
        'Format of the log files (JSON, text, CSV).')
    nivel_filtro: Any = Field(description=
        "List of log levels to filter (e.g., ['ERROR', 'WARNING']).",
        default=['ERROR', 'WARNING'])
    periodo_analise: Any = Field(..., description=
        "Dictionary specifying the start and end of the analysis period (e.g., {'inicio': '2023-01-01', 'fim': '2023-01-31'})."
        )
    agrupar_por: str = Field(description=
        "Parameter for grouping logs (e.g., 'hour', 'type').", default='hour')
    max_resultados: int = Field(description=
        'Maximum number of results to display.', default=30)


class LogAnalyticsToolTool(BaseTool):
    """LogAnalyticsTool is designed to analyze log files from distributed systems, supporting multiple formats such as JSON, plain text, and CSV. It extracts and identifies critical errors, warnings, usage patterns, and operational anomalies efficiently, producing structured reports in Markdown format with visualizations for better decision-making and system optimization."""
    model_config = {'arbitrary_types_allowed': True, 'validate_assignment':
        True}
    name: str = 'LogAnalyticsTool'
    description: str = get_description('LogAnalyticsToolTool.description')
    args_schema: Type[BaseModel] = LogAnalyticsToolParameters

    def analisar_logs(self, caminho_logs, formato, nivel_filtro,
        periodo_analise, agrupar_por, max_resultados):
        """Performs log analysis and generates a detailed report."""
        try:
            logs = self.carregar_logs(caminho_logs, formato)
            logs_filtrados = self.filtrar_logs_por_periodo(logs,
                periodo_analise, nivel_filtro)
            agregados = self.agrupar_logs(logs_filtrados, agrupar_por)
            anomalias = self.calcular_anomalias(agregados)
            return self.gerar_relatorio(logs_filtrados, agregados,
                anomalias, max_resultados)
        except Exception as e:
            return f'Erro ao analisar os logs: {str(e)}'

    def carregar_logs(self, caminho_logs, formato):
        """Loads logs from the specified path and format."""
        if not os.path.exists(caminho_logs):
            raise FileNotFoundError(f"O caminho '{caminho_logs}' não existe.")
        if formato == 'JSON':
            with open(caminho_logs, 'r') as f:
                return pd.DataFrame(json.load(f))
        elif formato == 'CSV':
            return pd.read_csv(caminho_logs)
        elif formato == 'text':
            with open(caminho_logs, 'r') as f:
                return pd.DataFrame([{'line': line.strip()} for line in f.
                    readlines()])
        else:
            raise ValueError(f"Formato '{formato}' não suportado.")

    def filtrar_logs_por_periodo(self, logs, periodo_analise, nivel_filtro):
        """Filters logs based on analysis period and levels."""
        inicio = datetime.strptime(periodo_analise['inicio'], '%Y-%m-%d')
        fim = datetime.strptime(periodo_analise['fim'], '%Y-%m-%d')
        logs['timestamp'] = pd.to_datetime(logs['timestamp'])
        return logs[(logs['timestamp'] >= inicio) & (logs['timestamp'] <=
            fim) & logs['level'].isin(nivel_filtro)]

    def agrupar_logs(self, logs, agrupar_por):
        """Aggregates logs by the specified parameter."""
        if agrupar_por == 'hour':
            return logs.groupby(logs['timestamp'].dt.hour).size()
        elif agrupar_por == 'type':
            return logs.groupby('type').size()
        else:
            raise ValueError(f"Agrupamento '{agrupar_por}' não suportado.")

    def calcular_anomalias(self, agregados):
        """Detects anomalies in aggregated logs using Isolation Forest."""
        model = IsolationForest()
        model.fit(agregados.values.reshape(-1, 1))
        return model.predict(agregados.values.reshape(-1, 1))

    def gerar_relatorio(self, logs_filtrados, agregados, anomalias,
        max_resultados):
        """Generates a detailed Markdown report with visualizations."""
        report = '# Relatório de Análise de Logs\n\n'
        report += f'## Logs Filtrados ({len(logs_filtrados)} registros)\n'
        report += logs_filtrados.head(max_resultados).to_markdown()
        report += '\n\n## Logs Agrupados\n'
        report += agregados.to_markdown()
        report += '\n\n## Anomalias Detectadas\n'
        report += pd.Series(anomalias).to_markdown()
        plt.figure(figsize=(10, 5))
        agregados.plot(kind='bar')
        plt.title('Distribuição de Logs')
        plt.savefig('distribuicao_logs.png')
        report += '\n\n![Distribuição de Logs](distribuicao_logs.png)\n'
        return report

    def _run(self, caminho_logs: str, formato: str, nivel_filtro: Any,
        periodo_analise: Any=['ERROR', 'WARNING'], agrupar_por: str='hour',
        max_resultados: int=30):
        return self.analisar_logs(caminho_logs, formato, nivel_filtro,
            periodo_analise, agrupar_por, max_resultados)


if __name__ == '__main__':
    tool = LogAnalyticsToolTool()
    result = tool.run(caminho_logs='exemplo', formato='exemplo',
        nivel_filtro=['ERROR', 'WARNING'], periodo_analise='exemplo',
        agrupar_por='hour', max_resultados=30)
    print(result)
