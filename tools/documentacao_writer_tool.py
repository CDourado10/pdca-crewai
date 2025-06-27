from typing import Type
import os
from pathlib import Path
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator


# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "DocumentacaoWriterInput.categoria": "Categoria da documentação. Exemplos: 'arquitetura', 'api', 'processo', 'tutorial', 'manual', 'referencia'.",
    
    "DocumentacaoWriterInput.titulo": "Título descritivo do documento. Será usado como parte do nome do arquivo.",
    
    "DocumentacaoWriterInput.conteudo": "Conteúdo completo do documento, formatado em markdown. Pode incluir explicações, diagramas, exemplos de código, entre outros elementos relevantes.",
    
    "DocumentacaoWriterInput.versao": "Versão do documento (por exemplo: '1.0', '2.3.1'). Ajuda a rastrear a evolução da documentação.",
    
    "DocumentacaoWriterInput.tags": "Lista de palavras-chave relacionadas ao documento, separadas por vírgula. Ajuda na classificação e busca.",
    
    "DocumentacaoWriterInput.role_agente": "Papel/função do agente que está criando a documentação. Por exemplo: 'especialista_arquitetura', 'documentador', 'analista_tecnico'.",
    
    "DocumentacaoWriterInput.sobrescrever": "Define se o arquivo deve ser sobrescrito caso já exista. Se True, substitui completamente o arquivo existente. Se False e o arquivo já existir, a operação será cancelada com um erro.",
    
    "DocumentacaoWriterTool.description": """Cria e salva documentação na pasta 'documentacao'.
Permite que os agentes documentem aspectos do sistema como arquitetura, processos, APIs, tutoriais e manuais.
Cada documento é salvo em um arquivo markdown com metadados como categoria, data, versão e autor.
A documentação é organizada em categorias para facilitar a navegação e consulta."""
}


def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, "Descrição não disponível")


class DocumentacaoWriterInput(BaseModel):
    """Input schema para DocumentacaoWriterTool."""
    
    categoria: str = Field(..., description=get_description("DocumentacaoWriterInput.categoria"))
    titulo: str = Field(..., description=get_description("DocumentacaoWriterInput.titulo"))
    conteudo: str = Field(..., description=get_description("DocumentacaoWriterInput.conteudo"))
    versao: str = Field("1.0", description=get_description("DocumentacaoWriterInput.versao"))
    tags: str = Field("", description=get_description("DocumentacaoWriterInput.tags"))
    role_agente: str = Field(..., description=get_description("DocumentacaoWriterInput.role_agente"))
    sobrescrever: bool = Field(True, description=get_description("DocumentacaoWriterInput.sobrescrever"))
    
    @validator('categoria')
    def validar_categoria(cls, v):
        """Valida a categoria da documentação."""
        # Verificar se não contém caracteres inválidos para nome de diretório
        for char in ['<', '>', ':', '"', '|', '?', '*']:
            if char in v:
                raise ValueError(f"Categoria inválida: '{v}'. O caractere '{char}' não é permitido em nomes de diretório.")
        return v
    
    @validator('titulo')
    def validar_titulo(cls, v):
        """Valida o título do documento."""
        # Verificar se não contém caracteres inválidos para nome de arquivo
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            if char in v:
                raise ValueError(f"Título inválido: '{v}'. O caractere '{char}' não é permitido em nomes de arquivo.")
        return v


