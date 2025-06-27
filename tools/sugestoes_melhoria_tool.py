from typing import Type
import os
from pathlib import Path
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator


# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "SugestoesMelhoriaInput.categoria": "Categoria da sugestão de melhoria. Exemplos: 'conhecimentos', 'ferramentas', 'prompts', 'agentes', 'fluxo', 'integracao'.",
    
    "SugestoesMelhoriaInput.titulo": "Título descritivo da sugestão. Será usado como parte do nome do arquivo.",
    
    "SugestoesMelhoriaInput.conteudo": "Conteúdo detalhado da sugestão de melhoria, incluindo descrição do problema atual, proposta de melhoria, benefícios esperados e, se possível, exemplos de implementação.",
    
    "SugestoesMelhoriaInput.prioridade": "Nível de prioridade da sugestão (de 1 a 5, onde 1 é a mais alta). Ajuda a categorizar a importância da implementação.",
    
    "SugestoesMelhoriaInput.tags": "Lista de palavras-chave relacionadas à sugestão, separadas por vírgula. Ajuda na classificação e busca.",
    
    "SugestoesMelhoriaInput.role_agente": "Papel/função do agente que está enviando a sugestão. Por exemplo: 'especialista_planejamento', 'analista_codigo', 'verificador_qualidade'.",
    
    "SugestoesMelhoriaTool.description": """Salva sugestões de melhoria do sistema na pasta 'sugestoes'.
Permite que os agentes comuniquem ideias para aprimorar o sistema, como melhorias em arquivos de conhecimentos,
uso das ferramentas, prompts, interação entre agentes, entre outros aspectos.
Cada sugestão é salva em um arquivo markdown com metadados como categoria, data, prioridade e tags.
Esta ferramenta funciona como um canal de comunicação entre os agentes e o desenvolvedor do sistema."""
}


def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, "Descrição não disponível")


class SugestoesMelhoriaInput(BaseModel):
    """Input schema para SugestoesMelhoriaTool."""
    
    categoria: str = Field(..., description=get_description("SugestoesMelhoriaInput.categoria"))
    titulo: str = Field(..., description=get_description("SugestoesMelhoriaInput.titulo"))
    conteudo: str = Field(..., description=get_description("SugestoesMelhoriaInput.conteudo"))
    prioridade: int = Field(3, ge=1, le=5, description=get_description("SugestoesMelhoriaInput.prioridade"))
    tags: str = Field("", description=get_description("SugestoesMelhoriaInput.tags"))
    role_agente: str = Field(..., description=get_description("SugestoesMelhoriaInput.role_agente"))
    
    @validator('categoria')
    def validar_categoria(cls, v):
        """Valida a categoria da sugestão."""
        # Verificar se não contém caracteres inválidos para nome de diretório
        for char in ['<', '>', ':', '"', '|', '?', '*']:
            if char in v:
                raise ValueError(f"Categoria inválida: '{v}'. O caractere '{char}' não é permitido em nomes de diretório.")
        return v
    
    @validator('titulo')
    def validar_titulo(cls, v):
        """Valida o título da sugestão."""
        # Verificar se não contém caracteres inválidos para nome de arquivo
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            if char in v:
                raise ValueError(f"Título inválido: '{v}'. O caractere '{char}' não é permitido em nomes de arquivo.")
        return v


