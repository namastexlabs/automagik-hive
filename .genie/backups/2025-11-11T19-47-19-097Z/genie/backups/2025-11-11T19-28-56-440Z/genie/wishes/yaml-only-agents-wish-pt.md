# 🧞 DESEJO: Definições de Agentes Apenas com YAML

**Status:** PRONTO_PARA_REVISÃO

## Resumo Executivo
Permitir que usuários criem agentes, equipes e workflows usando apenas arquivos de configuração YAML, tornando os arquivos factory em Python (`agent.py`, `team.py`, `workflow.py`) completamente opcionais para casos de uso simples.

## Análise do Estado Atual
**O que existe:**
- `hive/discovery.py` requer arquivos factory `agent.py`/`team.py`/`workflow.py` para carregar componentes (linhas 100-102, 197-199, 294-296)
- `hive/cli/create.py` gera tanto `config.yaml` QUANTO arquivos factory Python para cada componente
- `hive/scaffolder/generator.py` fornece métodos `ConfigGenerator.generate_*_from_yaml()` que podem criar componentes diretamente do YAML
- Agentes de exemplo como `support-bot` ainda usam padrão factory Python mesmo quando YAML é suficiente

**Lacuna identificada:**
- Sistema de descoberta ignora componentes sem arquivos Python, mesmo se existe `config.yaml` válido
- Scaffolding sempre cria boilerplate Python, adicionando sobrecarga cognitiva para iniciantes
- Não há forma de criar componentes puramente de forma declarativa sem conhecimento de Python

**Abordagem da solução:**
- Estender lógica de descoberta para detectar `config.yaml` e usar `ConfigGenerator` quando não há arquivo Python
- Fazer scaffolding pular opcionalmente a geração de arquivo Python (padrão: apenas YAML)
- Atualizar exemplos para demonstrar ambos os padrões (apenas YAML para simples, Python para avançado)

## Estratégia de Isolamento de Mudanças
- **Princípio de isolamento:** Adicionar caminho de descoberta apenas YAML junto ao caminho factory Python existente, nunca quebrando comportamento existente
- **Padrão de extensão:** Melhorar funções `discover_*()` com fallback para ConfigGenerator quando `.py` está faltando
- **Garantia de estabilidade:** Projetos existentes com factories Python continuam funcionando inalterados; apenas novos projetos apenas YAML se beneficiam

## Critérios de Sucesso
✅ `hive create agent my-bot` cria apenas `config.yaml` por padrão (sem `agent.py`)
✅ `hive create agent my-bot --with-python` cria ambos os arquivos para usuários avançados
✅ Sistema de descoberta carrega agentes de diretórios apenas YAML com sucesso
✅ Agentes template de exemplo demonstram padrão apenas YAML na documentação
✅ Agentes existentes baseados em Python (como exemplos atuais) continuam funcionando
✅ Cobertura completa de testes para descoberta mista (alguns apenas YAML, alguns com Python)

## Nunca Fazer (Limites de Proteção)
❌ Remover ou quebrar suporte a factory Python existente (compatibilidade retroativa crítica)
❌ Modificar internos de `hive/scaffolder/generator.py` (já está pronto para produção)
❌ Mudar schema YAML de agent/team/workflow (ConfigGenerator espera formato atual)
❌ Pular validação ao carregar componentes apenas YAML (manter portões de qualidade)

## Arquitetura Técnica

### Estrutura de Componentes
Camada de Descoberta:
├── hive/discovery.py                    # Melhorado para suportar caminhos apenas YAML + factory Python
│   ├── discover_agents()                # Linha 36-141: Adicionar fallback ConfigGenerator
│   ├── discover_teams()                 # Linha 241-335: Adicionar fallback ConfigGenerator
│   └── discover_workflows()             # Linha 144-238: Adicionar fallback ConfigGenerator

Camada de Scaffolding:
├── hive/cli/create.py                   # Adicionar flag --with-python, padrão apenas YAML
│   ├── agent()                          # Linha 16-52: Geração opcional de Python
│   ├── team()                           # Linha 54-93: Geração opcional de Python
│   └── workflow()                       # Linha 96-130: Geração opcional de Python

