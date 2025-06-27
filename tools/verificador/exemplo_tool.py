#!/usr/bin/env python
"""
Exemplo de ferramenta CrewAI para testar o verificador.
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "ExemploToolInput.mensagem": "Mensagem a ser processada",
    "ExemploToolInput.repeticoes": "Número de vezes para repetir a mensagem",
    "ExemploTool.description": "Uma ferramenta simples para testar o verificador de ferramentas."
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")


class ExemploToolInput(BaseModel):
    """Schema de entrada para a ferramenta de exemplo."""
    mensagem: str = Field(..., description=get_description("ExemploToolInput.mensagem"))
    repeticoes: int = Field(default=1, description=get_description("ExemploToolInput.repeticoes"))


class ExemploTool(BaseTool):
    """Ferramenta de exemplo para testar o verificador."""
    name: str = "Ferramenta de Exemplo"
    description: str = get_description("ExemploTool.description")
    args_schema: type[BaseModel] = ExemploToolInput

    def _run(self, mensagem: str, repeticoes: int = 1) -> str:
        """Executa a ferramenta de exemplo."""
        return mensagem * repeticoes
