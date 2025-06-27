#!/usr/bin/env python
"""
Módulo PDCA - Ferramentas e Equipes para o ciclo PDCA (Plan-Do-Check-Act)

Este módulo implementa um conjunto completo de ferramentas e equipes baseadas no ciclo PDCA,
uma metodologia para melhoria contínua e resolução de problemas.
"""

import os
import pkgutil
import importlib
import inspect
from pathlib import Path

# Inicializar estruturas para rastrear o que foi importado com sucesso
__imported_items__ = {}
__all__ = []

# Função para descobrir e importar dinamicamente todos os módulos
def discover_and_import_modules():
    """
    Descobre e importa automaticamente TODOS os módulos Python encontrados em qualquer
    subdiretório dentro do pacote PDCA, sem depender de categorias predefinidas.
    
    Esta abordagem permite que novas ferramentas e equipes sejam criadas em tempo de execução
    em qualquer local dentro da estrutura de diretórios, e ainda assim sejam descobertas
    automaticamente durante a próxima importação.
    """
    # Caminho base para este pacote
    base_path = Path(os.path.dirname(__file__))
    package_prefix = 'crews.pdca'
    
    # Classes e funções a serem incluídas em __all__
    global __all__
    global __imported_items__
    
    # Realizar uma busca recursiva em todos os diretórios dentro do pacote PDCA
    _scan_recursively(base_path, package_prefix)

# Função para escanear recursivamente todo o pacote
def _scan_recursively(base_dir: Path, package_prefix: str):
    """
    Escaneia recursivamente todos os diretórios e subdiretórios em busca de módulos Python.
    Não depende de estruturas predefinidas ou categorias fixas.
    """
    # Primeiro, verificar se há módulos Python diretamente neste diretório
    _import_directory_modules(str(base_dir), package_prefix)
    
    # Em seguida, processar todos os subdiretórios recursivamente
    for item in base_dir.iterdir():
        # Ignorar diretórios especiais ou arquivos
        if not item.is_dir() or item.name.startswith('__') or item.name.startswith('.'):
            continue
        
        # Construir o caminho completo do pacote para este subdiretório
        subdir_package = f"{package_prefix}.{item.name}"
        
        # Escanear este subdiretório recursivamente
        _scan_recursively(item, subdir_package)

# Função para importar módulos de um diretório específico
def _import_directory_modules(directory: str, package_path: str):
    """
    Importa todos os módulos Python encontrados em um diretório específico.
    """
    # Verificar existência do diretório
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return
    
    # Encontrar todos os módulos no diretório
    for _, name, is_pkg in pkgutil.iter_modules([directory]):
        # Ignorar arquivos especiais
        if name.startswith('_') or name.startswith('.'):
            continue
        
        # Formar o nome completo do módulo
        module_name = f'{package_path}.{name}'
        
        try:
            # Tentar importar o módulo
            module = importlib.import_module(module_name)
            
            # Registrar o módulo e suas classes/funções públicas
            _register_module_items(module, module_name)
            
            # Se for um pacote, já é tratado pela função _scan_recursively
            # que visita todos os subdiretórios automaticamente
            
        except (ImportError, ModuleNotFoundError):
            # Ignorar silenciosamente módulos que não podem ser importados
            pass

# Função para registrar as classes e funções de um módulo
def _register_module_items(module, module_name: str):
    """
    Registra todas as classes e funções públicas de um módulo:
    1. Adiciona-as à lista __all__ para serem exportadas
    2. Armazena-as no dicionário __imported_items__ para rastreamento
    3. IMPORTANTE: Adiciona-as ao namespace global do módulo para disponibilidade direta
    """
    global __all__
    global __imported_items__
    
    for attr_name, attr_obj in inspect.getmembers(module):
        # Ignorar atributos privados ou internos
        if attr_name.startswith('_'):
            continue
            
        # Verificar se é uma classe ou função pública
        if inspect.isclass(attr_obj) or inspect.isfunction(attr_obj):
            # Verificar se a classe/função foi definida neste módulo (não importada)
            if getattr(attr_obj, '__module__', '') == module_name:
                # Armazenar no dicionário de itens importados
                __imported_items__[attr_name] = attr_obj
                
                # Adicionar ao __all__ para exportação
                if attr_name not in __all__:
                    __all__.append(attr_name)
                    
                # CRUCIAL: Adicionar ao namespace global do módulo
                # Isso torna o objeto disponível diretamente via `from crews.pdca import X`
                globals()[attr_name] = attr_obj

# Executar a descoberta automática ao importar o pacote
discover_and_import_modules()

# Importar explicitamente alguns módulos essenciais, envolvidos em try/except
# para garantir que o módulo ainda seja carregado mesmo se algum deles falhar
# Importar classes essenciais de forma segura para compatibilidade com código existente
# Usamos importlib.util.find_spec para verificar se o módulo existe antes de importar

def _try_import_name(module_path, name):
    """Tenta importar um nome de um módulo e o adiciona a __all__ se for bem-sucedido."""
    try:
        # Verificar se o módulo existe antes de tentar importar
        spec = importlib.util.find_spec(module_path)
        if spec is not None:
            module = importlib.import_module(module_path)
            if hasattr(module, name):
                obj = getattr(module, name)
                # Armazenar no dicionário de itens importados
                __imported_items__[name] = obj
                # Adicionar ao namespace global do módulo
                globals()[name] = obj
                # Adicionar ao __all__ para exportação
                if name not in __all__:
                    __all__.append(name)
                return True
    except (ImportError, ModuleNotFoundError, AttributeError):
        pass
    return False

# Importar módulos essenciais
_important_modules = [
    ('crews.pdca.planejar.planejar_crew', 'PlanejarCrew'),
    ('crews.pdca.fazer.fazer_crew', 'FazerCrew'),
    ('crews.pdca.verificar.verificar_crew', 'VerificarCrew'),
    ('crews.pdca.agir.agir_crew', 'AgirCrew'),
    ('crews.pdca.pdca_flow', 'PDCAFlow'),
    ('crews.pdca.pdca_flow', 'criar_pdca_flow'),
    ('crews.pdca.pdca_continuous_flow', 'PDCAContinuousFlow'),
    ('crews.pdca.pdca_continuous_flow', 'criar_pdca_continuous_flow'),
]

# Tentar importar cada módulo
for module_path, name in _important_modules:
    _try_import_name(module_path, name)

# Função para facilitar o debug e diagnóstico do sistema de importação
def debug_imports():
    """
    Retorna informações detalhadas sobre os módulos importados dinamicamente.
    Inclui informações sobre quais itens foram de fato adicionados ao namespace.
    """
    # Verificar quais itens estão verdadeiramente disponíveis no namespace atual
    available_in_namespace = []
    for name in __all__:
        if name in globals():
            available_in_namespace.append(name)
    
    return {
        'total_imported': len(__all__),
        'imported_items': __all__,
        'available_in_namespace': available_in_namespace,
        'items_count_in_namespace': len(available_in_namespace),
        'base_directory': os.path.dirname(__file__)
    }

# Adicionar a função de debug ao __all__
__all__.append('debug_imports')
