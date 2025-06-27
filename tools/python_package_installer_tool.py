from typing import Type, Optional, List, Union
import subprocess
import sys
import re

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator


# Dicionário centralizado de descrições
DESCRIPTIONS = {
    "PythonPackageInstallerInput.pacote": "Nome do pacote Python a ser instalado ou lista de pacotes. Aceita tanto uma string única (ex: 'numpy') quanto uma lista de strings (ex: ['numpy', 'pandas', 'matplotlib']). Cada nome deve conter apenas caracteres alfanuméricos, pontos, hífens e sublinhados.",
    
    "PythonPackageInstallerInput.versao": "Versão específica do pacote (opcional). Exemplos: '==1.0.0', '>=2.0.0', '~=3.1.0'. Se fornecer apenas o número (ex: '2.0.0'), será convertido automaticamente para '==2.0.0'. Se estiver instalando múltiplos pacotes, esta versão será aplicada a todos, a menos que especificada no nome do pacote.",
    
    "PythonPackageInstallerInput.opcoes": "Opções adicionais para pip (opcional). Exemplos: ['--no-cache-dir', '--quiet', '--user']. Estas opções são passadas diretamente para o comando pip install.",
    
    "PythonPackageInstallerTool.description": """Instala um ou mais pacotes Python no ambiente virtual atual usando pip. 
Você pode especificar um único pacote ou uma lista de pacotes, a versão desejada e opções adicionais do pip. 
A ferramenta verifica se está em um ambiente virtual e executa o comando de instalação apropriado, 
retornando um relatório detalhado sobre o resultado da operação. 
Para pacotes múltiplos, você pode fornecer uma lista de nomes no parâmetro 'pacote'."""
}


