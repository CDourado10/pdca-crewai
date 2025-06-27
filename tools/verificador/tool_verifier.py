#!/usr/bin/env python
"""
Verificador de ferramentas dinâmicas para CrewAI.

Este módulo fornece uma ferramenta CrewAI para analisar e validar
arquivos .py contendo ferramentas customizadas, focando na compatibilidade
com o framework CrewAI e identificando problemas potenciais antes da execução.
"""

import ast
import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List, Type, Optional, Union

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ToolVerificationInput(BaseModel):
    """Entrada para a ferramenta de verificação."""
    tool_path: str = Field(..., description="Caminho absoluto para o arquivo .py da ferramenta a ser verificada.")


class _ToolAnalysisResult:
    """Classe interna para armazenar os resultados da análise."""
    def __init__(self, tool_path: Union[str, Path]):
        self.tool_path = Path(tool_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.tool_class_name: Optional[str] = None
        self.tool_class: Optional[Type[BaseTool]] = None
        self.ast_tree: Optional[ast.AST] = None
        self.module: Optional[Any] = None
        self.found_args_schema_name: Optional[str] = None
        self.tool_instance: Optional[Any] = None
        self.error_components: set[str] = set()

    def add_error(self, message: str, component: str = None):
        """Adiciona uma mensagem de erro com contexto do componente."""
        if component:
            self.error_components.add(component)
            error_msg = f"ERRO NO COMPONENTE: {component}\n"
            error_msg += "-" * 40 + "\n"
            error_msg += f"Problema: {message}"
            self.errors.append(error_msg)
        else:
            self.errors.append(f"ERRO: {message}")

    def add_warning(self, message: str, component: str = None):
        """Adiciona uma mensagem de aviso com contexto do componente."""
        if component:
            warning_msg = f"AVISO NO COMPONENTE: {component}\n"
            warning_msg += "-" * 40 + "\n"
            warning_msg += f"Atenção: {message}\n"
            self.warnings.append(warning_msg)
        else:
            self.warnings.append(f"AVISO: {message}")

    def add_info(self, message: str):
        """Adiciona uma mensagem informativa (apenas para debug)."""
        self.info.append(f"INFO: {message}")

    def _format_report(self) -> str:
        """Formata os resultados em um relatório textual.
           Mantido para possível log interno, mas não será o retorno principal.
        """
        report_lines = [f"## Relatório de Verificação: {self.tool_path.name}"]

        if not self.errors and not self.warnings:
            status_header = "**Status: APROVADO (com ressalvas)**"
            status_desc = ["   A verificação estática e de importação foi concluída sem erros ou avisos críticos.",
                           "   A instanciação não foi testada ou falhou (ver avisos), mas a estrutura parece válida."]
        elif not self.errors:
            status_header = "**Status: APROVADO COM AVISOS**"
            status_desc = ["   A ferramenta passou nas verificações essenciais, mas há avisos a serem considerados."]
        else:
            status_header = "**Status: FALHA**"
            status_desc = ["   Foram encontrados erros críticos que impedem o uso seguro da ferramenta."]

        report_lines.append(status_header)
        report_lines.extend(status_desc)

        if self.tool_class_name:
            report_lines.append(f"**Classe da Ferramenta Identificada:** `{self.tool_class_name}`")
        else:
            report_lines.append("**Classe da Ferramenta:** Nenhuma classe terminando com 'Tool' foi encontrada.")

        if self.info:
            report_lines.append("### Informações:")
            report_lines.extend(self.info)

        if self.warnings:
            report_lines.append("### Avisos:")
            report_lines.extend(self.warnings)

        if self.errors:
            report_lines.append("### Erros Críticos:")
            report_lines.extend(self.errors)

        report_lines.append("### Próximos Passos:")
        if not self.errors:
            report_lines.extend([
                "- Revise os avisos (se houver).",
                "- Realize testes funcionais da ferramenta com dados reais.",
                "- Se a instanciação falhou (ver avisos), investigue possíveis problemas de inicialização ou dependências."
            ])
        else:
            report_lines.extend([
                "- Corrija os erros críticos listados.",
                "- Execute a verificação novamente após as correções."
            ])

        return "\n".join(report_lines)


class ToolVerifierTool(BaseTool):
    """
    Verifica arquivos de ferramentas CrewAI (.py) buscando por conformidade
    estrutural e potenciais problemas antes da execução real.
    Foca na análise estática (AST) e na inspeção pós-importação.
    """
    name: str = "Verificador de Arquivos de Ferramenta CrewAI"
    description: str = (
        "Analisa um arquivo .py de ferramenta CrewAI para verificar sua estrutura, "
        "presença de elementos necessários (nome, descrição, args_schema, _run), "
        "e tenta importá-lo para identificar problemas básicos de código. "
        "Não garante funcionalidade completa, mas ajuda a pegar erros comuns."
    )
    args_schema: Type[BaseModel] = ToolVerificationInput
    model_config = {'arbitrary_types_allowed': True}

    # Método _run é obrigatório pela BaseTool
    def _run(self, tool_path: str) -> Dict[str, Any]:
        """Interface obrigatória para BaseTool. Chama a lógica principal em run()."""
        # Chama o método run principal, que já lida com a lógica e retorna o dict
        return self.run(tool_path=tool_path)

    def run(self, tool_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Executa a verificação completa da ferramenta e retorna um dicionário de resultados."""
        # Lidar com possíveis chamadas via kwargs (comuns no CrewAI)
        if tool_path is None:
            tool_path = kwargs.get('tool_path')
            if tool_path is None:
                return {
                    "sucesso": False,
                    "erros": [" ERRO: Argumento 'tool_path' não fornecido."],
                    "avisos": [],
                    "infos": [],
                    "tool_path": None,
                    "tool_class_name": None
                }

        res = _ToolAnalysisResult(tool_path)
        res.add_info(f"Iniciando verificação para: {res.tool_path}")

        # 1. Verificar existência do arquivo
        if not res.tool_path.exists():
            res.add_error(f"Arquivo não encontrado: {res.tool_path}")
            return self._build_result_dict(res)
        if not res.tool_path.is_file() or res.tool_path.suffix != '.py':
            res.add_error(f"O caminho fornecido não é um arquivo .py válido: {res.tool_path}")
            return self._build_result_dict(res)

        # 2. Análise AST (Sintaxe e Estrutura Básica)
        if not self._verify_ast(res):
            return self._build_result_dict(res) # Erro crítico na AST impede continuação

        # 3. Tentativa de Importação e Inspeção
        self._verify_import_and_inspect(res)

        # 4. Verificação da Instância (se a inspeção foi bem-sucedida)
        if res.tool_class:
            self._verify_instance(res)
            # A verificação da instância adiciona erros/avisos, mas não interrompe o fluxo aqui
            # pois queremos reportar todos os problemas encontrados.

        # 5. Verificação do Args Schema (somente se a instância foi criada com sucesso)
        if res.tool_instance:
            self._verify_args_schema(res)
        else:
            # Adiciona aviso se a instância não pôde ser criada, impedindo a verificação do schema
            res.add_warning("Verificação do args_schema pulada pois a instância da ferramenta não pôde ser criada.")

        if not res.errors and not res.warnings:
            res.add_info("Verificação concluída sem erros ou avisos críticos.")
        elif not res.errors:
            res.add_warning("Verificação concluída com avisos.")
        else:
            res.add_error("Verificação concluída com erros críticos.")

        res.add_info(f"Verificação finalizada para: {res.tool_path}")

        # Log interno (opcional)
        # print(res._format_report())

        return self._build_result_dict(res)

    def _build_result_dict(self, res: _ToolAnalysisResult) -> Dict[str, Any]:
        """Constrói o dicionário de resultados final."""
        return {
            "sucesso": not res.errors, # Sucesso significa sem erros críticos
            "erros": res.errors,
            "avisos": res.warnings,
            "infos": res.info,
            "tool_path": str(res.tool_path),
            "tool_class_name": res.tool_class_name
        }

    def _verify_ast(self, res: _ToolAnalysisResult) -> bool:
        """Verifica erros de sintaxe e estrutura básica via AST."""
        res.add_info("Analisando AST para erros de sintaxe e estrutura")
        try:
            source_code = res.tool_path.read_text(encoding='utf-8')
            res.ast_tree = ast.parse(source_code)
            res.add_info("Sintaxe do arquivo Python válida")
        except SyntaxError as e:
            # Extrair contexto do erro
            linhas = source_code.split('\n')
            inicio = max(0, e.lineno - 3)
            fim = min(len(linhas), e.lineno + 2)
            contexto = linhas[inicio:fim]
            
            # Identificar o componente com erro
            componente = self._identificar_componente_com_erro(source_code, e.lineno)
            
            componente_nome, componente_descricao = componente
            
            # Mensagem de erro extremamente simplificada
            parte1 = f"Erro de sintaxe na linha {e.lineno}: {e.msg}"
            parte2 = f"Componente: {componente_nome}"
            
            # Criar mensagem em partes para evitar problemas de formatação
            res.add_error(parte1)
            res.add_error(parte2)
            
            # Adicionar contexto da linha com erro de forma segura
            if contexto and 0 <= e.lineno - inicio - 1 < len(contexto):
                linha_com_erro = contexto[e.lineno - inicio - 1].strip()
                if len(linha_com_erro) > 30:  # Limitar o tamanho da linha
                    linha_com_erro = linha_com_erro[:27] + "..."
                res.add_error(f"Código: {linha_com_erro}")
                
                # Adicionar sugestão de correção com base no erro
                if e.msg == "expected ':'":
                    res.add_error("Sugestão: Adicione dois pontos (:) ao final da linha")
                elif "unexpected EOF" in e.msg:
                    res.add_error("Sugestão: Verifique parênteses/colchetes não fechados")
                elif "unexpected indent" in e.msg:
                    res.add_error("Sugestão: Corrija a indentação da linha")
                else:
                    res.add_error("Sugestão: Verifique a sintaxe Python na linha")
            
            return False
        except Exception as e:
            res.add_error(f"Erro ao ler ou parsear o arquivo: {e}\n{traceback.format_exc()}")
            return False

        # Procurar classe da ferramenta na AST
        found_tool_class_ast = False
        for node in ast.walk(res.ast_tree):
            if isinstance(node, ast.ClassDef) and node.name.endswith("Tool"):
                res.tool_class_name = node.name
                res.add_info(f"Classe AST encontrada: {node.name}")
                found_tool_class_ast = True
                
                # Verificar herança básica
                base_names = [b.id for b in node.bases if isinstance(b, ast.Name)]
                if "BaseTool" not in base_names:
                    res.add_warning(
                        "AVISO DE HERANÇA\n" +
                        "-" * 20 + "\n" +
                        f"Classe: {node.name}\n" +
                        "Problema: Não herda diretamente de 'BaseTool'\n" +
                        "Ação: Verifique se a classe herda corretamente de 'BaseTool'\n" +
                        "Exemplo:\n" +
                        "class MinhaFerramenta(BaseTool):\n" +
                        "    ..."
                    )
                else:
                    res.add_info("Herança de BaseTool verificada na AST.")

                # Verificar método _run
                run_method = next((item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == '_run'), None)
                if not run_method:
                    res.add_error(
                        "ERRO NO MÉTODO _run\n" +
                        "-" * 20 + "\n" +
                        f"Classe: {node.name}\n" +
                        "Problema: Método '_run' não encontrado\n" +
                        "Ação: Adicione o método '_run' à classe\n" +
                        "Exemplo:\n" +
                        "    def _run(self, param1: str, param2: int = 0) -> dict:\n" +
                        "        return {'resultado': 'processado'}"
                    )
                else:
                    res.add_info("Método '_run' encontrado na AST.")

                break

        if not found_tool_class_ast:
            res.add_error(
                "ERRO NA ESTRUTURA DA CLASSE\n" +
                "-" * 20 + "\n" +
                "Problema: Nenhuma classe terminando com 'Tool' foi encontrada\n" +
                "Ação: Crie uma classe que herde de BaseTool e termine com 'Tool'\n" +
                "Exemplo:\n" +
                "class MinhaFerramenta(BaseTool):\n" +
                "    name = 'Minha Ferramenta'\n" +
                "    description = 'Descrição da ferramenta'"
            )
            return False

        return True

    def _identificar_componente_com_erro(self, source_code: str, linha_erro: int) -> tuple[str, str]:
        """Identifica em qual componente da ferramenta o erro ocorreu.
        
        Args:
            source_code: Código fonte completo do arquivo
            linha_erro: Número da linha onde o erro ocorreu
            
        Returns:
            Tupla com (nome do componente, parâmetro do DynamicToolCreator)
            Ex: ('Método _run', 'implementation')
        """
        # Mapeamento de componentes para parâmetros do DynamicToolCreator
        MAPEAMENTO_COMPONENTES = {
            'Método _run': 'implementação do método _run',
            'Atributos da Classe': 'definição dos atributos da classe',
            'Schema de Entrada': 'definição dos parâmetros',
            'Herança de Classe': 'estrutura da classe',
            'Estrutura Python': 'sintaxe Python',
            'Imports': 'importações',
            'Métodos Customizados': 'métodos personalizados'
        }
        
        linhas = source_code.split('\n')
        linha_atual = linha_erro - 1  # 0-based index
        
        # Procura por padrões comuns acima da linha de erro
        linha_atual_str = linhas[linha_atual].strip()
        componente = None
        
        # Verifica componentes comuns
        if '_run' in ''.join(linhas[max(0, linha_atual-5):min(len(linhas), linha_atual+5)]):
            componente = 'Método _run'
        elif 'class' in linha_atual_str and ('Tool' in linha_atual_str or 'BaseTool' in linha_atual_str):
            componente = 'Herança de Classe'
        elif 'BaseModel' in linha_atual_str or any('Field(' in linha for linha in linhas[max(0, linha_atual-5):min(len(linhas), linha_atual+5)]):
            componente = 'Schema de Entrada'
        elif any(attr in linha_atual_str for attr in ['name', 'description', 'args_schema']):
            componente = 'Atributos da Classe'
        elif 'import' in linha_atual_str.lower() or 'from' in linha_atual_str.lower():
            componente = 'Imports'
        elif 'def' in linha_atual_str and '_run' not in linha_atual_str:
            componente = 'Métodos Customizados'
        else:
            componente = 'Estrutura Python'
        
        return (componente, MAPEAMENTO_COMPONENTES[componente])

    def _check_for_class_attributes(self, node: ast.ClassDef, res: _ToolAnalysisResult):
        """Verifica a presença de atributos de classe (name, description, args_schema) via AST."""
        required_attrs = {'name': False, 'description': False, 'args_schema': False}
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name) and item.target.id in required_attrs:
                    required_attrs[item.target.id] = True
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id in required_attrs:
                        required_attrs[target.id] = True

        # Reportar atributos ausentes
        for attr, found in required_attrs.items():
            if not found:
                # Aviso em vez de erro, pois a verificação na instância é mais confiável
                res.add_warning(f"Atributo de classe '{attr}' não detectado estaticamente via AST. Será verificado na instância.")
            else:
                res.add_info(f"Atributo de classe '{attr}' encontrado na AST.")

    def _verify_import_and_inspect(self, res: _ToolAnalysisResult):
        """Tenta importar o módulo e inspecionar a classe."""
        if not res.tool_class_name: # Se a AST não encontrou, não tenta importar
            res.add_warning("Importação pulada: Nenhuma classe de ferramenta foi encontrada na AST.")
            return

        res.add_info(f"Tentando importar dinamicamente o módulo: {res.tool_path.stem}")
        try:
            module_name = res.tool_path.stem
            spec = importlib.util.spec_from_file_location(module_name, res.tool_path)
            if spec is None or spec.loader is None:
                res.add_error(f"Falha ao criar spec de importação para {module_name}.")
                return

            res.module = importlib.util.module_from_spec(spec)
            # Adicionar diretório pai ao sys.path temporariamente pode ajudar com imports relativos
            original_sys_path = sys.path[:]
            parent_dir = str(res.tool_path.parent.resolve())
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)

            # Isolar a execução do módulo para evitar poluir o namespace principal
            # e capturar exceções durante a execução do código no nível do módulo
            try:
                spec.loader.exec_module(res.module)
                res.add_info("Módulo importado com sucesso.")
            except Exception as e_exec:
                res.add_error(f"Erro durante a execução do código do módulo (nível superior): {e_exec}\n{traceback.format_exc()}")
                # Não prosseguir com a inspeção se o módulo falhou ao carregar
                if parent_dir in sys.path:
                    sys.path.remove(parent_dir) # Limpa o sys.path modificado
                return
            finally:
                # Restaurar sys.path se foi modificado
                if parent_dir in sys.path and parent_dir not in original_sys_path:
                    sys.path.remove(parent_dir)


            # Inspecionar o módulo carregado
            found_class_in_module = False
            for name, obj in inspect.getmembers(res.module):
                if name == res.tool_class_name and inspect.isclass(obj):
                    if not issubclass(obj, BaseTool):
                        continue

                    res.add_info(f"Encontrada classe '{name}' herdando de BaseTool.")
                    found_class_in_module = True
                    res.tool_class = obj # Armazena a classe encontrada

                    # Verificar se _run existe e é callable
                    if not hasattr(obj, "_run") or not callable(getattr(obj, "_run")):
                        res.add_error(f"Método '_run' não encontrado ou não é chamável na classe '{name}' carregada.")
                    else:
                        res.add_info("Método '_run' encontrado e chamável via inspeção.")

                    break # Encontrou a classe esperada

            if not found_class_in_module:
                res.add_error(f"Classe '{res.tool_class_name}' (encontrada na AST) não foi encontrada no módulo importado.")

        except ImportError as e:
            res.add_error(f"Erro de importação ao carregar o módulo ou suas dependências: {e}\n{traceback.format_exc()}")
        except Exception as e:
            res.add_error(f"Erro inesperado durante a importação ou inspeção: {e}\n{traceback.format_exc()}")

    def _verify_instance(self, res: _ToolAnalysisResult):
        """Tenta instanciar a ferramenta, tratando erros comuns como avisos."""
        if not res.tool_class: # Não tenta se a classe não foi carregada
            res.add_info("Instanciação pulada devido a classe não carregada.")
            return

        res.add_info(f"Tentando instanciar '{res.tool_class_name}'...")
        try:
            instance = res.tool_class()
            res.add_info("Instanciação da ferramenta bem-sucedida.")
            res.tool_instance = instance # Armazena a instância

            # Verificar atributos na instância
            if not hasattr(instance, "name") or not isinstance(getattr(instance, "name", None), str):
                res.add_error(f"Atributo 'name' (string) não encontrado na INSTÂNCIA de '{res.tool_class_name}'.")
            else:
                res.add_info(f"Atributo 'name' encontrado na instância: '{instance.name}'.")

            if not hasattr(instance, "description") or not isinstance(getattr(instance, "description", None), str):
                res.add_error(f"Atributo 'description' (string) não encontrado na INSTÂNCIA de '{res.tool_class_name}'.")
            else:
                res.add_info("Atributo 'description' encontrado na instância.") # Não logar a descrição inteira

            if not hasattr(instance, "args_schema"):
                res.add_error("Atributo 'args_schema' não encontrado na instância da ferramenta.")
            elif not inspect.isclass(instance.args_schema) or not issubclass(instance.args_schema, BaseModel):
                res.add_error(f"Atributo 'args_schema' na INSTÂNCIA de '{res.tool_class_name}' não é uma subclasse de pydantic.BaseModel.")
            else:
                res.add_info(f"Atributo 'args_schema' encontrado na instância: {instance.args_schema.__name__}.")

        except Exception as e:
            # Captura erros durante a instanciação (ex: __init__ faltando args, etc.)
            res.add_error(f"Falha na instanciação: {e}\n{traceback.format_exc()}")

    def _verify_args_schema(self, res: _ToolAnalysisResult):
        """Verifica se o args_schema na INSTÂNCIA é um Pydantic Model válido."""
        # Esta verificação agora depende da INSTÂNCIA ter sido criada com sucesso.
        # A checagem se 'res.tool_instance' existe é feita ANTES de chamar este método.
        # A checagem se 'args_schema' existe na instância já foi feita por _verify_instance.

        args_schema = getattr(res.tool_instance, 'args_schema', None) # Pega da instância

        # Se chegou aqui, a instância existe. Verificamos se args_schema é um tipo BaseModel válido.
        if not args_schema or not isinstance(args_schema, type) or not issubclass(args_schema, BaseModel):
             # O erro já deve ter sido adicionado por _verify_instance se o atributo estava ausente ou do tipo errado.
             # Adicionamos um aviso aqui caso algo muito estranho tenha acontecido.
             if not any("args_schema" in error for error in res.errors): # Evita duplicar erros
                res.add_warning(f"Atributo 'args_schema' na instância é inesperadamente inválido (type={type(args_schema)}) apesar de ter passado na verificação inicial.")
             return

        res.add_info(f"Verificando a validade do Pydantic Model: {args_schema.__name__}")
        try:
            # Tenta obter o schema JSON para verificar se é um modelo Pydantic válido
            schema = args_schema.model_json_schema()
            if not schema or 'properties' not in schema:
                # Considerar se um schema sem propriedades é um erro ou aviso. Por ora, aviso.
                res.add_warning(f"O schema Pydantic '{args_schema.__name__}' parece vazio ou inválido (sem propriedades definidas).")
            else:
                res.add_info(f"Schema Pydantic '{args_schema.__name__}' parece válido.")
        except Exception as e:
            res.add_error(f"Erro ao validar o Pydantic Model '{args_schema.__name__}': {e}\n{traceback.format_exc()}")

# Bloco para execução direta do verificador
if __name__ == "__main__":
    import sys
    import json # Para imprimir o dicionário de forma legível

    if len(sys.argv) > 1:
        tool_file_path = sys.argv[1]
        print(f"Executando verificação direta para: {tool_file_path}")
        verifier_tool = ToolVerifierTool()
        # A ferramenta run() agora retorna um dicionário
        report_dict = verifier_tool.run(tool_path=tool_file_path)
        print("\n"+"="*30 + " RESULTADO (DICIONÁRIO) " + "="*30)
        # Imprime o dicionário formatado como JSON para melhor leitura
        print(json.dumps(report_dict, indent=4, ensure_ascii=False))
        print("="*72)
    else:
        print("Uso: python crews/pdca/tools/verificador/tool_verifier.py <caminho_para_arquivo_da_ferramenta.py>")
        print("Exemplo:")
        print("python crews/pdca/tools/verificador/tool_verifier.py crews/pdca/tools/loganalyzer_tool/loganalyzer_tool.py")
