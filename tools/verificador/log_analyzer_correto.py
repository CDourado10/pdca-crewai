#!/usr/bin/env python
"""
Exemplo de uso do DynamicToolCreator para criar um analisador de logs.

Este script demonstra como criar uma ferramenta mais complexa
usando o DynamicToolCreator para analisar arquivos de log.
"""

import sys
import os

# Adicionar o diretório raiz ao path para importações absolutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from crews.pdca.tools.dynamic_tool_creator import DynamicToolCreator

def criar_analisador_logs():
    """Cria uma ferramenta de análise de logs usando o DynamicToolCreator."""

    # Instanciar o criador de ferramentas
    tool_creator = DynamicToolCreator()

    # Definir e criar a ferramenta de análise de logs
    result = tool_creator.run(
        name="LogAnalyzer",
        description="Ferramenta para análise de arquivos de log, identificando erros, avisos e padrões de uso.",
        parameters=[
            {
                "name": "caminho_arquivo",
                "type": "string",
                "description": "Caminho para o arquivo de log a ser analisado",
                "required": True
            },
            {
                "name": "nivel_gravidade",
                "type": "string",
                "description": "Nível mínimo de gravidade para filtrar (ERROR, WARNING, INFO, DEBUG)",
                "required": False,
                "default": "WARNING"
            },
            {
                "name": "max_linhas",
                "type": "integer",
                "description": "Número máximo de linhas a processar",
                "required": False,
                "default": 1000
            },
            {
                "name": "formato_saida",
                "type": "string",
                "description": "Formato da saída (texto ou json)",
                "required": False,
                "default": "texto"
            }
        ],
        implementation='''
        def _run(self, caminho_arquivo, nivel_gravidade, max_linhas, formato_saida):
            """Implementação obrigatória do método _run para ferramentas BaseTool."""
            return self.processar_arquivo_log(caminho_arquivo, nivel_gravidade, max_linhas, formato_saida)
        ''',
        imports=[
            "import re",
            "import json",
            "from datetime import datetime",
            "from collections import Counter",
            "from typing import Dict, List, Any, Optional"
        ],
        custom_methods=[
            '''def processar_arquivo_log(self, caminho_arquivo, nivel_gravidade, max_linhas, formato_saida):
    """Processa um arquivo de log e retorna um relatório detalhado."""
    import re
    import json
    from datetime import datetime
    from collections import Counter
    
    # Constantes para níveis de gravidade
    NIVEIS_GRAVIDADE = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3,
        "CRITICAL": 4
    }
    
    # Validar parâmetros
    nivel_min = NIVEIS_GRAVIDADE.get(nivel_gravidade.upper(), 2)  # Padrão WARNING
    max_linhas = min(max(1, max_linhas), 10000)  # Limitar entre 1 e 10.000
    
    # Inicializar contadores e coletores
    total_linhas = 0
    total_erros = 0
    total_avisos = 0
    # Definir o padrão regex de forma simples para evitar problemas de escape
    padrao_data = re.compile('\\[(.+?)\\]')
    ocorrencias_por_hora = {}
    mensagens_comuns = Counter()
    eventos_filtrados = []
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            for i, linha in enumerate(arquivo):
                if i >= max_linhas:
                    break
                    
                total_linhas += 1
                
                # Detectar nível de gravidade
                nivel_linha = None
                for nivel in NIVEIS_GRAVIDADE:
                    if nivel in linha.upper():
                        nivel_linha = nivel
                        nivel_valor = NIVEIS_GRAVIDADE[nivel]
                        if nivel_valor == 3:  # ERROR
                            total_erros += 1
                        elif nivel_valor == 2:  # WARNING
                            total_avisos += 1
                        break
                
                # Filtrar por nível mínimo de gravidade
                if nivel_linha and NIVEIS_GRAVIDADE.get(nivel_linha, 0) >= nivel_min:
                    # Extrair timestamp
                    match_data = padrao_data.search(linha)
                    if match_data:
                        data_str = match_data.group(1)
                        try:
                            data = datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
                            hora = data.strftime('%Y-%m-%d %H')
                            ocorrencias_por_hora[hora] = ocorrencias_por_hora.get(hora, 0) + 1
                        except ValueError:
                            pass

                    # Extrair mensagem principal (simplificada)
                    mensagem = linha.strip()
                    if len(mensagem) > 50:
                        mensagem = mensagem[:47] + "..."
                    mensagens_comuns[mensagem] += 1

                    # Adicionar à lista de eventos filtrados
                    eventos_filtrados.append({
                        "nivel": nivel_linha,
                        "linha": i + 1,
                        "mensagem": linha.strip()
                    })

        # Preparar relatório
        resumo = {
            "arquivo": caminho_arquivo,
            "total_linhas_lidas": total_linhas,
            "total_erros": total_erros,
            "total_avisos": total_avisos,
            "nivel_filtro": nivel_gravidade,
            "distribuicao_temporal": dict(sorted(ocorrencias_por_hora.items())),
            "mensagens_mais_comuns": dict(mensagens_comuns.most_common(5)),
            "eventos_filtrados": eventos_filtrados[:30]  # Limitar a 30 eventos
        }

        # Formatar saída
        if formato_saida.lower() == "json":
            return json.dumps(resumo, indent=2)
        else:
            return self.formatar_relatorio_texto(resumo)

    except Exception as e:
        return {"erro": f"Erro ao processar arquivo de log: {repr(e)}"}
''',
            '''def formatar_relatorio_texto(self, resumo):
    """Formata o relatório de análise de log em formato textual estruturado."""
    saida = f"## Relatório de Análise de Log\\n\\n"
    saida += f"**Arquivo:** {resumo['arquivo']}\\n"
    saida += f"**Linhas lidas:** {resumo['total_linhas_lidas']}\\n"
    saida += f"**Erros encontrados:** {resumo['total_erros']}\\n"
    saida += f"**Avisos encontrados:** {resumo['total_avisos']}\\n"
    saida += f"**Nível de filtro aplicado:** {resumo['nivel_filtro']}\\n\\n"

    saida += "### Distribuição Temporal\\n\\n"
    for hora, contagem in resumo['distribuicao_temporal'].items():
        saida += f"- {hora}h: {contagem} ocorrências\\n"

    saida += "\\n### Mensagens Mais Comuns\\n\\n"
    for msg, contagem in resumo['mensagens_mais_comuns'].items():
        saida += f"- ({contagem}x) {msg}\\n"

    saida += "\\n### Eventos Filtrados (Primeiros 30)\\n\\n"
    for evento in resumo['eventos_filtrados']:
        saida += f"[{evento['nivel']}] Linha {evento['linha']}: {evento['mensagem'][:100]}\\n"

    return saida'''
        ]
    )

    print(f"Resultado: {result}")
    return result

if __name__ == "__main__":
    criar_analisador_logs()
