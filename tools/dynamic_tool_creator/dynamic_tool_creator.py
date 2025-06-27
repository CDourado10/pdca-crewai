#!/usr/bin/env python
"""
Criador dinâmico de ferramentas.

Este módulo permite criar ferramentas dinamicamente a partir de descrições,
parâmetros e código de execução.
"""

import ast
import astor
from typing import Dict, List, Any, Optional, Type, Union
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from pathlib import Path

# Importação absoluta para evitar problemas quando executado diretamente
try:
    from crews.pdca.tools.verificador import ToolVerifierTool
    from crews.pdca.tools.executar_ferramenta import ExecutarFerramentaTool
except ImportError:
    # Fallback para caso de falha na importação
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))
    from crews.pdca.tools.verificador import ToolVerifierTool
    from crews.pdca.tools.executar_ferramenta import ExecutarFerramentaTool

# Obter caminho raiz do projeto
project_root = str(Path(__file__).parent.parent.parent.parent.parent.absolute())

# Dicionário de descrições para substituir a função get_description
DESCRIPTIONS = {
    "ToolParameter.name": "Nome identificador único do parâmetro que será visível para o agente ao utilizar a ferramenta. Use nomes claros e descritivos que comuniquem a função do parâmetro (ex: 'caminho_arquivo', 'nivel_filtro').",
    
    "ToolParameter.type": "Tipo de dado do parâmetro que define como o agente deve formatá-lo. Opções: 'string' (texto), 'integer' (número inteiro), 'boolean' (verdadeiro/falso), 'array' (lista), 'object' (dicionário). O tipo correto garante validação adequada.",
    
    "ToolParameter.description": "Descrição detalhada que o agente verá ao consultar a ferramenta. Deve explicar claramente o propósito do parâmetro, incluir exemplos de valores válidos, restrições e impacto no funcionamento da ferramenta. Esta descrição é crucial para que o agente entenda como usar o parâmetro corretamente.",
    
    "ToolParameter.required": "Define se o parâmetro é obrigatório (True) ou opcional (False). Parâmetros obrigatórios devem sempre ser fornecidos pelo agente, enquanto opcionais podem usar valores padrão.",
    
    "ToolParameter.default": "Valor padrão usado quando o parâmetro é opcional (required=False) e o agente não fornece um valor. Deve ser compatível com o tipo definido e representar um valor sensato para uso comum da ferramenta.",
    
    "ToolDefinition.name": "Nome da ferramenta que será exibido para o agente. Deve ser conciso, descritivo e comunicar claramente a função principal da ferramenta (ex: 'LogAnalyzer', 'DataExtractor'). Este nome será usado na interface do agente e na documentação gerada.",
    
    "ToolDefinition.description": "Descrição completa da ferramenta que o agente verá ao consultar as ferramentas disponíveis. Deve explicar detalhadamente o propósito, capacidades e casos de uso da ferramenta. Esta descrição é fundamental para que o agente entenda quando e como utilizar a ferramenta para resolver problemas específicos.",
    
    "ToolDefinition.parameters": "Lista de parâmetros que a ferramenta aceita, definindo a interface que o agente utilizará para interagir com a ferramenta. Cada parâmetro deve incluir nome, tipo, descrição e indicação se é obrigatório, permitindo que o agente forneça os dados corretos no formato esperado.",
    
    "ToolDefinition.implementation": "Código Python que será executado quando o agente chamar a ferramenta. Este código será inserido dentro do método `_run()` e receberá automaticamente todos os parâmetros definidos na lista 'parameters'. IMPORTANTE PARA AGENTES: (1) Use preferencialmente o padrão de método auxiliar; (2) Para lógica complexa, utilize custom_methods; (3) NÃO inclua a definição 'def _run(...)'. Exemplo: 'return self.processar_api(url, formato)'",
    
    "ToolDefinition.imports": "Lista de importações necessárias para o funcionamento da ferramenta, como bibliotecas externas ou módulos internos. Exemplo: ['import os', 'from datetime import datetime']. Estas importações serão incluídas no topo do arquivo da ferramenta gerada.",
    
    "ToolDefinition.custom_methods": "Lista de métodos auxiliares completos que serão adicionados à classe da ferramenta e podem ser chamados pelo método _run. RECOMENDADO PARA AGENTES: Coloque toda lógica complexa nestes métodos auxiliares e mantenha o implementation simples. Formato esperado: ['def metodo1(self, param1, param2):\n    \"\"\"Docstring\"\"\"\n    # Lógica aqui\n    return resultado', 'def metodo2(self, param1):\n    # Outro método']. Cada string deve conter um método completo com indentação correta.",
    
    "DynamicToolCreator.description": "Ferramenta para criar novas ferramentas CrewAI em tempo de execução, expandindo dinamicamente as capacidades dos agentes. Permite definir o nome, descrição, parâmetros e implementação da nova ferramenta, gerando automaticamente o código necessário e validando sua estrutura. A ferramenta criada segue as melhores práticas do CrewAI, com interface clara para os agentes, validação de parâmetros e retorno de resultados em formato semântico compreensível. Ideal para equipes que precisam adicionar novas funcionalidades específicas durante a execução do fluxo de trabalho."
}