class DocumentacaoWriterTool(BaseTool):
    name: str = "documentacao_writer"
    description: str = get_description("DocumentacaoWriterTool.description")
    args_schema: Type[BaseModel] = DocumentacaoWriterInput
    
    def _obter_diretorio_documentacao(self) -> Path:
        """Obtém o caminho absoluto para o diretório 'documentacao'."""
        # Diretório atual do script
        diretorio_atual = Path(__file__).resolve().parent
        
        # Navegar até a raiz do projeto (assumindo a estrutura crews/pdca/tools -> raiz)
        diretorio_raiz = diretorio_atual.parent.parent.parent
        
        # Caminho para o diretório documentacao
        diretorio_documentacao = diretorio_raiz / 'documentacao'
        
        # Criar o diretório se não existir
        if not diretorio_documentacao.exists():
            diretorio_documentacao.mkdir(parents=True, exist_ok=True)
        
        return diretorio_documentacao

    def _run(self, categoria: str, titulo: str, conteudo: str, role_agente: str, versao: str = "1.0", tags: str = "", sobrescrever: bool = True) -> str:
        """
        Cria e salva um documento na pasta 'documentacao'.
        
        Args:
            categoria: Categoria do documento (ex: arquitetura, api, tutorial).
            titulo: Título descritivo do documento.
            conteudo: Conteúdo completo do documento.
            role_agente: Papel/função do agente que está criando o documento.
            versao: Versão do documento (ex: 1.0, 2.3.1).
            tags: Tags relacionadas ao documento, separadas por vírgula.
            sobrescrever: Se True, substitui arquivos existentes. Se False, falha caso o arquivo já exista.
            
        Returns:
            Mensagem formatada com o resultado da operação.
        """
        try:
            # Obter o diretório documentacao
            diretorio_documentacao = self._obter_diretorio_documentacao()
            
            # Construir o caminho completo para a categoria
            caminho_categoria = diretorio_documentacao / categoria
            
            # Garantir que o diretório da categoria exista
            caminho_categoria.mkdir(parents=True, exist_ok=True)
            
            # Gerar nome de arquivo baseado no título, versão e role do agente
            titulo_formatado = titulo.replace(' ', '_').lower()
            role_formatada = role_agente.replace(' ', '_').lower()
            nome_arquivo_base = f"{titulo_formatado}_v{versao}_by_{role_formatada}"
            nome_arquivo = f"{nome_arquivo_base}.md"
            
            # Caminho completo do arquivo
            caminho_arquivo = caminho_categoria / nome_arquivo
            
            # Verificar se o arquivo já existe
            if caminho_arquivo.exists() and not sobrescrever:
                return f"""
                ## ❌ Operação cancelada
                
                - **Documento:** {titulo}
                - **Caminho:** {caminho_arquivo}
                - **Status:** Falha - arquivo já existe e a opção 'sobrescrever' está desativada
                - **Ação sugerida:** Defina 'sobrescrever=True' para substituir o arquivo existente ou altere a versão
                """
            
            # Formatar as tags
            tags_formatadas = tags.strip()
            
            # Preparar o conteúdo do arquivo com metadados
            data_formatada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            
            conteudo_formatado = f"""# {titulo}

## Metadados
- **Data:** {data_formatada}
- **Categoria:** {categoria}
- **Versão:** {versao}
- **Autor:** {role_agente}
- **Tags:** {tags_formatadas}

{conteudo}
"""
            
            # Escrever o conteúdo no arquivo
            with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                arquivo.write(conteudo_formatado)
            
            # Preparar o caminho relativo para exibição mais limpa
            caminho_relativo = os.path.join('documentacao', categoria, nome_arquivo)
            
            return f"""
            ## ✅ Documento criado com sucesso
            
            - **Título:** {titulo}
            - **Categoria:** {categoria}
            - **Versão:** {versao}
            - **Autor:** {role_agente}
            - **Arquivo:** {nome_arquivo}
            - **Caminho:** {caminho_relativo}
            - **Tamanho:** {len(conteudo_formatado)} caracteres
            - **Data:** {data_formatada}
            - **Status:** {"Documento sobrescrito" if caminho_arquivo.exists() else "Novo documento criado"}
            """
                
        except Exception as e:
            return f"""
            ## ❌ Erro ao criar documento
            
            - **Título:** {titulo}
            - **Categoria:** {categoria}
            - **Autor:** {role_agente}
            - **Erro:** {str(e)}
            - **Sugestão:** Verifique permissões de escrita e se o caminho é válido
            """


