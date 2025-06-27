from typing import Type, Optional
import os
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator


# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "KnowledgeFileWriterInput.subpasta": "Nome da subpasta dentro do diretório 'knowledge' onde o arquivo deve ser salvo. Se a subpasta não existir, ela será criada automaticamente. Exemplos: 'python', 'ferramentas/exemplos', 'documentacao/api'.",
    
    "KnowledgeFileWriterInput.nome_arquivo": "Nome do arquivo a ser criado ou sobrescrito, incluindo a extensão. Exemplos: 'documento.md', 'exemplo.txt', 'configuracao.yaml'.",
    
    "KnowledgeFileWriterInput.conteudo": "Conteúdo que será escrito no arquivo. Pode ser qualquer texto, código, ou dados formatados que devem ser salvos no arquivo especificado.",
    
    "KnowledgeFileWriterInput.sobrescrever": "Define se o arquivo deve ser sobrescrito caso já exista. Se True, substitui completamente o arquivo existente. Se False e o arquivo já existir, a operação será cancelada com um erro.",
    
    "KnowledgeFileWriterTool.description": """Cria arquivos em subpastas do diretório 'knowledge'. 
Permite criar novas subpastas automaticamente quando necessário.
É útil para armazenar documentação, exemplos, ou qualquer conteúdo textual que precise ser persistido.
A ferramenta retorna o caminho completo do arquivo criado e um status indicando sucesso ou falha."""
}


def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, "Descrição não disponível")


class KnowledgeFileWriterInput(BaseModel):
    """Input schema para KnowledgeFileWriterTool."""
    
    subpasta: str = Field(..., description=get_description("KnowledgeFileWriterInput.subpasta"))
    nome_arquivo: str = Field(..., description=get_description("KnowledgeFileWriterInput.nome_arquivo"))
    conteudo: str = Field(..., description=get_description("KnowledgeFileWriterInput.conteudo"))
    sobrescrever: bool = Field(True, description=get_description("KnowledgeFileWriterInput.sobrescrever"))
    
    @validator('subpasta')
    def validar_subpasta(cls, v):
        """Valida o nome da subpasta."""
        # Verificar se não contém caracteres inválidos para nome de diretório
        for char in ['<', '>', ':', '"', '|', '?', '*']:
            if char in v:
                raise ValueError(f"Nome de subpasta inválido: '{v}'. O caractere '{char}' não é permitido em nomes de diretório.")
        return v
    
    @validator('nome_arquivo')
    def validar_nome_arquivo(cls, v):
        """Valida o nome do arquivo."""
        # Verificar se não contém caracteres inválidos para nome de arquivo
        for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
            if char in v:
                raise ValueError(f"Nome de arquivo inválido: '{v}'. O caractere '{char}' não é permitido em nomes de arquivo.")
        return v