Gerador (Sem Mudanças Necessárias):
└── hive/scaffolder/generator.py         # Já suporta conversão YAML → Componente
    ├── generate_agent_from_yaml()       # Linha 32-128: Reusar como está
    ├── generate_team_from_yaml()        # Linha 131-217: Reusar como está
    └── generate_workflow_from_yaml()    # Linha 220-300: Reusar como está

Testes:
├── tests/hive/discovery/                # Novo diretório de testes
│   ├── test_yaml_only_discovery.py      # Carregamento de componentes apenas YAML
│   ├── test_python_factory_discovery.py # Padrão Python existente (regressão)
│   └── test_mixed_discovery.py          # Ambos padrões coexistindo
└── tests/hive/cli/
    └── test_create_yaml_only.py         # Comportamento de flags CLI

### Convenções de Nomenclatura
- Flag CLI: `--with-python` (opt-in para usuários avançados)
- Funções de descoberta: Manter nomes existentes, melhorar implementação
- Métodos auxiliares: `_try_load_from_yaml()`, `_try_load_from_python()`
- Arquivos de teste: `test_yaml_only_*.py`, `test_mixed_*.py`

## Decomposição de Tarefas

### Grafo de Dependências
```
A[Melhoria de Descoberta] <--- Base independente
B[Atualização Scaffolding CLI] <--- Melhoria UX independente
A & B ---> C[Testes & Exemplos]
C ---> D[Documentação]
```

### Grupo A: Melhoria de Descoberta (Tarefa Única)
Dependências: Nenhuma | Melhorar lógica de descoberta para suportar componentes apenas YAML

**A1-discovery-yaml-fallback**: @hive/discovery.py [contexto]
**Cria:** Funções `discover_*()` melhoradas com carregamento de caminho duplo
**Exporta:** Descoberta retrocompatível suportando ambos os padrões
**Padrão de Implementação:**
```python
# Descoberta melhorada em hive/discovery.py (exemplo para agentes)
def discover_agents() -> list[Agent]:
    agents: list[Agent] = []
    # ... configuração de diretório existente ...

    for agent_path in scan_dir.iterdir():
        if not agent_path.is_dir() or agent_path.name.startswith("_"):
            continue

        # Tentar factory Python primeiro (comportamento existente)
        factory_file = agent_path / "agent.py"
        if factory_file.exists():
            # Carregamento factory Python existente (linhas 104-138)
            agents.append(_load_from_python_factory(factory_file, agent_path))
            continue

        # Fallback: Tentar carregamento apenas YAML
        config_file = agent_path / "config.yaml"
        if config_file.exists():
            try:
                from hive.scaffolder.generator import generate_agent_from_yaml
                agent = generate_agent_from_yaml(str(config_file))
                agents.append(agent)
                agent_id = getattr(agent, "id", agent.name)
                print(f"  ✅ Agente carregado (apenas YAML): {agent.name} (id: {agent_id})")
            except Exception as e:
                print(f"  ❌ Falha ao carregar agente YAML de {agent_path.name}: {e}")
                continue
        else:
            print(f"  ⏭️  Pulando {agent_path.name} (sem agent.py ou config.yaml)")

    return agents
```
**Critérios de Sucesso:**
- Agentes apenas YAML carregam com sucesso junto a agentes factory Python
- Mensagens de erro distinguem entre falhas factory Python e YAML
- Descoberta baseada em Python existente inalterada (testes de regressão passam)

### Grupo B: Atualização Scaffolding CLI (Tarefas Paralelas)
Dependências: Nenhuma | Melhorias CLI independentes de mudanças de descoberta