# Função para obter descrições do dicionário local
def get_description(key: str) -> str:
    """Retorna a descrição para a chave especificada do dicionário local."""
    return DESCRIPTIONS.get(key, f"Descrição para {key} não encontrada")

# Função simplificada para registrar uso da ferramenta (apenas para logging)
def register_tool_usage(tool_name: str, params: Dict[str, Any], metadata: Dict[str, Any] = None):
    """Registra o uso da ferramenta (versão simplificada que apenas imprime informações)."""
    print(f"Ferramenta {tool_name} utilizada com parâmetros: {params}")
    if metadata:
        print(f"Metadados: {metadata}")

class ToolParameter(BaseModel):
    """Definição de um parâmetro para uma ferramenta."""
    name: str = Field(
        ...,
        description=get_description("ToolParameter.name")
    )
    type: str = Field(
        ...,
        description=get_description("ToolParameter.type")
    )
    description: str = Field(
        ...,
        description=get_description("ToolParameter.description")
    )
    required: bool = Field(
        default=True,
        description=get_description("ToolParameter.required")
    )
    default: Optional[Any] = Field(
        default=None,
        description=get_description("ToolParameter.default")
    )

class ToolDefinition(BaseModel):
    """Especificação para criar uma nova ferramenta no CrewAI."""
    name: str = Field(
        ...,
        description=get_description("ToolDefinition.name")
    )
    description: str = Field(
        ...,
        description=get_description("ToolDefinition.description")
    )
    parameters: List[Union[Dict[str, Any], "ToolParameter"]] = Field(
        default=[],
        description=get_description("ToolDefinition.parameters")
    )       
    implementation: str = Field(
        ...,
        description=get_description("ToolDefinition.implementation")
    )
    imports: List[str] = Field(
        default=[],
        description=get_description("ToolDefinition.imports")
    )
    custom_methods: List[str] = Field(
        default=[],
        description=get_description("ToolDefinition.custom_methods")
    )