class KnowledgeFileWriterTool(BaseTool):
    name: str = "knowledge_file_writer"
    description: str = get_description("KnowledgeFileWriterTool.description")
    args_schema: Type[BaseModel] = KnowledgeFileWriterInput
    
    def _obter_diretorio_knowledge(self) -> Path:
        """Obtém o caminho absoluto para o diretório 'knowledge'."""
        # Diretório atual do script
        diretorio_atual = Path(__file__).resolve().parent
        
        # Navegar até a raiz do projeto (assumindo a estrutura crews/pdca/tools -> raiz)
        diretorio_raiz = diretorio_atual.parent.parent.parent
        
        # Caminho para o diretório knowledge
        diretorio_knowledge = diretorio_raiz / 'knowledge'
        
        if not diretorio_knowledge.exists():
            raise ValueError(f"Diretório 'knowledge' não encontrado em: {diretorio_knowledge}")
        
        return diretorio_knowledge

    def _run(self, subpasta: str, nome_arquivo: str, conteudo: str, sobrescrever: bool = True) -> str:
        """
        Cria um arquivo em uma subpasta do diretório 'knowledge'.
        
        Args:
            subpasta: Nome da subpasta dentro do diretório 'knowledge'.
            nome_arquivo: Nome do arquivo a ser criado.
            conteudo: Conteúdo a ser escrito no arquivo.
            sobrescrever: Se True, substitui arquivos existentes. Se False, falha caso o arquivo já exista.
            
        Returns:
            Mensagem formatada com o resultado da operação.
        """
        try:
            # Obter o diretório knowledge
            diretorio_knowledge = self._obter_diretorio_knowledge()
            
            # Construir o caminho completo para a subpasta
            caminho_subpasta = diretorio_knowledge / subpasta
            
            # Garantir que a subpasta exista (criar se necessário)
            caminho_subpasta.mkdir(parents=True, exist_ok=True)
            
            # Caminho completo do arquivo
            caminho_arquivo = caminho_subpasta / nome_arquivo
            
            # Verificar se o arquivo já existe
            if caminho_arquivo.exists() and not sobrescrever:
                return f"""
                ## ❌ Operação cancelada
                
                - **Arquivo**: {nome_arquivo}
                - **Caminho**: {caminho_arquivo}
                - **Status**: Falha - arquivo já existe e a opção 'sobrescrever' está desativada
                - **Ação sugerida**: Defina 'sobrescrever=True' para substituir o arquivo existente ou escolha outro nome
                """
            
            # Escrever o conteúdo no arquivo
            with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
                arquivo.write(conteudo)
            
            # Preparar o caminho relativo para exibição mais limpa
            caminho_relativo = os.path.join('knowledge', subpasta, nome_arquivo)
            
            return f"""
            ## ✅ Arquivo criado com sucesso
            
            - **Arquivo**: {nome_arquivo}
            - **Caminho**: {caminho_relativo}
            - **Tamanho**: {len(conteudo)} caracteres
            - **Status**: Operação concluída com sucesso
            - **Ação**: {'Arquivo sobrescrito' if caminho_arquivo.exists() else 'Novo arquivo criado'}
            """
                
        except Exception as e:
            return f"""
            ## ❌ Erro ao criar arquivo
            
            - **Arquivo**: {nome_arquivo}
            - **Subpasta**: {subpasta}
            - **Erro**: {str(e)}
            - **Sugestão**: Verifique permissões de escrita e se o caminho é válido
            """


if __name__ == "__main__":
    # Exemplo de uso da ferramenta para testes
    ferramenta = KnowledgeFileWriterTool()
    
    # Escolha qual exemplo quer rodar
    exemplo_a_executar = 1  # Mude este número para testar diferentes exemplos
    
    if exemplo_a_executar == 1:
        # Exemplo 1: Criar arquivo em uma subpasta existente
        print("\n=== EXEMPLO 1: Criar arquivo em subpasta existente ===\n")
        resultado = ferramenta._run(
            subpasta="exemplo_teste",
            nome_arquivo="arquivo_teste.md",
            conteudo="# Arquivo de Teste\n\nEste é um arquivo de teste criado pela ferramenta KnowledgeFileWriterTool."
        )
        print(resultado)
    
    elif exemplo_a_executar == 2:
        # Exemplo 2: Criar arquivo em estrutura aninhada de pastas
        print("\n=== EXEMPLO 2: Criar arquivo em estrutura aninhada ===\n")
        resultado = ferramenta._run(
            subpasta="exemplo_teste/subpasta1/subpasta2",
            nome_arquivo="arquivo_aninhado.txt",
            conteudo="Conteúdo do arquivo em uma estrutura aninhada de diretórios."
        )
        print(resultado)
    
    elif exemplo_a_executar == 3:
        # Exemplo 3: Tentar criar um arquivo sem sobrescrever
        print("\n=== EXEMPLO 3: Evitar sobrescrita de arquivo existente ===\n")
        # Primeiro criar o arquivo
        ferramenta._run(
            subpasta="exemplo_teste",
            nome_arquivo="nao_sobrescrever.txt",
            conteudo="Conteúdo original que não deve ser sobrescrito."
        )
        # Depois tentar sobrescrevê-lo com sobrescrever=False
        resultado = ferramenta._run(
            subpasta="exemplo_teste",
            nome_arquivo="nao_sobrescrever.txt",
            conteudo="Este conteúdo não deveria substituir o original.",
            sobrescrever=False
        )
        print(resultado)
    
    # Para executar via comando:
    # python -m crews.pdca.tools.knowledge_file_writer_tool