def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS."""
    return DESCRIPTIONS.get(key, "Descrição não disponível")


class PythonPackageInstallerInput(BaseModel):
    """Input schema para PythonPackageInstallerTool."""
    
    pacote: Union[str, List[str]] = Field(..., description=get_description("PythonPackageInstallerInput.pacote"))
    versao: Optional[str] = Field(None, description=get_description("PythonPackageInstallerInput.versao"))
    opcoes: Optional[List[str]] = Field(None, description=get_description("PythonPackageInstallerInput.opcoes"))
    
    @validator('pacote')
    def validar_nome_pacote(cls, v):
        """Valida o nome do pacote para evitar injeção de comandos."""
        
        # Convertendo string única para lista para processamento uniforme
        pacotes = v if isinstance(v, list) else [v]
        
        # Validando cada pacote na lista
        for pacote in pacotes:
            if not isinstance(pacote, str):
                raise ValueError(f"Nome de pacote inválido: {pacote}. Deve ser uma string.")
            if not re.match(r'^[A-Za-z0-9._-]+$', pacote):
                raise ValueError(f"Nome de pacote inválido: {pacote}. Use apenas letras, números, pontos, hífens e sublinhados.")
        return v
    
    @validator('versao')
    def validar_versao(cls, v):
        """Valida o formato da versão, se fornecida."""
        if v is not None and not re.match(r'^[=<>~!].+$', v):
            return f"=={v}" if re.match(r'^[0-9]', v) else v
        return v


class PythonPackageInstallerTool(BaseTool):
    name: str = "instalador_pacotes_python"
    description: str = get_description("PythonPackageInstallerTool.description")
    args_schema: Type[BaseModel] = PythonPackageInstallerInput

    def _run(self, pacote: Union[str, List[str]], versao: Optional[str] = None, opcoes: Optional[List[str]] = None) -> str:
        """
        Executa a instalação de um ou mais pacotes Python usando pip.
        
        Args:
            pacote: Nome do pacote ou lista de pacotes a serem instalados.
            versao: Versão específica a ser aplicada (opcional).
            opcoes: Opções adicionais para pip (opcional).
            
        Returns:
            Mensagem formatada com o resultado da instalação.
        """
        # Verifica se estamos em um ambiente virtual
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        
        if not in_venv:
            return "Aviso: Nenhum ambiente virtual detectado. A instalação será feita no ambiente Python global."
        
        # Convertendo string única para lista para processamento uniforme
        pacotes = pacote if isinstance(pacote, list) else [pacote]
        
        # Constrói o comando de instalação base
        comando_base = [sys.executable, "-m", "pip", "install"]
        
        # Adiciona opções, se fornecidas
        if opcoes:
            comando_base.extend(opcoes)
        
        resultados = []
        
        # Processa cada pacote
        for pacote_individual in pacotes:
            # Prepara o comando para este pacote específico
            comando = comando_base.copy()
            
            # Adiciona o pacote com versão, se especificada
            pacote_completo = pacote_individual
            if versao and not any(op in pacote_individual for op in ['==', '>=', '<=', '~=', '>', '<']):
                pacote_completo = f"{pacote_individual}{versao}"
            
            comando.append(pacote_completo)
            
            try:
                # Executa o comando de instalação
                resultado = subprocess.run(
                    comando,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # Prepara o relatório para este pacote
                if resultado.returncode == 0:
                    resultados.append(f"""
                    ## Pacote: {pacote_completo}
                    - Status: ✅ Instalado com sucesso
                    - Ambiente: {'Virtual' if in_venv else 'Global'}
                    - Detalhes: {resultado.stdout.strip()[:200]}...
                    """)
                else:
                    resultados.append(f"""
                    ## Pacote: {pacote_completo}
                    - Status: ❌ Falha
                    - Código de erro: {resultado.returncode}
                    - Mensagem de erro: {resultado.stderr.strip()[:200]}...
                    """)
                    
            except Exception as e:
                resultados.append(f"""
                ## Pacote: {pacote_completo}
                - Status: ❌ Erro
                - Detalhes: {str(e)}
                """)
        
        # Monta o relatório completo
        if len(pacotes) == 1:
            return resultados[0]
        else:
            cabecalho = f"# Relatório de Instalação de {len(pacotes)} Pacotes\n\n"
            resumo = []
            
            # Conta sucessos e falhas
            sucessos = sum(1 for r in resultados if "✅" in r)
            falhas = len(pacotes) - sucessos
            
            resumo.append(f"- Total de pacotes: {len(pacotes)}")
            resumo.append(f"- Instalados com sucesso: {sucessos}")
            resumo.append(f"- Falhas: {falhas}\n\n")
            
            return cabecalho + "\n".join(resumo) + "\n\n" + "\n\n".join(resultados)


if __name__ == "__main__":
    # Exemplo de uso da ferramenta para testes
    instalador = PythonPackageInstallerTool()
    
    # Escolha qual exemplo quer rodar (para evitar instalar todos os pacotes de uma vez)
    exemplo_a_executar = 4  # Mude este número para testar diferentes exemplos
    
    if exemplo_a_executar == 1:
        # Exemplo 1: Instalar pacote único sem versão específica
        print("\n=== EXEMPLO 1: Instalação básica de pacote único ===\n")
        resultado = instalador._run(pacote="requests")
        print(resultado)
    
    elif exemplo_a_executar == 2:
        # Exemplo 2: Instalar pacote com versão específica
        print("\n=== EXEMPLO 2: Instalação com versão específica ===\n")
        resultado = instalador._run(pacote="pandas", versao="==1.5.3")
        print(resultado)
    
    elif exemplo_a_executar == 3:
        # Exemplo 3: Instalar pacote com opções adicionais
        print("\n=== EXEMPLO 3: Instalação com opções ===\n")
        resultado = instalador._run(pacote="numpy", opcoes=["--quiet", "--no-cache-dir"])
        print(resultado)
    
    elif exemplo_a_executar == 4:
        # Exemplo 4: Instalar múltiplos pacotes de uma vez
        print("\n=== EXEMPLO 4: Instalação de múltiplos pacotes ===\n")
        resultado = instalador._run(pacote=["requests", "six", "urllib3"])
        print(resultado)
    
    elif exemplo_a_executar == 5:
        # Exemplo 5: Instalar múltiplos pacotes com versão específica
        print("\n=== EXEMPLO 5: Múltiplos pacotes com versão específica ===\n")
        resultado = instalador._run(pacote=["requests", "pandas"], versao="==2.0.0")
        print(resultado)
    
    # Para executar via comando:
    # python -m crews.pdca.tools.python_package_installer_tool