**B1-cli-create-flag**: @hive/cli/create.py [contexto]
**Modifica:** Adicionar flag `--with-python` aos comandos `agent()`, `team()`, `workflow()`
**Implementação:**
```python
# hive/cli/create.py (exemplo para comando agent)
@create_app.command()
def agent(
    name: str = typer.Argument(..., help="Nome do agente (kebab-case)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Descrição do agente"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="Modelo LLM a usar"),
    with_python: bool = typer.Option(False, "--with-python", help="Gerar factory agent.py (avançado)"),
):
    """Criar um novo agente com configuração YAML."""
    # ... validação existente e criação de diretório ...

    # Gerar config.yaml (sempre)
    _generate_agent_config(agent_path, name, description or f"{name.replace('-', ' ').title()} Agent", model)

    # Gerar agent.py apenas se solicitado
    if with_python:
        _generate_agent_python(agent_path, name, model)
        files_created = [
            f"{CLI_EMOJIS['file']} {agent_path}/config.yaml",
            f"{CLI_EMOJIS['file']} {agent_path}/agent.py (avançado)",
        ]
    else:
        files_created = [f"{CLI_EMOJIS['file']} {agent_path}/config.yaml"]

    _show_agent_success(name, agent_path, files_created, with_python)
```
**Critérios de Sucesso:**
- Padrão `hive create agent my-bot` cria apenas `config.yaml`
- `hive create agent my-bot --with-python` cria ambos os arquivos
- Mensagens de sucesso indicam claramente qual padrão foi usado

**B2-cli-config-generation**: @hive/cli/create.py [contexto]
**Modifica:** Dividir `_generate_agent_files()` em `_generate_agent_config()` + `_generate_agent_python()`
**Exporta:** Funções separadas para geração YAML e Python
**Implementação:**
```python
def _generate_agent_config(agent_path: Path, name: str, description: str, model: str):
    """Gerar configuração de agente apenas YAML."""
    config_content = f"""agent:
  name: "{description}"
  id: "{name}"
  version: "1.0.0"
  description: "{description}"
  model: "openai:{model}"

instructions: |
  Você é {description}.

  [Adicione suas instruções de agente aqui]

storage:
  type: "postgres"
  table_name: "{name.replace("-", "_")}_sessions"
  auto_upgrade_schema: true
"""
    (agent_path / "config.yaml").write_text(config_content)


def _generate_agent_python(agent_path: Path, name: str, model: str):
    """Gerar factory Python (padrão avançado)."""
    # Código de geração agent.py existente da linha 200-239
    # ... (manter template factory Python existente) ...
```
**Critérios de Sucesso:**
- Config YAML inclui formato correto de `model:` (`provider:model_id`)
- Factory Python referencia `config.yaml` quando gerado
- Ambas funções mantêm compatibilidade de estrutura YAML existente

**B3-cli-success-messages**: @hive/cli/create.py [contexto]
**Modifica:** Atualizar mensagens de painel de sucesso para refletir padrão usado
**Implementação:**
```python
def _show_agent_success(name: str, agent_path: Path, files_created: list[str], with_python: bool):
    """Mostrar mensagem de sucesso para criação de agente."""
    next_steps = [
        "1. Editar config.yaml para customizar seu agente",
        "2. Atualizar instruções em config.yaml",
        "3. Testar seu agente: [yellow]hive dev[/yellow]",
    ]

    if with_python:
        next_steps.insert(1, "2. Customizar agent.py para lógica avançada (opcional)")

    message = f"""Agente '{name}' criado com sucesso!

[bold cyan]Arquivos criados:[/bold cyan]
{chr(10).join(f"  {f}" for f in files_created)}

[bold cyan]Padrão:[/bold cyan] {"Factory Python (Avançado)" if with_python else "Apenas YAML (Recomendado)"}

[bold cyan]Próximos passos:[/bold cyan]
{chr(10).join(f"  {step}" for step in next_steps)}
"""
    panel = Panel(message, title=f"{CLI_EMOJIS['robot']} Agente Criado", border_style="green")
    console.print("\n")
    console.print(panel)
```
**Critérios de Sucesso:**
- Mensagens distinguem claramente padrão apenas YAML vs factory Python
- "Próximos passos" se adaptam baseado no padrão usado
- Usuários entendem quando Python é opcional

### Grupo C: Testes & Validação (Após A & B)
Dependências: A1-discovery-yaml-fallback, B1/B2/B3-cli-changes

**C1-discovery-tests**: @tests/hive/discovery/ [novo diretório]
**Cria:** Suite de testes abrangente para melhorias de descoberta
**Arquivos:**
- `tests/hive/discovery/test_yaml_only_discovery.py`
- `tests/hive/discovery/test_python_factory_discovery.py` (regressão)
- `tests/hive/discovery/test_mixed_discovery.py`

