# Projeto PDCA - Ciclo de Melhoria Contínua com CrewAI

## Visão Geral

O Projeto PDCA implementa o ciclo de melhoria contínua Plan-Do-Check-Act (Planejar-Fazer-Verificar-Agir) utilizando a arquitetura de agentes e equipes da biblioteca CrewAI. Este sistema permite a criação de fluxos de trabalho automatizados e inteligentes para resolução de problemas e melhoria contínua em diversos contextos organizacionais.

## Estrutura do Projeto

O projeto está organizado em módulos que representam as diferentes fases do ciclo PDCA, além de componentes de suporte:

```text
crews/pdca/
├── __init__.py                # Inicialização do pacote com importação dinâmica
├── pdca_flow.py               # Implementação do fluxo PDCA básico
├── pdca_continuous_flow.py    # Implementação do fluxo PDCA contínuo e adaptativo
├── pdca_models.py             # Modelos de dados Pydantic para o ciclo PDCA
├── planejar/                  # Módulo da fase de planejamento
├── fazer/                     # Módulo da fase de execução
├── verificar/                 # Módulo da fase de verificação
├── agir/                      # Módulo da fase de ação corretiva
├── ferramentas/               # Equipe para criação dinâmica de ferramentas
├── tools/                     # Ferramentas utilizadas pelos agentes
├── utilities/                 # Utilitários de suporte
├── documentacao_crew/         # Equipe para geração de documentação
└── resultados/                # Diretório para armazenamento de resultados
```

## Componentes Principais

### Fluxos PDCA

#### PDCAFlow (`pdca_flow.py`)

Implementa o ciclo PDCA tradicional usando a arquitetura de Flows do CrewAI. Principais características:

- Gerenciamento de estado e persistência do ciclo
- Execução sequencial das fases: Planejar, Fazer, Verificar, Agir
- Logging detalhado de todas as operações
- Geração de relatórios e reinício de ciclos

#### PDCAContinuousFlow (`pdca_continuous_flow.py`)

Extensão do fluxo PDCA para um ciclo contínuo e adaptativo:

- Integração de ferramentas dinâmicas para criação automática de agentes, equipes e tarefas
- Adaptação automática da equipe com base nos resultados anteriores
- Busca de conhecimento em ciclos anteriores para melhoria contínua
- Execução de múltiplos ciclos contínuos

### Modelos de Dados (`pdca_models.py`)

Define os modelos Pydantic para estruturar os dados do ciclo PDCA:

- Enumerações para fases (`PDCAFase`) e status (`PDCAStatus`)
- Modelos para Plano de Ação, Resultado de Execução, Resultado de Verificação e Ação Corretiva
- Modelo principal `PDCAState` que agrega todas as informações do ciclo
- Modelo para saída das ferramentas inteligentes

### Equipes Especializadas

#### PlanejarCrew (`planejar/planejar_crew.py`)

Equipe especializada na fase PLAN (Planejar) do ciclo PDCA:

- Análise profunda do problema, contexto e causas
- Definição de metas claras e mensuráveis
- Elaboração de plano de ação detalhado
- Integração de todos os elementos do planejamento

#### FazerCrew (`fazer/fazer_crew.py`)

Equipe especializada na fase DO (Fazer) do ciclo PDCA:

- Coordenação da implementação do plano de ação
- Execução das atividades planejadas
- Coleta de dados durante a execução
- Monitoramento de progresso e documentação

#### VerificarCrew (`verificar/verificar_crew.py`)

Equipe especializada na fase CHECK (Verificar) do ciclo PDCA:

- Análise dos dados coletados durante a execução
- Comparação dos resultados com as metas estabelecidas
- Identificação de desvios e suas causas
- Avaliação da eficácia das ações implementadas

#### AgirCrew (`agir/agir_crew.py`)

Equipe especializada na fase ACT (Agir) do ciclo PDCA:

- Desenvolvimento de soluções para problemas identificados
- Padronização e institucionalização de melhorias
- Correção de desvios e ajustes de curso
- Documentação de lições aprendidas
- Preparação para o próximo ciclo PDCA

#### FerramentasCrew (`ferramentas/ferramentas_crew.py`)

Equipe especializada na criação dinâmica de ferramentas:

- Criação de agentes especializados para tarefas específicas
- Definição de tarefas bem estruturadas
- Formação de equipes otimizadas
- Criação de ferramentas personalizadas
- Integração de todos os recursos criados

#### DocumentacaoCrew (`documentacao_crew/documentacao_crew.py`)

Equipe especializada na criação de documentação técnica:

- Projeto da estrutura da documentação
- Criação de conteúdo técnico claro e preciso
- Validação da qualidade e usabilidade da documentação
- Finalização do pacote de documentação

### Ferramentas Dinâmicas

O projeto inclui um conjunto poderoso de ferramentas dinâmicas que permitem a criação e adaptação de componentes em tempo de execução, representando um dos aspectos mais inovadores desta implementação:

### 🛠️ Dynamic Tool Creator

Uma ferramenta revolucionária que permite criar novas ferramentas dinamicamente a partir de descrições, parâmetros e código de execução:

- **Geração de código AST**: Constrói ferramentas completas usando Abstract Syntax Trees (AST)
- **Validação automática**: Inclui validação de parâmetros e tipos
- **Documentação integrada**: Gera automaticamente descrições detalhadas para agentes
- **Testabilidade**: Cria blocos de teste para validação imediata das ferramentas geradas