class SugestoesMelhoriaTool(BaseTool):
    name: str = "sugestoes_melhoria"
    description: str = get_description("SugestoesMelhoriaTool.description")
    args_schema: Type[BaseModel] = SugestoesMelhoriaInput
    
    def _obter_diretorio_sugestoes(self) -> Path:
        """Obtém o caminho absoluto para o diretório 'sugestoes'."""
        # Diretório atual do script
        diretorio_atual = Path(__file__).resolve().parent
        
        # Navegar até a raiz do projeto (assumindo a estrutura crews/pdca/tools -> raiz)
        diretorio_raiz = diretorio_atual.parent.parent.parent
        
        # Caminho para o diretório sugestoes
        diretorio_sugestoes = diretorio_raiz / 'sugestoes'
        
        # Criar o diretório se não existir
        if not diretorio_sugestoes.exists():
            diretorio_sugestoes.mkdir(parents=True, exist_ok=True)
        
        return diretorio_sugestoes

    def _run(self, categoria: str, titulo: str, conteudo: str, role_agente: str, prioridade: int = 3, tags: str = "") -> str:
        """
        Salva uma sugestão de melhoria do sistema na pasta 'sugestoes'.
        
        Args:
            categoria: Categoria da sugestão (ex: conhecimentos, ferramentas, prompts).
            titulo: Título descritivo da sugestão.
            conteudo: Conteúdo detalhado da sugestão.
            role_agente: Papel/função do agente que está enviando a sugestão.
            prioridade: Nível de prioridade (1-5, onde 1 é mais alta).
            tags: Tags relacionadas à sugestão, separadas por vírgula.
            
        Returns:
            Mensagem formatada com o resultado da operação.
        """
        try:
            # Obter o diretório sugestoes
            diretorio_sugestoes = self._obter_diretorio_sugestoes()
            
            # Construir o caminho completo para a categoria
            caminho_categoria = diretorio_sugestoes / categoria
            
            # Garantir que o diretório da categoria exista
            caminho_categoria.mkdir(parents=True, exist_ok=True)
            
            # Gerar nome de arquivo baseado na data, título e role do agente
            data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
            titulo_formatado = titulo.replace(' ', '_').lower()
            role_formatada = role_agente.replace(' ', '_').lower()
            nome_arquivo_base = f"{data_atual}_{titulo_formatado}_by_{role_formatada}"
            nome_arquivo = f"{nome_arquivo_base}.md"
            
            # Caminho completo do arquivo
            caminho_arquivo = caminho_categoria / nome_arquivo
            
            # Verificar se o arquivo já existe e criar um nome único
            contador = 1
            while caminho_arquivo.exists():
                nome_arquivo = f"{nome_arquivo_base}_{contador}.md"
                caminho_arquivo = caminho_categoria / nome_arquivo
                contador += 1
            
            # Formatar as tags
            tags_formatadas = tags.strip()
            
            # Preparar o conteúdo do arquivo com metadados
            data_formatada = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            nivel_prioridade = "⭐" * prioridade
            
            conteudo_formatado = f"""# Sugestão: {titulo}

## Metadados
- **Data:** {data_formatada}
- **Categoria:** {categoria}
- **Autor:** {role_agente}
- **Prioridade:** {prioridade}/5 {nivel_prioridade}
- **Tags:** {tags_formatadas}

## Detalhes da Sugestão
{conteudo}
"""
            
            # Escrever o conteúdo no arquivo
            with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                arquivo.write(conteudo_formatado)
            
            # Preparar o caminho relativo para exibição mais limpa
            caminho_relativo = os.path.join('sugestoes', categoria, nome_arquivo)
            
            return f"""
            ## ✅ Sugestão de melhoria registrada com sucesso
            
            - **Título:** {titulo}
            - **Categoria:** {categoria}
            - **Autor:** {role_agente}
            - **Prioridade:** {prioridade}/5 {nivel_prioridade}
            - **Arquivo:** {nome_arquivo}
            - **Caminho:** {caminho_relativo}
            - **Tamanho:** {len(conteudo_formatado)} caracteres
            - **Data:** {data_formatada}
            - **Status:** Sugestão salva com sucesso para análise posterior
            """
                
        except Exception as e:
            return f"""
            ## ❌ Erro ao registrar sugestão de melhoria
            
            - **Título:** {titulo}
            - **Categoria:** {categoria}
            - **Autor:** {role_agente}
            - **Erro:** {str(e)}
            - **Sugestão:** Verifique permissões de escrita e se o caminho é válido
            """