**Casos de Teste:**
```python
# test_yaml_only_discovery.py
def test_discover_yaml_only_agent(tmp_path):
    """Agente apenas YAML carrega sem agent.py."""
    agent_dir = tmp_path / "ai" / "agents" / "yaml-bot"
    agent_dir.mkdir(parents=True)

    config = {
        "agent": {"name": "YAML Bot", "id": "yaml-bot", "model": "openai:gpt-4o-mini"},
        "instructions": "Você é um agente apenas YAML."
    }
    (agent_dir / "config.yaml").write_text(yaml.dump(config))

    # Descoberta deve carregar
    agents = discover_agents()
    assert len(agents) == 1
    assert agents[0].name == "YAML Bot"
    assert agents[0].id == "yaml-bot"


def test_discover_mixed_agents(tmp_path):
    """Tanto agentes apenas YAML quanto factory Python coexistem."""
    # Criar agente apenas YAML
    yaml_dir = tmp_path / "ai" / "agents" / "yaml-bot"
    yaml_dir.mkdir(parents=True)
    (yaml_dir / "config.yaml").write_text(yaml.dump({...}))

    # Criar agente factory Python
    python_dir = tmp_path / "ai" / "agents" / "python-bot"
    python_dir.mkdir(parents=True)
    (python_dir / "config.yaml").write_text(yaml.dump({...}))
    (python_dir / "agent.py").write_text("""
def get_python_bot_agent(**kwargs):
    return Agent(name="Python Bot", ...)
""")

    agents = discover_agents()
    assert len(agents) == 2
    names = {a.name for a in agents}
    assert names == {"YAML Bot", "Python Bot"}


def test_python_factory_takes_precedence(tmp_path):
    """Quando ambos existem, factory Python é usado (compatibilidade retroativa)."""
    agent_dir = tmp_path / "ai" / "agents" / "hybrid-bot"
    agent_dir.mkdir(parents=True)

    # Ambos arquivos existem
    (agent_dir / "config.yaml").write_text(yaml.dump({
        "agent": {"name": "Nome YAML", ...}
    }))
    (agent_dir / "agent.py").write_text("""
def get_hybrid_bot_agent(**kwargs):
    return Agent(name="Nome Python", ...)
""")

    agents = discover_agents()
    # Factory Python deve ganhar
    assert agents[0].name == "Nome Python"
```

**C2-cli-create-tests**: @tests/hive/cli/test_create_yaml_only.py [novo arquivo]
**Cria:** Testes de comportamento de comando CLI
**Casos de Teste:**
```python
def test_create_agent_yaml_only_default(cli_runner, tmp_path):
    """Padrão cria agente apenas YAML."""
    result = cli_runner(["create", "agent", "my-bot"])

    agent_path = tmp_path / "ai" / "agents" / "my-bot"
    assert (agent_path / "config.yaml").exists()
    assert not (agent_path / "agent.py").exists()
    assert result.exit_code == 0
    assert "Apenas YAML (Recomendado)" in result.output


def test_create_agent_with_python_flag(cli_runner, tmp_path):
    """--with-python cria ambos arquivos."""
    result = cli_runner(["create", "agent", "my-bot", "--with-python"])

    agent_path = tmp_path / "ai" / "agents" / "my-bot"
    assert (agent_path / "config.yaml").exists()
    assert (agent_path / "agent.py").exists()
    assert result.exit_code == 0
    assert "Factory Python (Avançado)" in result.output


def test_yaml_only_agent_runnable(cli_runner, tmp_path):
    """Agente apenas YAML funciona no servidor dev."""
    # Criar agente apenas YAML
    cli_runner(["create", "agent", "test-bot"])

    # Iniciar servidor dev (mockado)
    # Verificar agente aparece no registro
    # Testar endpoint run
    pass
```

**C3-example-updates**: @hive/examples/agents/ [contexto]
**Modifica:** Atualizar agentes de exemplo para demonstrar padrão apenas YAML
**Mudanças:**
- Converter `support-bot` para apenas YAML (remover `agent.py`)
- Manter `code-reviewer` como exemplo factory Python (padrão avançado)
- Adicionar `README.md` em examples explicando ambos os padrões