Esta ferramenta é particularmente poderosa por permitir que agentes criem suas próprias ferramentas durante a execução do ciclo PDCA, adaptando-se a novos desafios sem intervenção humana.

### 👤 Dynamic Agent Creator

Permite criar configurações de agentes especializados com diferentes papéis, objetivos e histórias de fundo:

- **Configuração YAML**: Gera arquivos de configuração estruturados para agentes
- **Personalização de contexto**: Define backstories detalhadas para melhorar o raciocínio do agente
- **Integração com LLMs**: Configuração flexível de modelos de linguagem por agente

### 📋 Dynamic Task Creator

Facilita a definição de tarefas específicas para cada fase do ciclo PDCA:

- **Descrições detalhadas**: Define claramente o escopo e objetivos de cada tarefa
- **Saídas esperadas**: Especifica os resultados esperados para validação
- **Formatação multilinhas**: Suporta diferentes estilos de formatação para melhor legibilidade

### 👥 Dynamic Crew Creator

Uma ferramenta avançada que permite a composição de equipes especializadas conforme necessário:

- **Geração de código completo**: Cria classes de equipes funcionais com todos os métodos necessários
- **Configuração de fluxo**: Suporta diferentes tipos de processos (sequencial, hierárquico)
- **Integração de agentes e tarefas**: Conecta automaticamente agentes às suas tarefas
- **Estrutura de diretórios**: Cria toda a estrutura de arquivos necessária para uma nova equipe

Estas ferramentas dinâmicas representam um avanço significativo na automação e adaptabilidade do ciclo PDCA, permitindo que o sistema evolua e se adapte continuamente a novos desafios e contextos sem necessidade de reprogramação manual.

## Requisitos e Dependências

- Python 3.9+
- CrewAI (biblioteca principal para agentes, tarefas, equipes e fluxos)
- Pydantic (para modelos de dados)
- python-dotenv (para carregamento de variáveis de ambiente)
- Outras dependências específicas para ferramentas dinâmicas

## Configuração do Ambiente

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure as variáveis de ambiente no arquivo `.env`:

   ```makefile
   OPENAI_API_KEY=sua_chave_api
   AZURE_OPENAI_API_KEY=sua_chave_azure
   AZURE_OPENAI_ENDPOINT=seu_endpoint_azure
   ```

## Uso Básico

### Executando um Ciclo PDCA Completo

```python
from crews.pdca import PDCAFlow

# Criar uma instância do fluxo PDCA
pdca_flow = PDCAFlow()

# Definir os inputs para o ciclo
inputs = {
    "problema": "Falta de CRM para gerenciar clientes",
    "contexto": "Construtora de condomínios que vende lotes. Necessita de um CRM para gerenciar clientes, emitir boletos e enviar mensagens via WhatsApp.",
    "objetivo": "Implementar um sistema CRM completo com funcionalidades de gestão de clientes, emissão de boletos e integração com WhatsApp",
    "restricoes": "Orçamento limitado, equipe pequena, prazo de 6 meses",
    "prazo": "6 meses",
    "recursos": "Equipe de TI com 3 pessoas, orçamento de R$ 50.000",
    "definicao_problema": "A empresa não possui um sistema centralizado para gerenciar informações de clientes, o que dificulta o acompanhamento de vendas, pagamentos e comunicação",
    "analise_contexto": "A empresa está em crescimento e precisa melhorar a eficiência operacional para atender um número crescente de clientes"
}

# Executar o ciclo PDCA completo
resultado = pdca_flow.executar_ciclo_completo(inputs)

# Gerar relatório final
relatorio = pdca_flow.gerar_relatorio()
print(relatorio)
```

### Executando um Ciclo PDCA Contínuo

```python
from crews.pdca import PDCAContinuousFlow

# Criar uma instância do fluxo PDCA contínuo
pdca_continuous = PDCAContinuousFlow()

# Definir os inputs para o ciclo
inputs = {
    "problema": "Falta de CRM para gerenciar clientes",
    "contexto": "Construtora de condomínios que vende lotes...",
    # ... outros inputs como no exemplo anterior
}

# Executar múltiplos ciclos PDCA contínuos
resultados = pdca_continuous.executar_ciclos_continuos(inputs, num_ciclos=3)

# Gerar relatório final
relatorio_final = pdca_continuous.gerar_relatorio_consolidado()
print(relatorio_final)
```

## Exemplo de Caso de Uso

O projeto inclui um exemplo completo de implementação de um sistema CRM para uma construtora de condomínios:

1. **Fase de Planejamento**: Análise do problema, definição de metas e elaboração de plano de ação para implementação do CRM.
2. **Fase de Execução**: Implementação do plano, incluindo pesquisa de fornecedores, configuração do sistema e integração com sistemas existentes.
3. **Fase de Verificação**: Análise dos resultados obtidos, comparação com as metas estabelecidas e identificação de desvios.
4. **Fase de Ação**: Desenvolvimento de soluções para problemas identificados, padronização de melhorias e preparação para o próximo ciclo.

## Extensão e Personalização

O sistema foi projetado para ser facilmente extensível:

- Novas ferramentas podem ser adicionadas ao diretório `tools/`
- Novos agentes podem ser definidos nas equipes existentes
- Novas equipes podem ser criadas para fases específicas
- O fluxo PDCA pode ser personalizado para diferentes contextos

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas alterações (`git commit -am 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Crie um novo Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