class ToolASTBuilder:
    """Construtor de AST para ferramentas do CrewAI."""
    def __init__(self, tool_def: ToolDefinition):
        # Converter os parâmetros de dict para ToolParameter se necessário
        converted_parameters = []
        for param in tool_def.parameters:
            if isinstance(param, dict):
                # Converter dict para ToolParameter
                converted_param = ToolParameter(
                    name=param.get('name', ''),
                    type=param.get('type', 'string'),
                    description=param.get('description', 'Parâmetro sem descrição'),
                    required=param.get('required', True),
                    default=param.get('default')
                )
                converted_parameters.append(converted_param)
            else:
                # Se já for ToolParameter, manter como está
                converted_parameters.append(param)
        
        # Criar uma cópia da definição com os parâmetros convertidos
        self.tool_def = ToolDefinition(
            name=tool_def.name,
            description=tool_def.description,
            parameters=converted_parameters,  # Usar os parâmetros convertidos
            implementation=tool_def.implementation,
            imports=tool_def.imports,
            custom_methods=tool_def.custom_methods
        )
        self.tree = ast.Module(body=[], type_ignores=[])
        
    def _create_descriptions_dict(self) -> None:
        """Cria o dicionário centralizado de descrições para a ferramenta."""
        # Cria um dicionário vazio para as descrições
        descriptions_dict = ast.Dict(keys=[], values=[])
        
        # Adiciona descrições para cada parâmetro
        for param in self.tool_def.parameters:
            param_name = param.name
            param_desc = param.description
            
            # Chave para o dicionário: NomeFerramenta.Parameters.nome_parametro
            tool_name_clean = self.tool_def.name.replace(' ', '')
            key_str = f"{tool_name_clean}Parameters.{param_name}"
            
            # Adiciona ao dicionário
            descriptions_dict.keys.append(ast.Constant(value=key_str))
            descriptions_dict.values.append(ast.Constant(value=param_desc))
        
        # Adiciona descrição da própria ferramenta
        tool_name_clean = self.tool_def.name.replace(' ', '')
        descriptions_dict.keys.append(ast.Constant(value=f"{tool_name_clean}Tool.description"))
        descriptions_dict.values.append(ast.Constant(value=self.tool_def.description))
        
        # Cria a atribuição para DESCRIPTIONS
        descriptions_assign = ast.Assign(
            targets=[ast.Name(id="DESCRIPTIONS", ctx=ast.Store())],
            value=descriptions_dict
        )
        
        # Adicionar comentário antes da definição
        comment = ast.Expr(
            value=ast.Constant(
                value="# Dicionário centralizado de descrições"
            )
        )
        
        # Adiciona o comentário e a atribuição à árvore AST
        self.tree.body.append(comment)
        self.tree.body.append(descriptions_assign)
        
        # Adiciona também a função get_description usando ast diretamente para evitar erros de sintaxe
        get_desc_func = ast.FunctionDef(
            name='get_description',
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg='key', annotation=ast.Name(id='str', ctx=ast.Load()))],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                vararg=None,
                kwarg=None
            ),
            body=[
                # Docstring como expressão
                ast.Expr(value=ast.Constant(value="Retorna a descrição para a chave especificada do dicionário DESCRIPTIONS.")),
                # Return statement
                ast.Return(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id='DESCRIPTIONS', ctx=ast.Load()),
                            attr='get',
                            ctx=ast.Load()
                        ),
                        args=[
                            ast.Name(id='key', ctx=ast.Load()),
                            ast.JoinedStr([
                                ast.Constant(value="Descrição para "),
                                ast.FormattedValue(
                                    value=ast.Name(id='key', ctx=ast.Load()),
                                    conversion=-1,
                                    format_spec=None
                                ),
                                ast.Constant(value=" não encontrada")
                            ])
                        ],
                        keywords=[]
                    )
                )
            ],
            decorator_list=[],
            returns=ast.Name(id='str', ctx=ast.Load())
        )
        
        # Adiciona o comentário antes da função
        comment = ast.Expr(
            value=ast.Constant(
                value="# Função para obter descrições do dicionário local"
            )
        )
        
        # Adiciona o comentário e a função à árvore AST
        self.tree.body.append(comment)
        self.tree.body.append(get_desc_func)
    
    def add_imports(self) -> None:
        """Adiciona imports ao início do arquivo."""
        # Imports padrão
        standard_imports = [
            "from typing import Dict, List, Any, Optional, Type",
            "from pydantic import BaseModel, Field",
            "from crewai.tools import BaseTool"
        ]
        
        # Combina com imports personalizados
        all_imports = standard_imports + self.tool_def.imports
        
        # Remove duplicatas mantendo a ordem
        unique_imports = []
        seen = set()
        for imp in all_imports:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)
        
        # Adiciona os imports ao AST
        for imp in unique_imports:
            self.tree.body.append(ast.parse(imp).body[0])
            
        # Adiciona o dicionário de descrições e a função get_description
        self._create_descriptions_dict()
    
    def create_parameter_model(self) -> None:
        """Cria a classe de modelo para os parâmetros da ferramenta."""
        if not self.tool_def.parameters:
            return
        
        # Nome da classe do modelo
        model_name = f"{self.tool_def.name.replace(' ', '')}Parameters"
        
        # Corpo da classe
        class_body = [
            # Docstring
            ast.Expr(
                ast.Constant(
                    value=f"Parâmetros para a ferramenta {self.tool_def.name}."
                )
            )
        ]
        
        # Adiciona os campos para cada parâmetro
        for param in self.tool_def.parameters:
            # Determina o tipo do campo
            type_annotation = self._get_type_annotation(param.type)
            
            # Determina o valor padrão
            default_value = None
            if not param.required:
                if param.default is not None:
                    default_value = ast.Constant(value=param.default)
                else:
                    if param.type == "string":
                        default_value = ast.Constant(value="")
                    elif param.type == "integer" or param.type == "number":
                        default_value = ast.Constant(value=0)
                    elif param.type == "boolean":
                        default_value = ast.Constant(value=False)
                    elif param.type == "array":
                        default_value = ast.List(elts=[], ctx=ast.Load())
                    elif param.type == "object":
                        default_value = ast.Dict(keys=[], values=[])
                    else:
                        default_value = ast.Constant(value=None)
            
            # Cria o campo com Field
            if param.required:
                # Para campos obrigatórios, usa Field(...) 
                field_value = ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[ast.Constant(value=Ellipsis)],  # Usa ... como primeiro argumento
                    keywords=[
                        ast.keyword(
                            arg="description",
                            value=ast.Constant(value=param.description)
                        )
                    ]
                )
            else:
                # Para campos opcionais, usa Field(default=valor)
                field_value = ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="description",
                            value=ast.Constant(value=param.description)
                        ),
                        ast.keyword(
                            arg="default",
                            value=default_value
                        )
                    ]
                )
            
            # Cria a atribuição do campo
            field_assign = ast.AnnAssign(
                target=ast.Name(id=param.name, ctx=ast.Store()),
                annotation=type_annotation,
                value=field_value,
                simple=1
            )
            
            class_body.append(field_assign)
        
        # Cria a classe
        class_def = ast.ClassDef(
            name=model_name,
            bases=[ast.Name(id="BaseModel", ctx=ast.Load())],
            keywords=[],
            body=class_body,
            decorator_list=[]
        )
        
        self.tree.body.append(class_def)
    
    def _get_type_annotation(self, param_type: str) -> ast.AST:
        """Converte o tipo de parâmetro para uma anotação de tipo AST."""
        if param_type == "string":
            return ast.Name(id="str", ctx=ast.Load())
        elif param_type == "integer":
            return ast.Name(id="int", ctx=ast.Load())
        elif param_type == "number":
            return ast.Name(id="float", ctx=ast.Load())
        elif param_type == "boolean":
            return ast.Name(id="bool", ctx=ast.Load())
        elif param_type == "array":
            return ast.Subscript(
                value=ast.Name(id="List", ctx=ast.Load()),
                slice=ast.Name(id="Any", ctx=ast.Load()),
                ctx=ast.Load()
            )
        elif param_type == "object":
            return ast.Subscript(
                value=ast.Name(id="Dict", ctx=ast.Load()),
                slice=ast.Tuple(
                    elts=[
                        ast.Name(id="str", ctx=ast.Load()),
                        ast.Name(id="Any", ctx=ast.Load())
                    ],
                    ctx=ast.Load()
                ),
                ctx=ast.Load()
            )
        else:
            return ast.Name(id="Any", ctx=ast.Load())
    
    def create_tool_class(self) -> None:
        """Cria a classe da ferramenta."""
        # Nome da classe
        class_name = f"{self.tool_def.name.replace(' ', '')}Tool"
        
        # Corpo da classe
        class_body = [
            # Docstring
            ast.Expr(
                ast.Constant(
                    value=self.tool_def.description
                )
            ),
            # model_config
            ast.Assign(
                targets=[ast.Name(id="model_config", ctx=ast.Store())],
                value=ast.Dict(
                    keys=[
                        ast.Constant(value="arbitrary_types_allowed"),
                        ast.Constant(value="validate_assignment")
                    ],
                    values=[
                        ast.Constant(value=True),
                        ast.Constant(value=True)
                    ]
                )
            ),
            # name
            ast.AnnAssign(
                target=ast.Name(id="name", ctx=ast.Store()),
                annotation=ast.Name(id="str", ctx=ast.Load()),
                value=ast.Constant(value=self.tool_def.name),
                simple=1
            ),
            # description
            ast.AnnAssign(
                target=ast.Name(id="description", ctx=ast.Store()),
                annotation=ast.Name(id="str", ctx=ast.Load()),
                value=ast.Call(
                    func=ast.Name(id="get_description", ctx=ast.Load()),
                    args=[ast.Constant(value=f"{self.tool_def.name.replace(' ', '')}Tool.description")],
                    keywords=[]
                ),
                simple=1
            )
        ]
        
        # Adiciona args_schema se houver parâmetros
        if self.tool_def.parameters:
            model_name = f"{self.tool_def.name.replace(' ', '')}Parameters"
            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id="args_schema", ctx=ast.Store()),
                    annotation=ast.Name(id="Type[BaseModel]", ctx=ast.Load()),
                    value=ast.Name(id=model_name, ctx=ast.Load()),
                    simple=1
                )
            )
        
        # Adiciona métodos personalizados
        for method_code in self.tool_def.custom_methods:
            method_ast = ast.parse(method_code).body[0]
            class_body.append(method_ast)
        
        # Cria o método _run
        run_method = self._create_run_method()
        class_body.append(run_method)
        
        # Cria a classe
        class_def = ast.ClassDef(
            name=class_name,
            bases=[ast.Name(id="BaseTool", ctx=ast.Load())],
            keywords=[],
            body=class_body,
            decorator_list=[]
        )
        
        self.tree.body.append(class_def)
        
        # Adiciona um bloco if __name__ == "__main__" para testar a ferramenta
        main_block = self._create_main_block(class_name)
        self.tree.body.append(main_block)
    
    def _create_run_method(self) -> ast.FunctionDef:
        """Cria o método _run da ferramenta."""
        # Determina os parâmetros da função
        args = [ast.arg(arg="self", annotation=None)]
        
        for param in self.tool_def.parameters:
            type_annotation = self._get_type_annotation(param.type)
            
            if param.required:
                args.append(ast.arg(arg=param.name, annotation=type_annotation))
            else:
                args.append(ast.arg(arg=param.name, annotation=type_annotation))
        
        # Cria os valores padrão para parâmetros opcionais
        defaults = []
        for param in self.tool_def.parameters:
            if not param.required:
                if param.default is not None:
                    defaults.append(ast.Constant(value=param.default))
                else:
                    if param.type == "string":
                        defaults.append(ast.Constant(value=""))
                    elif param.type == "integer" or param.type == "number":
                        defaults.append(ast.Constant(value=0))
                    elif param.type == "boolean":
                        defaults.append(ast.Constant(value=False))
                    elif param.type == "array":
                        defaults.append(ast.List(elts=[], ctx=ast.Load()))
                    elif param.type == "object":
                        defaults.append(ast.Dict(keys=[], values=[]))
                    else:
                        defaults.append(ast.Constant(value=None))
        
        # MODIFICADO: Preservar a indentação original do código de implementação
        # Isso é fundamental para manter a estrutura sintática válida
        implementation_code = self.tool_def.implementation.strip()
        
        try:
            # Tenta fazer o parse da implementação
            implementation_ast = ast.parse(implementation_code).body
            body = implementation_ast
            
        except SyntaxError as e:
            # Extrai informações detalhadas sobre o erro
            erro_linha = e.lineno
            erro_offset = e.offset
            linhas_codigo = implementation_code.split("\n")
            
            # Prepara o contexto do erro (3 linhas antes e depois)
            inicio = max(0, erro_linha - 4)
            fim = min(len(linhas_codigo), erro_linha + 3)
            contexto = linhas_codigo[inicio:fim]
            
            # Formata a mensagem de erro
            erro_detalhado = [
                "\nERRO DE SINTAXE NA IMPLEMENTAÇÃO",
                "=" * 40,
                f"Ferramenta: {self.tool_def.name}",
                f"Erro: {e.msg}",
                f"Linha: {erro_linha}",
                "\nContexto do erro:",
                "-" * 20
            ]
            
            # Adiciona o contexto com números de linha
            for i, linha in enumerate(contexto, start=inicio + 1):
                marcador = ">>" if i == erro_linha else "  "
                erro_detalhado.append(f"{marcador} {i:4d} | {linha}")
                if i == erro_linha:
                    erro_detalhado.append(f"     | {' ' * (erro_offset-1)}^")
            
            erro_detalhado.extend([
                "-" * 20,
                "\nATENÇÃO - PARÂMETROS DA FERRAMENTA:",
                f"Os seguintes parâmetros são automaticamente recebidos pelo método _run: {', '.join([p.name for p in self.tool_def.parameters])}",
                "Você NÃO precisa redeclará-los, apenas usá-los diretamente na implementação.",
                "\nINSTRUÇÕES PARA AGENTES DO CREWAI:",
                "\n1. IMPLEMENTAÇÃO RECOMENDADA (MÉTODO AUXILIAR):",
                """        # Delegar para método auxiliar é a abordagem mais segura
        return self.processar_api(url, formato)""",
                "\n   Adicione o método auxiliar via custom_methods:",
                """def processar_api(self, url, formato):
    # Validar parâmetros
    if not url.startswith(('http://', 'https://')):
        return 'Erro: URL inválida'
    
    # Processar requisição
    try:
        response = requests.get(url)
        dados = response.json()
        return json.dumps(dados) if formato == 'json' else str(dados)[:500]
    except Exception as e:
        return f'Erro: {str(e)}'""",
                "\n2. IMPLEMENTAÇÃO SIMPLIFICADA (SEM BLOCOS COMPLEXOS):",
                """        # Processamento direto
        resultado = {'url': url, 'formato': formato}
        return json.dumps(resultado)""",
                "\n3. ESTRUTURA PARA PROCESSAMENTO DIRETO:",
                """        # Validação básica sem blocos condicionais complexos
        if not url.startswith('http'):
            return {'erro': 'URL inválida'}
            
        # Continuar com processamento direto
        response = requests.get(url)
        return str(response.text)[:500]""",
                "\nREGRAS PARA IMPLEMENTAÇÃO:",
                "1. Evite blocos complexos aninhados no método _run",
                "2. Use métodos auxiliares para lógica complexa (via custom_methods)",
                "3. Mantenha a indentação consistente",
                "4. Para APIs, implemente tratamento de erros adequado"
            ])
            
            # Lança o erro com a mensagem formatada
            raise SyntaxError("\n".join(erro_detalhado)) from e
        
        # Cria o método
        run_method = ast.FunctionDef(
            name="_run",
            args=ast.arguments(
                posonlyargs=[],
                args=args,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=defaults,
                vararg=None,
                kwarg=None
            ),
            body=body,
            decorator_list=[],
            returns=None
        )
        
        return run_method
    
    def _create_main_block(self, class_name: str) -> ast.If:
        """Cria um bloco if __name__ == "__main__" para testar a ferramenta."""
        # Cria o corpo do bloco if
        if_body = [
            # Cria uma instância da ferramenta
            ast.Assign(
                targets=[ast.Name(id="tool", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id=class_name, ctx=ast.Load()),
                    args=[],
                    keywords=[]
                )
            ),
            # Executa a ferramenta com parâmetros de exemplo
            ast.Assign(
                targets=[ast.Name(id="result", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="tool", ctx=ast.Load()),
                        attr="run",
                        ctx=ast.Load()
                    ),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg=param.name,
                            value=ast.Constant(value=param.default if param.default is not None else "exemplo")
                        )
                        for param in self.tool_def.parameters
                    ]
                )
            ),
            # Imprime o resultado
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[ast.Name(id="result", ctx=ast.Load())],
                    keywords=[]
                )
            )
        ]
        
        # Cria o bloco if
        if_block = ast.If(
            test=ast.Compare(
                left=ast.Name(id="__name__", ctx=ast.Load()),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value="__main__")]
            ),
            body=if_body,
            orelse=[]
        )
        
        return if_block
    
    def generate_code(self) -> str:
        """Gera o código Python a partir da AST."""
        return astor.to_source(self.tree)