**Estrutura de Exemplo:**
```
hive/examples/agents/
├── README.md                      # Guia de padrões
├── support-bot/                   # Exemplo apenas YAML
│   └── config.yaml
├── code-reviewer/                 # Exemplo factory Python
│   ├── config.yaml
│   └── agent.py
└── researcher/                    # Exemplo apenas YAML
    └── config.yaml
```

**Critérios de Sucesso:**
- Todos testes passam: `uv run pytest tests/hive/discovery/ tests/hive/cli/test_create_yaml_only.py -v`
- Cobertura ≥90% para novos caminhos de descoberta
- Exemplos demonstram ambos padrões claramente

### Grupo D: Documentação (Após C)
Dependências: Testes completos e atualizações de exemplos

**D1-readme-update**: @README.md [contexto]
**Modifica:** Adicionar documentação de padrão apenas YAML na seção "Quick Start"
**Adição de Conteúdo:**
```markdown
### Crie Seu Primeiro Agente (30 segundos)

**Padrão Apenas YAML (Recomendado para Iniciantes):**
```bash
# Criar agente com apenas config YAML
hive create agent my-bot

# Editar config
cat ai/agents/my-bot/config.yaml

# Iniciar servidor dev
hive dev
```

**Padrão Avançado (Factories Python):**
```bash
# Criar agente com customização Python
hive create agent my-bot --with-python

# Agora você pode customizar ai/agents/my-bot/agent.py
# para carregamento avançado de ferramentas, instruções dinâmicas, etc.
```
```

**D2-claude-md-update**: @CLAUDE.md [contexto]
**Modifica:** Documentar padrão apenas YAML na seção de arquitetura
**Conteúdo:**
```markdown
## Padrões de Desenvolvimento de Agentes

### Padrão Apenas YAML (Recomendado)
- **Quando usar:** Agentes simples com configuração estática
- **Estrutura:** `ai/agents/{name}/config.yaml` apenas
- **Descoberta:** Automática via `ConfigGenerator.generate_agent_from_yaml()`
- **Exemplo:** `hive/examples/agents/support-bot/`

### Padrão Factory Python (Avançado)
- **Quando usar:** Carregamento dinâmico de ferramentas, inicialização customizada, lógica runtime
- **Estrutura:** `ai/agents/{name}/config.yaml` + `agent.py`
- **Descoberta:** Factory Python tem precedência quando ambos existem
- **Exemplo:** `hive/examples/agents/code-reviewer/`
```

**Critérios de Sucesso:**
- Documentação explica claramente quando usar cada padrão
- Quick start reflete apenas YAML como caminho padrão
- Caminho de migração de apenas YAML → factory Python documentado

## Exemplos de Implementação

### Padrão de Melhoria de Descoberta
```python
# hive/discovery.py - discover_agents() melhorado
def discover_agents() -> list[Agent]:
    """Descobrir agentes de padrão apenas YAML OU factory Python."""
    agents: list[Agent] = []

    # ... configuração de diretório existente (linhas 56-89) ...

    for agent_path in scan_dir.iterdir():
        if not agent_path.is_dir() or agent_path.name.startswith("_"):
            continue
        if agent_path.name == "examples":
            continue

        # Estratégia 1: Tentar factory Python primeiro (compatibilidade retroativa)
        factory_file = agent_path / "agent.py"
        if factory_file.exists():
            agent = _load_agent_from_python(factory_file, agent_path)
            if agent:
                agents.append(agent)
                continue

        # Estratégia 2: Fallback para carregamento apenas YAML
        config_file = agent_path / "config.yaml"
        if config_file.exists():
            agent = _load_agent_from_yaml(config_file, agent_path)
            if agent:
                agents.append(agent)
                continue

        # Nenhum encontrado
        print(f"  ⏭️  Pulando {agent_path.name} (sem agent.py ou config.yaml)")

    print(f"\n🎯 Total de agentes carregados: {len(agents)}")
    return agents


def _load_agent_from_python(factory_file: Path, agent_path: Path) -> Agent | None:
    """Carregar agente usando factory Python (comportamento existente)."""
    try:
        # Código existente das linhas 104-138
        spec = importlib.util.spec_from_file_location(f"hive.agents.{agent_path.name}", factory_file)
        if spec is None or spec.loader is None:
            print(f"  ❌ Falha ao carregar spec para {agent_path.name}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Encontrar função factory
        for name in dir(module):
            if name.startswith("get_") and callable(getattr(module, name)):
                factory = getattr(module, name)
                try:
                    result = factory()
                    if isinstance(result, Agent):
                        agent_id = getattr(result, "id", result.name)
                        print(f"  ✅ Agente carregado (Python): {result.name} (id: {agent_id})")
                        return result
                except Exception as e:
                    print(f"  ⚠️  Factory {name} falhou: {e}")
                    continue

        print(f"  ⚠️  Nenhuma função factory encontrada em {agent_path.name}/agent.py")
        return None
    except Exception as e:
        print(f"  ❌ Falha ao carregar agente Python de {agent_path.name}: {e}")
        return None


def _load_agent_from_yaml(config_file: Path, agent_path: Path) -> Agent | None:
    """Carregar agente usando padrão apenas YAML (nova funcionalidade)."""
    try:
        from hive.scaffolder.generator import generate_agent_from_yaml

        agent = generate_agent_from_yaml(str(config_file), validate=True)
        agent_id = getattr(agent, "id", agent.name)
        print(f"  ✅ Agente carregado (apenas YAML): {agent.name} (id: {agent_id})")
        return agent
    except Exception as e:
        print(f"  ❌ Falha ao carregar agente YAML de {agent_path.name}: {e}")
        return None
```

