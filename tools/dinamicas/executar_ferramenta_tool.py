from typing import Type, Dict, Any
import os
import sys
import importlib.util
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Adicionar diretório raiz do projeto ao sys.path
project_root = str(Path(__file__).parent.parent.parent.parent.parent.absolute())
sys.path.append(project_root)

# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "ExecutarFerramentaToolInput.caminho_ferramenta": "Caminho absoluto ou relativo para o arquivo Python da ferramenta a ser executada (ex: 'crews/pdca/tools/exemplo_dinamico/ferramentaexemplo_tool.py').",
    "ExecutarFerramentaToolInput.nome_classe": "Nome da classe da ferramenta a ser instanciada (ex: 'FerramentaExemploTool').",
    "ExecutarFerramentaToolInput.parametros": "Dicionário com os parâmetros a serem passados para a ferramenta, no formato {'nome_parametro': valor}.",
    "ExecutarFerramentaTool.description": "Ferramenta universal para execução dinâmica de qualquer ferramenta CrewAI existente no sistema. Permite que um agente utilize funcionalidades de ferramentas sem precisar ter acesso direto a elas. Possibilita composição de ferramentas, testes dinâmicos, integração entre diferentes domínios e execução de ferramentas criadas em tempo de execução. Forneça o caminho do arquivo, o nome da classe e os parâmetros necessários para invocar qualquer ferramenta disponível no ecossistema."
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")


class ExecutarFerramentaToolInput(BaseModel):
    """Esquema de entrada para a ferramenta ExecutarFerramentaTool."""

    caminho_ferramenta: str = Field(
        ..., 
        description=get_description("ExecutarFerramentaToolInput.caminho_ferramenta")
    )
    
    nome_classe: str = Field(
        ..., 
        description=get_description("ExecutarFerramentaToolInput.nome_classe")
    )
    
    parametros: Dict[str, Any] = Field(
        default={}, 
        description=get_description("ExecutarFerramentaToolInput.parametros")
    )


class ExecutarFerramentaTool(BaseTool):
    name: str = "Executar Ferramenta"
    description: str = get_description("ExecutarFerramentaTool.description")
    args_schema: Type[BaseModel] = ExecutarFerramentaToolInput

    def _run(
        self, 
        caminho_ferramenta: str, 
        nome_classe: str, 
        parametros: Dict[str, Any] = {}
    ) -> str:
        try:
            # Lista de possíveis caminhos para tentar
            caminhos_possiveis = [
                caminho_ferramenta,  # Primeiro, tenta exatamente como foi passado
            ]
            
            # Se for um caminho relativo, adiciona outras possibilidades
            if not os.path.isabs(caminho_ferramenta):
                # 1. Relativo ao project_root
                caminhos_possiveis.append(os.path.join(project_root, caminho_ferramenta))
                
                # 2. Se o caminho começa com "crews/", tenta encontrar a partir do diretório atual
                if caminho_ferramenta.startswith("crews/") or caminho_ferramenta.startswith("crews\\"):
                    # Buscar recursivamente um diretório 'crews' acima do diretório atual
                    dir_atual = os.path.abspath(os.getcwd())
                    while dir_atual and os.path.basename(dir_atual) != "crews":
                        parent = os.path.dirname(dir_atual)
                        if parent == dir_atual:  # Chegou na raiz sem encontrar
                            break
                        dir_atual = parent
                    
                    # Se encontrou um diretório 'crews', usa-o como base
                    if os.path.basename(dir_atual) == "crews":
                        parte_relativa = caminho_ferramenta[6:] if caminho_ferramenta.startswith("crews/") else caminho_ferramenta[7:]
                        caminhos_possiveis.append(os.path.join(dir_atual, parte_relativa))
            
            # Tentar cada caminho possível até encontrar um válido
            caminho_valido = None
            for caminho in caminhos_possiveis:
                if os.path.exists(caminho):
                    caminho_valido = caminho
                    break
            
            if not caminho_valido:
                return f"ERRO: O arquivo não foi encontrado em nenhum dos caminhos tentados:\n{chr(10).join(caminhos_possiveis)}"
            
            # Carregar o módulo dinamicamente
            spec = importlib.util.spec_from_file_location(
                "modulo_dinamico", caminho_valido
            )
            if not spec or not spec.loader:
                return f"ERRO: Não foi possível carregar o módulo do arquivo {caminho_valido}."
            
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            # Verificar se a classe existe no módulo
            if not hasattr(modulo, nome_classe):
                return f"ERRO: A classe {nome_classe} não foi encontrada no módulo {caminho_valido}."
            
            # Obter a classe e criar uma instância
            classe_ferramenta = getattr(modulo, nome_classe)
            ferramenta = classe_ferramenta()
            
            # Verificar se a ferramenta tem o método run
            if not hasattr(ferramenta, "run") or not callable(getattr(ferramenta, "run")):
                return f"ERRO: A classe {nome_classe} não possui um método 'run' executável."  
            
            # Executar a ferramenta com os parâmetros fornecidos
            resultado = ferramenta.run(**parametros)
            
            return f"""
## Execução de Ferramenta: {nome_classe}

**Caminho:** {caminho_ferramenta}
**Parâmetros utilizados:** {parametros}

### Resultado da execução:
{resultado}
"""
        except Exception as e:
            return f"""
## ERRO na Execução de Ferramenta

**Ferramenta:** {nome_classe}
**Caminho:** {caminho_ferramenta}
**Parâmetros tentados:** {parametros}

### Detalhes do erro:
```
{str(e)}
```

Verifique se:
1. O caminho está correto
2. A classe existe e herda de BaseTool
3. Os parâmetros fornecidos correspondem aos esperados pela ferramenta
"""