if __name__ == "__main__":
    # Exemplo de uso da ferramenta para testes
    ferramenta = SugestoesMelhoriaTool()
    
    # Escolha qual exemplo quer rodar
    exemplo_a_executar = 1  # Mude este número para testar diferentes exemplos
    
    if exemplo_a_executar == 1:
        # Exemplo 1: Registrar sugestão sobre prompts
        print("\n=== EXEMPLO 1: Sugestão sobre prompts ===\n")
        resultado = ferramenta._run(
            categoria="prompts",
            titulo="Melhorar prompts da fase de planejamento",
            conteudo="""Os prompts da fase de planejamento poderiam ser mais específicos sobre as restrições de tempo e recursos.
            
Problema atual:
- Os agentes na fase de planejamento nem sempre consideram limitações práticas
- As estimativas de tempo para execução são frequentemente otimistas demais

Sugestão de melhoria:
1. Adicionar seção específica sobre "Restrições e Limitações" no prompt
2. Incluir exemplos de estimativas realistas baseadas em casos anteriores
3. Solicitar explicitamente que o agente justifique suas estimativas

Benefícios esperados:
- Planos mais realistas e executáveis
- Melhor alinhamento entre as fases de planejamento e execução
- Redução de retrabalho devido a planos inexequíveis""",
            role_agente="especialista_planejamento",
            prioridade=2,
            tags="prompts, planejamento, estimativas, tempo, restrições"
        )
        print(resultado)
    
    elif exemplo_a_executar == 2:
        # Exemplo 2: Sugestão sobre ferramentas
        print("\n=== EXEMPLO 2: Sugestão sobre ferramentas ===\n")
        resultado = ferramenta._run(
            categoria="ferramentas",
            titulo="Nova ferramenta para consulta de recursos externos",
            conteudo="""Seria útil ter uma ferramenta específica para consultar recursos externos como APIs públicas ou documentação técnica.
            
Descrição da ferramenta proposta:
- Nome: ExternalResourceTool
- Funcionalidade: Permite consultar APIs, documentações e outros recursos externos de forma padronizada
- Parâmetros principais: tipo_recurso, consulta, formato_saida

Implementação sugerida:
```python
class ExternalResourceTool(BaseTool):
    name: str = "external_resource"
    description: str = "Consulta recursos externos como APIs e documentações técnicas"
    
    def _run(self, tipo_recurso: str, consulta: str, formato_saida: str = "markdown") -> str:
        # Implementação...
```

Casos de uso:
1. Consulta a documentações técnicas durante a fase de planejamento
2. Obtenção de dados atualizados de APIs externas durante a execução
3. Validação de conceitos técnicos na fase de verificação""",
            role_agente="especialista_ferramentas",
            prioridade=3,
            tags="ferramentas, recursos externos, api, documentação"
        )
        print(resultado)
        
    elif exemplo_a_executar == 3:
        # Exemplo 3: Sugestão sobre fluxo do sistema
        print("\n=== EXEMPLO 3: Sugestão sobre fluxo do sistema ===\n")
        resultado = ferramenta._run(
            categoria="fluxo",
            titulo="Adicionar fase intermediária de feedback",
            conteudo="""O ciclo PDCA poderia se beneficiar de uma fase intermediária de feedback entre o Fazer e o Verificar.
            
Problema identificado:
Atualmente, a verificação ocorre apenas após a implementação completa, o que pode levar a retrabalho significativo caso haja problemas fundamentais.

Proposta:
Adicionar uma fase de "Feedback Intermediário" que:
1. Ocorre após 30-40% da implementação
2. Permite ajustes no plano antes de continuar
3. Envolve uma validação parcial com menos recursos

Benefícios esperados:
- Identificação precoce de problemas
- Redução de desperdício de recursos
- Maior flexibilidade para adaptação
- Maior alinhamento com metodologias ágeis

Impacto na implementação:
- Adição de uma nova crew "FeedbackCrew"
- Modificação do fluxo principal do PDCAFlow
- Novos modelos Pydantic para resultados intermediários""",
            role_agente="coordenador_pdca",
            prioridade=1,
            tags="fluxo, pdca, feedback, melhoria contínua, ágil"
        )
        print(resultado)
    
    # Para executar via comando:
    # python -m crews.pdca.tools.sugestoes_melhoria_tool
