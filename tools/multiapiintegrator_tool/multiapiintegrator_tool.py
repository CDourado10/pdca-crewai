from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests
import json
from cachetools import TTLCache
"""# Dicionário centralizado de descrições"""
DESCRIPTIONS = {'MultiAPIIntegratorParameters.api_endpoint':
    'URL do endpoint da API externa.',
    'MultiAPIIntegratorParameters.metodo_http':
    'Método HTTP a ser utilizado (GET, POST, etc.).',
    'MultiAPIIntegratorParameters.parametros_consulta':
    'Dicionário contendo parâmetros de consulta para a requisição.',
    'MultiAPIIntegratorParameters.headers':
    'Cabeçalhos HTTP a serem enviados na requisição.',
    'MultiAPIIntegratorParameters.autenticacao':
    'Dados de autenticação como tokens ou chaves de API.',
    'MultiAPIIntegratorParameters.timeout':
    'Tempo limite para aguardar uma resposta da API.',
    'MultiAPIIntegratorParameters.formato_saida':
    'Formato de saída desejado (json ou texto).',
    'MultiAPIIntegratorTool.description':
    'Ferramenta para integrar dados de múltiplas APIs externas, gerenciar credenciais, caching, e lidar com erros, fornecendo um formato padronizado e semântico de saída.'
    }
"""# Função para obter descrições do dicionário local"""


def get_description(key: str) ->str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f'Descrição para {key} não encontrada')


class MultiAPIIntegratorParameters(BaseModel):
    """Parâmetros para a ferramenta MultiAPIIntegrator."""
    api_endpoint: str = Field(..., description=
        'URL do endpoint da API externa.')
    metodo_http: str = Field(..., description=
        'Método HTTP a ser utilizado (GET, POST, etc.).')
    parametros_consulta: Any = Field(description=
        'Dicionário contendo parâmetros de consulta para a requisição.',
        default={})
    headers: Any = Field(description=
        'Cabeçalhos HTTP a serem enviados na requisição.', default={})
    autenticacao: Any = Field(..., description=
        'Dados de autenticação como tokens ou chaves de API.')
    timeout: int = Field(description=
        'Tempo limite para aguardar uma resposta da API.', default=30)
    formato_saida: str = Field(description=
        'Formato de saída desejado (json ou texto).', default='json')


class MultiAPIIntegratorTool(BaseTool):
    """Ferramenta para integrar dados de múltiplas APIs externas, gerenciar credenciais, caching, e lidar com erros, fornecendo um formato padronizado e semântico de saída."""
    model_config = {'arbitrary_types_allowed': True, 'validate_assignment':
        True}
    name: str = 'MultiAPIIntegrator'
    description: str = get_description('MultiAPIIntegratorTool.description')
    args_schema: Type[BaseModel] = MultiAPIIntegratorParameters

    def iniciar_integracao(self, api_endpoint, metodo_http,
        parametros_consulta, headers, autenticacao, timeout, formato_saida):
        try:
            return self.processar_requisicao(api_endpoint, metodo_http,
                parametros_consulta, headers, autenticacao, timeout,
                formato_saida)
        except Exception as e:
            return self.formatar_saida({'erro': str(e)}, formato_saida,
                cache_hit=False)

    def processar_requisicao(self, api_endpoint, metodo_http,
        parametros_consulta, headers, autenticacao, timeout, formato_saida):
        """Lida com requisições a APIs externas incluindo respostas cacheadas e transformação de dados."""
        cache_key = f'{metodo_http}:{api_endpoint}:{str(parametros_consulta)}'
        resposta_cache = self.cache.get(cache_key)
        if resposta_cache:
            return self.formatar_saida(resposta_cache, formato_saida,
                cache_hit=True)
        if autenticacao:
            headers.update(autenticacao)
        response = requests.request(method=metodo_http, url=api_endpoint,
            params=parametros_consulta, headers=headers, timeout=timeout)
        resposta = {'dados': response.json() if response.headers.get(
            'Content-Type') == 'application/json' else response.text,
            'metadados': {'status': response.status_code, 'origem':
            api_endpoint, 'tempo_resposta': response.elapsed.total_seconds()}}
        if response.status_code >= 400:
            resposta['log_erros'
                ] = f'Erro HTTP {response.status_code}: {response.text[:200]}'
        self.cache[cache_key] = resposta
        return self.formatar_saida(resposta, formato_saida, cache_hit=False)

    def formatar_saida(self, dados, formato_saida, cache_hit=False):
        """Formatar saída padronizada estruturada"""
        if formato_saida == 'json':
            dados['metadados']['cache_hit'] = cache_hit
            return json.dumps(dados, indent=2)
        else:
            saida_texto = f"""## Resumo da Resposta

- Status: {dados['metadados'].get('status', 'N/A')}
- Origem: {dados['metadados'].get('origem', 'N/A')}
- Tempo de Resposta: {dados['metadados'].get('tempo_resposta', 'N/A')}s

"""
            if cache_hit:
                saida_texto += '(Dados recuperados do cache)\n\n'
            if 'dados' in dados:
                saida_texto += f"### Dados:\n\n{str(dados['dados'])[:500]}\n\n"
            if 'log_erros' in dados:
                saida_texto += '### Logs de Erro:\n\n' + str(dados['log_erros']
                    )[:500]
            return saida_texto

    def inicializar_cache(self):
        """Inicializa um sistema de cache em memória para dados de API."""
        self.cache = TTLCache(maxsize=100, ttl=300)

    def _run(self, api_endpoint: str, metodo_http: str, parametros_consulta:
        Any, headers: Any={}, autenticacao: Any={}, timeout: int=30,
        formato_saida: str='json'):
        return self.iniciar_integracao(api_endpoint, metodo_http,
            parametros_consulta, headers, autenticacao, timeout, formato_saida)


if __name__ == '__main__':
    tool = MultiAPIIntegratorTool()
    result = tool.run(api_endpoint='exemplo', metodo_http='exemplo',
        parametros_consulta={}, headers={}, autenticacao='exemplo', timeout
        =30, formato_saida='json')
    print(result)