if __name__ == "__main__":
    # Exemplo de uso da ferramenta para testes
    ferramenta = DocumentacaoWriterTool()
    
    # Escolha qual exemplo quer rodar
    exemplo_a_executar = 1  # Mude este número para testar diferentes exemplos
    
    if exemplo_a_executar == 1:
        # Exemplo 1: Documento de arquitetura
        print("\n=== EXEMPLO 1: Documento de Arquitetura ===\n")
        resultado = ferramenta._run(
            categoria="arquitetura",
            titulo="Arquitetura de Microserviços do Sistema",
            conteudo="""## Visão Geral

Esta documentação descreve a arquitetura de microserviços adotada no sistema.

### Componentes Principais

1. **API Gateway** - Ponto de entrada único para todas as requisições
2. **Serviço de Autenticação** - Gerencia identidades e tokens
3. **Serviço de Processamento** - Implementa a lógica principal do negócio
4. **Banco de Dados** - Armazena dados persistentes

### Diagrama de Arquitetura

```
[Cliente] → [API Gateway] → [Serviços]
                ↓
         [Banco de Dados]
```

### Fluxo de Comunicação

1. Cliente envia requisição para o API Gateway
2. API Gateway valida a autenticação com o Serviço de Autenticação
3. Requisição é encaminhada para o serviço apropriado
4. Resultado é retornado para o cliente

### Tecnologias Utilizadas

- **API Gateway**: Express.js
- **Microserviços**: Node.js
- **Banco de Dados**: MongoDB
- **Comunicação**: REST e gRPC""",
            role_agente="arquiteto_sistema",
            versao="1.0",
            tags="arquitetura, microserviços, api, design"
        )
        print(resultado)
    
    elif exemplo_a_executar == 2:
        # Exemplo 2: Tutorial
        print("\n=== EXEMPLO 2: Tutorial ===\n")
        resultado = ferramenta._run(
            categoria="tutorial",
            titulo="Como usar a API de Análise de Dados",
            conteudo="""## Introdução

Este tutorial explica como utilizar a API de Análise de Dados para processar conjuntos de dados.

### Pré-requisitos

- Credenciais de API válidas
- Python 3.8+
- Biblioteca requests instalada

### Passo 1: Autenticação

```python
import requests

API_KEY = "sua-chave-api"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Teste de autenticação
response = requests.get("https://api.exemplo.com/auth/test", headers=headers)
if response.status_code == 200:
    print("Autenticação bem-sucedida!")
else:
    print("Falha na autenticação.")
```

### Passo 2: Envio de Dados

```python
# Preparar os dados
data = {
    "dataset_name": "vendas_2023",
    "format": "csv",
    "analysis_type": "trend"
}

# Enviar para processamento
response = requests.post(
    "https://api.exemplo.com/analyze", 
    json=data,
    headers=headers
)

job_id = response.json()["job_id"]
print(f"Análise iniciada. ID: {job_id}")
```

### Passo 3: Obtenção de Resultados

```python
# Verificar status e obter resultados
result_response = requests.get(
    f"https://api.exemplo.com/results/{job_id}",
    headers=headers
)

if result_response.status_code == 200:
    results = result_response.json()
    print("Resultados:", results)
else:
    print("Análise ainda em processamento ou erro.")
```

### Dicas e Boas Práticas

- Sempre verifique o status da análise antes de tentar obter resultados
- Utilize timeouts adequados para análises complexas
- Implemente retry logic para casos de falha temporária""",
            role_agente="especialista_api",
            versao="1.2",
            tags="tutorial, api, análise de dados, código, exemplo"
        )
        print(resultado)
        
    elif exemplo_a_executar == 3:
        # Exemplo 3: Referência
        print("\n=== EXEMPLO 3: Documentação de Referência ===\n")
        resultado = ferramenta._run(
            categoria="referencia",
            titulo="Guia de Referência da API REST",
            conteudo="""## API REST - Referência Completa

Este documento fornece a referência completa para a API REST do sistema.

### Base URL

```
https://api.exemplo.com/v1
```

### Endpoints

#### Usuários

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /users | Lista todos os usuários |
| GET | /users/{id} | Obtém detalhes de um usuário |
| POST | /users | Cria um novo usuário |
| PUT | /users/{id} | Atualiza um usuário existente |
| DELETE | /users/{id} | Remove um usuário |

#### Produtos

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /products | Lista todos os produtos |
| GET | /products/{id} | Obtém detalhes de um produto |
| POST | /products | Adiciona um novo produto |
| PUT | /products/{id} | Atualiza um produto existente |
| DELETE | /products/{id} | Remove um produto |

### Códigos de Status

- 200: Sucesso
- 201: Recurso criado com sucesso
- 400: Requisição inválida
- 401: Não autorizado
- 404: Recurso não encontrado
- 500: Erro interno do servidor

### Exemplos de Resposta

#### Obter Usuário (GET /users/123)

```json
{
  "id": 123,
  "name": "João Silva",
  "email": "joao@exemplo.com",
  "role": "admin",
  "created_at": "2023-01-15T14:30:00Z"
}
```

### Limites de Taxa

- Máximo de 100 requisições por minuto por IP
- Máximo de 1000 requisições por dia por chave de API""",
            role_agente="documentador_api",
            versao="2.1",
            tags="referência, api, rest, endpoints, http"
        )
        print(resultado)
    
    # Para executar via comando:
    # python -m crews.pdca.tools.documentacao_writer_tool
