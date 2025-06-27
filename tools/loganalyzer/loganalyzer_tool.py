from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import re
import json
from datetime import datetime
from collections import Counter
from typing import Dict, List, Any, Optional
"""# Dicionário centralizado de descrições"""
DESCRIPTIONS = {'LogAnalyzerParameters.caminho_arquivo':
    'Caminho para o arquivo de log a ser analisado',
    'LogAnalyzerParameters.nivel_gravidade':
    'Nível mínimo de gravidade para filtrar (ERROR, WARNING, INFO, DEBUG)',
    'LogAnalyzerParameters.max_linhas':
    'Número máximo de linhas a processar',
    'LogAnalyzerParameters.formato_saida':
    'Formato da saída (texto ou json)', 'LogAnalyzerTool.description':
    'Ferramenta para análise de arquivos de log, identificando erros, avisos e padrões de uso.'
    }
"""# Função para obter descrições do dicionário local"""


def get_description(key: str) ->str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f'Descrição para {key} não encontrada')


class LogAnalyzerParameters(BaseModel):
    """Parâmetros para a ferramenta LogAnalyzer."""
    caminho_arquivo: str = Field(..., description=
        'Caminho para o arquivo de log a ser analisado')
    nivel_gravidade: str = Field(description=
        'Nível mínimo de gravidade para filtrar (ERROR, WARNING, INFO, DEBUG)',
        default='WARNING')
    max_linhas: int = Field(description=
        'Número máximo de linhas a processar', default=1000)
    formato_saida: str = Field(description=
        'Formato da saída (texto ou json)', default='texto')


class LogAnalyzerTool(BaseTool):
    """Ferramenta para análise de arquivos de log, identificando erros, avisos e padrões de uso."""
    model_config = {'arbitrary_types_allowed': True, 'validate_assignment':
        True}
    name: str = 'LogAnalyzer'
    description: str = get_description('LogAnalyzerTool.description')
    args_schema: Type[BaseModel] = LogAnalyzerParameters

    def processar_arquivo_log(self, caminho_arquivo, nivel_gravidade,
        max_linhas, formato_saida):
        """Processa um arquivo de log e retorna um relatório detalhado."""
        NIVEIS_GRAVIDADE = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3,
            'CRITICAL': 4}
        nivel_min = NIVEIS_GRAVIDADE.get(nivel_gravidade.upper(), 2)
        max_linhas = min(max(1, max_linhas), 10000)
        total_linhas = 0
        total_erros = 0
        total_avisos = 0
        padrao_data = re.compile(
            '\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\]')
        ocorrencias_por_hora = {}
        mensagens_comuns = Counter()
        eventos_filtrados = []
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                for i, linha in enumerate(arquivo):
                    if i >= max_linhas:
                        break
                    total_linhas += 1
                    nivel_linha = None
                    for nivel in NIVEIS_GRAVIDADE:
                        if nivel in linha.upper():
                            nivel_linha = nivel
                            nivel_valor = NIVEIS_GRAVIDADE[nivel]
                            if nivel_valor == 3:
                                total_erros += 1
                            elif nivel_valor == 2:
                                total_avisos += 1
                            break
                    if nivel_linha and NIVEIS_GRAVIDADE.get(nivel_linha, 0
                        ) >= nivel_min:
                        match_data = padrao_data.search(linha)
                        if match_data:
                            data_str = match_data.group(1)
                            try:
                                data = datetime.strptime(data_str,
                                    '%Y-%m-%d %H:%M:%S')
                                hora = data.strftime('%Y-%m-%d %H')
                                ocorrencias_por_hora[hora
                                    ] = ocorrencias_por_hora.get(hora, 0) + 1
                            except ValueError:
                                pass
                        mensagem = linha.strip()
                        if len(mensagem) > 50:
                            mensagem = mensagem[:47] + '...'
                        mensagens_comuns[mensagem] += 1
                        eventos_filtrados.append({'nivel': nivel_linha,
                            'linha': i + 1, 'mensagem': linha.strip()})
            resumo = {'arquivo': caminho_arquivo, 'total_linhas_lidas':
                total_linhas, 'total_erros': total_erros, 'total_avisos':
                total_avisos, 'nivel_filtro': nivel_gravidade,
                'distribuicao_temporal': dict(sorted(ocorrencias_por_hora.
                items())), 'mensagens_mais_comuns': dict(mensagens_comuns.
                most_common(5)), 'eventos_filtrados': eventos_filtrados[:30]}
            if formato_saida.lower() == 'json':
                return json.dumps(resumo, indent=2)
            else:
                return self.formatar_relatorio_texto(resumo)
        except Exception as e:
            return {'erro': f'Erro ao processar arquivo de log: {repr(e)}'}

    def formatar_relatorio_texto(self, resumo):
        """Formata o relatório de análise de log em formato textual estruturado."""
        saida = f'## Relatório de Análise de Log\n\n'
        saida += f"**Arquivo:** {resumo['arquivo']}\n"
        saida += f"**Linhas lidas:** {resumo['total_linhas_lidas']}\n"
        saida += f"**Erros encontrados:** {resumo['total_erros']}\n"
        saida += f"**Avisos encontrados:** {resumo['total_avisos']}\n"
        saida += f"**Nível de filtro aplicado:** {resumo['nivel_filtro']}\n\n"
        saida += '### Distribuição Temporal\n\n'
        for hora, contagem in resumo['distribuicao_temporal'].items():
            saida += f'- {hora}h: {contagem} ocorrências\n'
        saida += '\n### Mensagens Mais Comuns\n\n'
        for msg, contagem in resumo['mensagens_mais_comuns'].items():
            saida += f'- ({contagem}x) {msg}\n'
        saida += '\n### Eventos Filtrados (Primeiros 30)\n\n'
        for evento in resumo['eventos_filtrados']:
            saida += (
                f"[{evento['nivel']}] Linha {evento['linha']}: {evento['mensagem'][:100]}\n"
                )
        return saida

    def _run(self, caminho_arquivo: str, nivel_gravidade: str='WARNING',
        max_linhas: int=1000, formato_saida: str='texto'):
        return self.processar_arquivo_log(caminho_arquivo, nivel_gravidade,
            max_linhas, formato_saida)


if __name__ == '__main__':
    tool = LogAnalyzerTool()
    result = tool.run(caminho_arquivo='exemplo', nivel_gravidade='WARNING',
        max_linhas=1000, formato_saida='texto')
    print(result)