### Padrão CLI (Apenas YAML por Padrão)
```python
# hive/cli/create.py - Criação de agente melhorada
@create_app.command()
def agent(
    name: str = typer.Argument(..., help="Nome do agente (kebab-case)"),
    description: str | None = typer.Option(None, "--description", "-d", help="Descrição do agente"),
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="Modelo LLM a usar"),
    with_python: bool = typer.Option(False, "--with-python", help="Gerar agent.py (usuários avançados)"),
):
    """Criar um novo agente - apenas YAML por padrão."""
    # ... validação e criação de diretório (existente) ...

    # Sempre gerar config.yaml
    _generate_agent_config(agent_path, name, description or f"{name.replace('-', ' ').title()} Agent", model)

    files_created = [f"{CLI_EMOJIS['file']} {agent_path}/config.yaml"]

    # Opcionalmente gerar agent.py
    if with_python:
        _generate_agent_python(agent_path, name, model)
        files_created.append(f"{CLI_EMOJIS['file']} {agent_path}/agent.py")

    _show_agent_success(name, agent_path, files_created, with_python)


def _generate_agent_config(agent_path: Path, name: str, description: str, model: str):
    """Gerar configuração de agente apenas YAML (sempre criado)."""
    config_content = f"""agent:
  name: "{description}"
  id: "{name}"
  version: "1.0.0"
  description: "{description}"
  model: "openai:{model}"

instructions: |
  Você é {description}.

  [Adicione suas instruções de agente aqui]

storage:
  type: "postgres"
  table_name: "{name.replace("-", "_")}_sessions"
  auto_upgrade_schema: true
"""
    (agent_path / "config.yaml").write_text(config_content)


def _generate_agent_python(agent_path: Path, name: str, model: str):
    """Gerar factory Python para customização avançada (opcional)."""
    # Manter geração factory Python existente das linhas 200-239
    agent_py_content = f'''"""Factory de agente para {name} (padrão avançado)."""

import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_{name.replace("-", "_")}_agent(**kwargs) -> Agent:
    """Criar agente {name} com lógica customizada."""
    # Carregar config base do YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Lógica de inicialização customizada aqui
    # Exemplo: carregamento dinâmico de ferramentas, seleção de modelo runtime, etc.

    agent_config = config.get("agent", {{}})
    model_config = config.get("model", {{}})

    model = OpenAIChat(
        id=model_config.get("id", "{model}"),
        temperature=model_config.get("temperature", 0.7),
    )

    agent = Agent(
        name=agent_config.get("name"),
        model=model,
        instructions=config.get("instructions"),
        description=agent_config.get("description"),
        **kwargs
    )

    if agent_config.get("id"):
        agent.id = agent_config.get("id")

    return agent
'''
    (agent_path / "agent.py").write_text(agent_py_content)
```