if __name__ == "__main__":
    # Demonstração ousada: executando a ferramenta ExecutarFerramentaTool para executar
    # a ferramenta CrewExecutor, que por sua vez executará a equipe PlanejarCrew
    
    print("=== Demonstração em Cascata de Ferramentas ===\n")
    print("1. ExecutarFerramentaTool -> 2. CrewExecutor -> 3. PlanejarCrew\n")
    
    # Criar instância da ferramenta
    executar_tool = ExecutarFerramentaTool()
    
    # Exemplo de inputs para a equipe PlanejarCrew
    planejar_inputs = {
        "problema": "Necessidade de otimizar o processo de criação de ferramentas no sistema CrewAI",
        "contexto": "Sistema baseado em CrewAI com múltiplas equipes e agentes interagindo",
        "restricoes": "Manter compatibilidade com a arquitetura atual e minimizar dependências externas",
        "recursos_disponiveis": "Equipe de desenvolvimento, documentação do CrewAI, ferramentas existentes",
        "prazo": "2 semanas",
        "objetivo_principal": "Simplificar e acelerar o processo de criação de novas ferramentas para agentes"
    }
    
    # Preparar parâmetros para o CrewExecutor
    crew_executor_params = {
        "crew_path": "crews.pdca.planejar.planejar_crew",
        "crew_class": "PlanejarCrew",
        "inputs": planejar_inputs,
        "verbose": True
    }
    
    try:
        # Executar a ferramenta ExecutarFerramentaTool, que executará o CrewExecutor,
        # que por sua vez executará a PlanejarCrew
        resultado = executar_tool.run(
            caminho_ferramenta="crews/pdca/tools/dinamicas/crew_executor.py",
            nome_classe="CrewExecutor",
            parametros=crew_executor_params
        )
        
        # Exibir o resultado
        print("\n=== Resultado da Execução ===\n")
        print(resultado)
        
    except Exception as e:
        print(f"\n=== ERRO NA DEMONSTRAÇÃO ===\n{str(e)}")