class DynamicToolCreator(BaseTool):
    """Uma ferramenta para criar novas ferramentas no CrewAI dinamicamente."""

    model_config = {
        'arbitrary_types_allowed': True,
        'validate_assignment': True
    }

    name: str = "Dynamic Tool Creator"
    description: str = get_description("DynamicToolCreator.description")
    args_schema: Type[BaseModel] = ToolDefinition

    def verificar_metodos_vazios(self, custom_methods: List[str]) -> List[str]:
        """Verifica se algum método auxiliar está vazio (contém apenas 'pass').
        
        Parâmetros:
            custom_methods: Lista de métodos personalizados a verificar
            
        Retorna:
            Lista de nomes dos métodos que estão vazios (contêm apenas 'pass')
        """
        metodos_vazios = []
        
        for metodo in custom_methods:
            # Tenta parsear o método para AST
            try:
                metodo_ast = ast.parse(metodo).body[0]
                
                # Verifica se é uma definição de função
                if isinstance(metodo_ast, ast.FunctionDef):
                    # Verifica se o corpo do método contém apenas 'pass'
                    if len(metodo_ast.body) == 1 and isinstance(metodo_ast.body[0], ast.Pass):
                        # Extrai o nome do método
                        nome_metodo = metodo_ast.name
                        metodos_vazios.append(nome_metodo)
            except Exception as e:
                # Se não conseguir parsear, ignorar
                print(f"Erro ao analisar método: {e}")
                continue
                
        return metodos_vazios
    
    def _run(self, 
            name: str, 
            description: str, 
            parameters = [],
            implementation: str = "",
            imports: List[str] = [],
            custom_methods: List[str] = []):
        """Cria e salva uma nova ferramenta.
        
        Parâmetros:
            name: Nome da ferramenta
            description: Descrição da ferramenta
            parameters: Lista de parâmetros (pode ser lista de ToolParameter ou dict)
            implementation: Código de implementação da ferramenta
            imports: Lista de importações adicionais
            custom_methods: Lista de métodos personalizados
        """
        register_tool_usage(
            tool_name="DynamicToolCreator",
            params={
                "name": name,
                "parameters_count": len(parameters),
                "imports_count": len(imports),
                "custom_methods_count": len(custom_methods)
            },
            metadata={
                "implementation_length": len(implementation)
            }
        )
        
        # Normaliza o nome da ferramenta para o nome do arquivo
        tool_dir_name = name.lower().replace(" ", "") + "_tool"

        # Cria o diretório para a ferramenta
        tools_dir = Path(f"crews/pdca/tools/{tool_dir_name}")
        tools_dir.mkdir(parents=True, exist_ok=True)

        tool_file_name = name.lower().replace(" ", "_") + "_tool.py"
        
        # Verificar se há métodos auxiliares vazios
        metodos_vazios = self.verificar_metodos_vazios(custom_methods)
        if metodos_vazios:
            mensagem_erro = f"ERRO: Os seguintes métodos auxiliares estão vazios (apenas 'pass'): {', '.join(metodos_vazios)}. \nMétodos vazios não são permitidos, você deve implementar a lógica necessária para cada método auxiliar definido."
            return mensagem_erro
            
        # Garantir que todos os parâmetros estejam no formato de dicionário
        converted_parameters = []
        for param in parameters:
            if isinstance(param, dict):
                # Se já é um dicionário, manter como está
                converted_parameters.append(param.copy())
            else:
                # Se for outro tipo (como ToolParameter), converter para dict
                # Este caso não deve ocorrer com a definição atual, mas mantemos por segurança
                try:
                    converted_parameters.append({
                        'name': getattr(param, 'name', ''),
                        'type': getattr(param, 'type', 'string'),
                        'description': getattr(param, 'description', 'Parâmetro sem descrição'),
                        'required': getattr(param, 'required', True),
                        'default': getattr(param, 'default', None)
                    })
                except Exception as e:
                    print(f"Erro ao converter parâmetro: {e}")
                    # Usar um parâmetro padrão para evitar falhas
                    converted_parameters.append({
                        'name': 'param_default',
                        'type': 'string',
                        'description': 'Parâmetro padrão (conversão falhou)',
                        'required': False,
                        'default': ''
                    })

        # Cria a definição da ferramenta
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=converted_parameters,
            implementation=implementation,
            imports=imports,
            custom_methods=custom_methods
        )
        
        # Cria o construtor de AST
        builder = ToolASTBuilder(tool_def)
        
        # Adiciona os imports
        builder.add_imports()
        
        # Cria o modelo de parâmetros se houver parâmetros
        if parameters:
            builder.create_parameter_model()
        
        # Cria a classe da ferramenta
        builder.create_tool_class()
        
        # Gera o código
        code = builder.generate_code()
        
        # Salva o código em um arquivo
        tool_file_path = tools_dir / tool_file_name
        with open(tool_file_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Cria o arquivo __init__.py para garantir que o diretório seja um pacote Python
        init_file_path = tools_dir / "__init__.py"
        if not init_file_path.exists():
            with open(init_file_path, "w", encoding="utf-8") as f:
                f.write("# Pacote para ferramentas dinâmicas\n")
                f.write(f"from .{name.lower().replace(' ', '_')}_tool import {name.replace(' ', '')}Tool\n")
        
        # Verificar a ferramenta criada para identificar erros comuns
        print(f"Verificando a ferramenta criada: {tool_file_path}")
        verificador = ToolVerifierTool()
        verificacao_dict = verificador.run(
            tool_path=str(tool_file_path)
        )
        
        # Usar o dicionário diretamente
        verificacao_sucesso = verificacao_dict.get("sucesso", False)
        verificacao_erros = verificacao_dict.get("erros", ["Erro: Falha ao obter erros da verificação."])
        verificacao_avisos = verificacao_dict.get("avisos", [])
        
        # Construir o relatório final a partir do dicionário
        report_lines = [f"## Ferramenta Criada: {name}"]
        report_lines.append(f"**Localização:** {tool_file_path}")
        report_lines.append(f"**Descrição:** {description}")

        if parameters:
            report_lines.append("### Parâmetros da Ferramenta:")
            for i, param in enumerate(converted_parameters):
                req_text = "Sim" if param.get('required', True) else "Não"
                default_text = f", Valor Padrão: {param.get('default')}" if not param.get('required', True) and param.get('default') is not None else ""
                report_lines.append(f"{i+1}. **{param.get('name', 'N/D')}** ({param.get('type', 'N/D')}): {param.get('description', 'N/D')}. Obrigatório: {req_text}{default_text}")

        if not verificacao_sucesso:
            report_lines.append(f"\n**A ferramenta '{name}' foi criada, mas foram encontrados problemas críticos que precisam ser corrigidos:**")
            # Processar cada erro para garantir formatação adequada
            for erro in verificacao_erros:
                # Adicionar o erro formatado ao relatório
                report_lines.append(erro)
                
            if verificacao_avisos: # Mostrar avisos mesmo se houver erros
                report_lines.append("\n**Avisos adicionais:**")
                for aviso in verificacao_avisos:
                    report_lines.append(aviso)
        elif verificacao_avisos:
            report_lines.append(f"\n**A ferramenta '{name}' foi criada com os seguintes avisos:**")
            for aviso in verificacao_avisos:
                report_lines.append(aviso)
        else:
            report_lines.append(f"\n**A ferramenta '{name}' foi criada e verificada com sucesso!**")
        
        # Processar o relatório para garantir formatação adequada
        # Primeiro, juntar todas as linhas
        raw_report = "\n".join([line for line in report_lines if line.strip()])
        
        # Substituir sequências problemáticas que podem afetar a formatação
        # Isso garante que as mensagens de erro sejam exibidas corretamente
        final_report = raw_report.replace("\n\n", "\n").replace("\r\n", "\n")
        
        # Se a verificação foi bem-sucedida, testar a execução da ferramenta
        if verificacao_sucesso:
            nome_classe = f"{name.replace(' ', '')}Tool"
            
            # Adicionar seção de teste dinâmico ao relatório
            final_report += "\n\n## Teste de Execução Dinâmica\n\n"
            
            try:
                # Preparar parâmetros de teste básicos para parâmetros obrigatórios
                parametros_teste = {}
                
                for param in converted_parameters:
                    if param.get('required', True):
                        tipo = param.get('type', 'string')
                        nome_param = param.get('name', '')
                        
                        if tipo == 'string':
                            parametros_teste[nome_param] = f"valor_teste_{nome_param}"
                        elif tipo == 'integer':
                            parametros_teste[nome_param] = 42
                        elif tipo == 'boolean':
                            parametros_teste[nome_param] = True
                        elif tipo == 'array':
                            parametros_teste[nome_param] = ["item1", "item2"]
                        elif tipo == 'object':
                            parametros_teste[nome_param] = {"chave": "valor"}
                
                # Executar a ferramenta dinamicamente
                print(f"Testando execução dinâmica da ferramenta: {nome_classe} com parâmetros: {parametros_teste}")
                
                # Usar o ExecutarFerramentaTool para carregar e executar a ferramenta
                executar_tool = ExecutarFerramentaTool()
                resultado_execucao = executar_tool.run(
                    caminho_ferramenta=str(tool_file_path),
                    nome_classe=nome_classe,
                    parametros=parametros_teste
                )
                
                # Adicionar informações sobre a execução ao relatório
                final_report += "A ferramenta foi compilada e executada dinamicamente para verificar sua funcionalidade.\n\n"
                final_report += f"**Parâmetros de teste:** {parametros_teste}\n\n"
                
                # Se houver mensagem de erro relacionada a valor_teste_, omitir da saída
                if isinstance(resultado_execucao, str) and "valor_teste_" in str(parametros_teste) and ("ERRO" in resultado_execucao or "erro" in resultado_execucao):
                    final_report += "**Nota:** A ferramenta foi testada com valores placebo. Em uma execução real, serão usados valores válidos fornecidos pelo agente."
                else:
                    final_report += "**Resultado da execução:**\n\n"
                    final_report += resultado_execucao.replace('\n', '\n\n') if isinstance(resultado_execucao, str) else str(resultado_execucao)
                
            except Exception as e:
                # Capturar e reportar erros durante a execução
                final_report += "**ATENÇÃO:** A ferramenta foi criada e verificada estaticamente, mas falhou na execução dinâmica.\n\n"
                final_report += f"**Erro:** {str(e)}\n\n"
                final_report += "**Dicas para correção:**\n\n"
                final_report += "1. Verifique se a implementação da ferramenta está correta\n"
                final_report += "2. Garanta que os parâmetros obrigatórios estão sendo tratados adequadamente\n"
                final_report += "3. Corrija o método _run da ferramenta\n"

        return final_report

# ---------------- Definições Auxiliares ----------------

if __name__ == "__main__":
    # Exemplo de uso da ferramenta
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
# Simplesmente chamar o método personalizado que contém toda a lógica
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
    padrao_data = re.compile('\\[(\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2})\\]')
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