## Protocolo de Testes
```bash
# Testes de descoberta (nova funcionalidade)
uv run pytest tests/hive/discovery/test_yaml_only_discovery.py -v
uv run pytest tests/hive/discovery/test_mixed_discovery.py -v

# Testes de regressão (factories Python existentes ainda funcionam)
uv run pytest tests/hive/discovery/test_python_factory_discovery.py -v

# Testes CLI (apenas YAML por padrão)
uv run pytest tests/hive/cli/test_create_yaml_only.py -v

# Testes de integração (end-to-end)
uv run pytest tests/integration/test_yaml_only_workflow.py -v

# Suite completa
uv run pytest tests/hive/discovery/ tests/hive/cli/ -v --cov=hive/discovery --cov=hive/cli/create

# Análise estática
uv run ruff check hive/discovery.py hive/cli/create.py
uv run mypy hive/discovery.py hive/cli/create.py
```

## Checklist de Validação
- [ ] Agentes apenas YAML carregam sem `agent.py`
- [ ] Agentes factory Python ainda funcionam (compatibilidade retroativa)
- [ ] Projetos mistos (alguns YAML, alguns Python) funcionam corretamente
- [ ] Flag `--with-python` gera ambos os arquivos
- [ ] Comportamento padrão é apenas YAML (sem flag = sem arquivo Python)
- [ ] Mensagens de erro distinguem falhas de carregamento YAML vs Python
- [ ] Exemplos demonstram ambos padrões claramente
- [ ] Documentação explica quando usar cada padrão
- [ ] Todos testes existentes passam (sem regressões)
- [ ] Novos testes alcançam ≥90% de cobertura das mudanças de descoberta

## Caminho de Migração

### Para Usuários Existentes (Nenhuma Ação Necessária)
- Agentes factory Python continuam funcionando inalterados
- Sistema de descoberta prioriza factories Python quando ambos arquivos existem
- Sem mudanças que quebrem projetos existentes

### Para Novos Usuários (Padrão Apenas YAML)
```bash
# Começar com apenas YAML (simples)
hive create agent my-bot
# Editar config.yaml, iniciar servidor dev

# Atualizar para factory Python mais tarde se necessário
hive create agent my-bot --with-python  # Adiciona agent.py junto ao config.yaml
```

### Convertendo Factories Python Existentes para Apenas YAML
```bash
# Se agent.py apenas carrega config.yaml sem lógica customizada:
cd ai/agents/my-bot
rm agent.py  # Descoberta usará automaticamente carregador apenas YAML
```

## Avaliação de Riscos

### Baixo Risco
- Adicionar caminho apenas YAML não modifica lógica factory Python existente
- Ordem de descoberta (Python → YAML) garante compatibilidade retroativa
- Flag CLI é opt-in para geração Python

### Risco Médio
- Nova dependência em `ConfigGenerator` na camada de descoberta
- Potencial diferença de performance entre factory Python vs carregamento YAML
- Mensagens de erro podem confundir usuários se ambos arquivos existem com configs diferentes

### Mitigação
- Cobertura de testes abrangente (90%+) valida ambos caminhos
- Testes de performance garantem carregamento YAML aceitável (<100ms por agente)
- Documentação afirma claramente que factory Python tem precedência
- Tratamento de erros distingue entre estratégias de carregamento

## Questões Abertas para Revisão do Usuário

1. **Comportamento Padrão:** Deve ser apenas YAML o padrão, ou manter padrão factory Python atual com flag `--yaml-only` ao invés?
   - **Recomendação:** Padrão apenas YAML (mais simples para iniciantes, alinha com visão)

2. **Estratégia de Migração:** Devemos fornecer ferramenta para converter factories Python → apenas YAML automaticamente?
   - **Recomendação:** Documentar processo manual primeiro, adicionar ferramenta se usuários solicitarem

3. **Distribuição de Exemplos:** Devem exemplos embutidos ser todos apenas YAML, todos Python, ou mistos?
   - **Recomendação:** Mistos (2 apenas YAML, 1 factory Python) para demonstrar ambos padrões

4. **Performance:** Devem agentes apenas YAML ser cacheados após primeiro carregamento para igualar performance factory Python?
   - **Recomendação:** Perfilar primeiro, otimizar se carregamento >100ms por agente
