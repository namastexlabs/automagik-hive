# 🧪 Guia de Testes - Agentes YAML-Only

**Versão:** 1.0.0
**Data:** 2025-11-06
**Funcionalidade:** Criação de agentes usando apenas YAML (sem necessidade de Python)

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Teste 1: Criar Agente YAML-Only (Padrão)](#teste-1-criar-agente-yaml-only-padrão)
3. [Teste 2: Criar Agente com Python Factory](#teste-2-criar-agente-com-python-factory)
4. [Teste 3: Descoberta Automática de Agentes](#teste-3-descoberta-automática-de-agentes)
5. [Teste 4: Agentes Mistos (YAML + Python)](#teste-4-agentes-mistos-yaml--python)
6. [Teste 5: Exemplos Incluídos](#teste-5-exemplos-incluídos)
7. [Teste 6: Migração de Padrões](#teste-6-migração-de-padrões)
8. [Teste 7: Integração Completa](#teste-7-integração-completa)
9. [Solução de Problemas](#solução-de-problemas)

---

## Pré-requisitos

### Ambiente de Desenvolvimento

```bash
# 1. Verificar que está no diretório correto
pwd
# Deve mostrar: /Users/caiorod/Documents/Namastex/automagik-hive

# 2. Verificar branch
git branch
# Deve estar em: wish/yaml-only-agents

# 3. Verificar status git
git status
# Deve mostrar as mudanças dos grupos A, B, C, D

# 4. Sincronizar dependências
uv sync

# 5. Verificar que .env existe
ls -la .env
# Se não existir:
cp .env.example .env
# Edite .env e adicione suas chaves de API
```

### Chaves de API Necessárias

Edite `.env` e adicione pelo menos uma chave:

```bash
# Pelo menos uma destas:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

### Limpar Testes Anteriores

```bash
# Remover agentes de teste antigos (se existirem)
rm -rf ai/agents/teste-*
rm -rf ai/agents/my-bot*
rm -rf ai/agents/yaml-*
rm -rf ai/agents/python-*

# Verificar limpeza
ls ai/agents/
# Deve mostrar apenas diretórios exemplo
```

---

## Teste 1: Criar Agente YAML-Only (Padrão)

### Objetivo
Verificar que o comando padrão `hive create agent` cria apenas o arquivo `config.yaml` (sem `agent.py`).

### Passos

#### 1.1 Criar Agente YAML-Only

```bash
# Criar agente de teste
hive create agent teste-yaml
```

**Resultado Esperado:**
```
✨ Creating agent: teste-yaml

Agent 'teste-yaml' created successfully!

Files created:
  📄 ai/agents/teste-yaml/config.yaml

Pattern: YAML-Only (Recommended)

Next steps:
  1. Edit config.yaml to customize your agent
  2. Update instructions in config.yaml
  3. Test your agent: hive dev
```

#### 1.2 Verificar Estrutura de Arquivos

```bash
# Listar arquivos criados
ls -la ai/agents/teste-yaml/

# Resultado esperado:
# drwxr-xr-x  3 user  staff   96 Nov  6 20:00 .
# drwxr-xr-x  8 user  staff  256 Nov  6 20:00 ..
# -rw-r--r--  1 user  staff  XXX Nov  6 20:00 config.yaml
```

**✅ Verificação:** Deve existir APENAS `config.yaml`, SEM `agent.py`

#### 1.3 Verificar Conteúdo do config.yaml

```bash
# Visualizar conteúdo
cat ai/agents/teste-yaml/config.yaml
```

**Resultado Esperado:**
```yaml
agent:
  name: "Teste Yaml Agent"
  id: "teste-yaml"
  version: "1.0.0"
  description: "Teste Yaml Agent"
  model: "openai:gpt-4o-mini"

instructions: |
  You are Teste Yaml Agent.

  [Add your agent instructions here]

storage:
  type: "postgres"
  table_name: "teste_yaml_sessions"
  auto_upgrade_schema: true
```

**✅ Verificações:**
- [ ] Campo `agent.id` = "teste-yaml"
- [ ] Campo `agent.model` está no formato "provider:model_id"
- [ ] Campo `instructions` está presente
- [ ] Campo `storage.table_name` usa underscore (teste_yaml)

#### 1.4 Testar Descoberta do Agente

```bash
# Testar descoberta via Python
uv run python -c "
from hive.discovery import discover_agents

agents = discover_agents()
print(f'Total de agentes descobertos: {len(agents)}')

# Procurar nosso agente de teste
for agent in agents:
    if agent.id == 'teste-yaml':
        print(f'✅ Agente encontrado: {agent.name}')
        print(f'   ID: {agent.id}')
        print(f'   Modelo: {agent.model}')
        break
else:
    print('❌ Agente teste-yaml NÃO foi descoberto')
"
```

**Resultado Esperado:**
```
  ✅ Loaded agent (YAML-only): Teste Yaml Agent (id: teste-yaml)
...
Total de agentes descobertos: X
✅ Agente encontrado: Teste Yaml Agent
   ID: teste-yaml
   Modelo: <modelo_info>
```

**✅ Verificação:** Mensagem deve mostrar "Loaded agent (YAML-only)"

---

## Teste 2: Criar Agente com Python Factory

### Objetivo
Verificar que a flag `--with-python` cria AMBOS os arquivos: `config.yaml` E `agent.py`.

### Passos

#### 2.1 Criar Agente com Flag --with-python

```bash
# Criar agente com Python factory
hive create agent teste-python --with-python
```

**Resultado Esperado:**
```
✨ Creating agent: teste-python

Agent 'teste-python' created successfully!

Files created:
  📄 ai/agents/teste-python/config.yaml
  📄 ai/agents/teste-python/agent.py (advanced)

Pattern: Python Factory (Advanced)

Next steps:
  1. Edit config.yaml to customize your agent
  2. Customize agent.py for advanced logic (optional)
  3. Update instructions in config.yaml
  4. Test your agent: hive dev
```

#### 2.2 Verificar Estrutura de Arquivos

```bash
# Listar arquivos criados
ls -la ai/agents/teste-python/

# Resultado esperado:
# drwxr-xr-x  4 user  staff  128 Nov  6 20:05 .
# drwxr-xr-x  9 user  staff  288 Nov  6 20:05 ..
# -rw-r--r--  1 user  staff  XXX Nov  6 20:05 agent.py
# -rw-r--r--  1 user  staff  XXX Nov  6 20:05 config.yaml
```

**✅ Verificação:** Devem existir AMBOS `config.yaml` E `agent.py`

#### 2.3 Verificar Conteúdo do agent.py

```bash
# Visualizar conteúdo
cat ai/agents/teste-python/agent.py
```

**Resultado Esperado:**
```python
"""Agent factory for teste-python (advanced pattern)."""

import yaml
from pathlib import Path
from agno.agent import Agent
from agno.models.openai import OpenAIChat


def get_teste_python_agent(**kwargs) -> Agent:
    """Create teste-python agent with custom logic."""
    # Load base config from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Custom initialization logic here
    # ...

    agent = Agent(
        name=config["agent"]["name"],
        model=...,
        instructions=config.get("instructions"),
        description=config["agent"].get("description"),
        **kwargs
    )

    if config["agent"].get("id"):
        agent.id = config["agent"].get("id")

    return agent
```

**✅ Verificações:**
- [ ] Função nomeada `get_teste_python_agent` (usa underscore)
- [ ] Carrega `config.yaml` do mesmo diretório
- [ ] Aceita `**kwargs` para sobrescritas runtime
- [ ] Define `agent.id` como atributo de instância

#### 2.4 Testar Descoberta do Agente Python

```bash
# Testar descoberta via Python
uv run python -c "
from hive.discovery import discover_agents

agents = discover_agents()

# Procurar nosso agente Python
for agent in agents:
    if agent.id == 'teste-python':
        print(f'✅ Agente encontrado: {agent.name}')
        print(f'   ID: {agent.id}')
        print(f'   Tipo: Python Factory')
        break
else:
    print('❌ Agente teste-python NÃO foi descoberto')
"
```

**Resultado Esperado:**
```
  ✅ Loaded agent (Python): Teste Python Agent (id: teste-python)
...
✅ Agente encontrado: Teste Python Agent
   ID: teste-python
   Tipo: Python Factory
```

**✅ Verificação:** Mensagem deve mostrar "Loaded agent (Python)"

---

## Teste 3: Descoberta Automática de Agentes

### Objetivo
Verificar que o sistema de descoberta carrega corretamente agentes YAML-only E Python factory.

### Passos

#### 3.1 Listar Todos os Agentes Descobertos

```bash
# Script de descoberta completo
uv run python -c "
from hive.discovery import discover_agents

print('🔍 Iniciando descoberta de agentes...\n')

agents = discover_agents()

print(f'\n📊 Resumo da Descoberta:')
print(f'   Total de agentes: {len(agents)}')
print(f'\n📋 Lista de Agentes:\n')

for agent in agents:
    agent_id = getattr(agent, 'id', 'N/A')
    print(f'   • {agent.name}')
    print(f'     ID: {agent_id}')
    print(f'     Modelo: {agent.model.id if hasattr(agent.model, \"id\") else \"N/A\"}')
    print()
"
```

**Resultado Esperado:**
```
🔍 Iniciando descoberta de agentes...

  ✅ Loaded agent (YAML-only): Teste Yaml Agent (id: teste-yaml)
  ✅ Loaded agent (Python): Teste Python Agent (id: teste-python)
  ✅ Loaded agent (YAML-only): researcher (id: researcher)
  ...

📊 Resumo da Descoberta:
   Total de agentes: X

📋 Lista de Agentes:

   • Teste Yaml Agent
     ID: teste-yaml
     Modelo: gpt-4o-mini

   • Teste Python Agent
     ID: teste-python
     Modelo: gpt-4o-mini

   • researcher
     ID: researcher
     Modelo: gpt-4o
   ...
```

**✅ Verificações:**
- [ ] Agentes YAML-only aparecem com mensagem "(YAML-only)"
- [ ] Agentes Python aparecem com mensagem "(Python)"
- [ ] Todos os agentes foram descobertos sem erros
- [ ] IDs estão corretos

#### 3.2 Verificar Ordem de Precedência (Python > YAML)

```bash
# Criar cenário de teste: agente com AMBOS os arquivos
mkdir -p ai/agents/teste-hibrido

# Criar config.yaml
cat > ai/agents/teste-hibrido/config.yaml << 'EOF'
agent:
  name: "Nome YAML"
  id: "teste-hibrido"
  version: "1.0.0"
  model: "openai:gpt-4o-mini"

instructions: "Instruções do YAML"
EOF

# Criar agent.py
cat > ai/agents/teste-hibrido/agent.py << 'EOF'
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_teste_hibrido_agent(**kwargs):
    agent = Agent(
        name="Nome Python",
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions="Instruções do Python",
        **kwargs
    )
    agent.id = "teste-hibrido"
    return agent
EOF

# Testar qual tem precedência
uv run python -c "
from hive.discovery import discover_agents

agents = discover_agents()

for agent in agents:
    if agent.id == 'teste-hibrido':
        print(f'Nome do agente: {agent.name}')
        print(f'Instruções: {agent.instructions[:30]}...')
        break
"
```

**Resultado Esperado:**
```
  ✅ Loaded agent (Python): Nome Python (id: teste-hibrido)

Nome do agente: Nome Python
Instruções: Instruções do Python...
```

**✅ Verificação:** Quando AMBOS os arquivos existem, Python factory tem PRECEDÊNCIA

#### 3.3 Limpar Teste de Precedência

```bash
# Remover agente de teste
rm -rf ai/agents/teste-hibrido
```

---

## Teste 4: Agentes Mistos (YAML + Python)

### Objetivo
Verificar que projetos podem ter AMBOS os tipos de agentes coexistindo.

### Passos

#### 4.1 Cenário de Projeto Misto

```bash
# Já temos:
# - teste-yaml (YAML-only)
# - teste-python (Python factory)
# - researcher (YAML-only, do exemplo)
# - support-bot (Python factory, do exemplo - se existir)

# Verificar estrutura
tree ai/agents/ -L 2 -I '__pycache__'
```

**Resultado Esperado:**
```
ai/agents/
├── teste-python/
│   ├── agent.py
│   └── config.yaml
├── teste-yaml/
│   └── config.yaml
└── ...
```

#### 4.2 Testar Descoberta Mista

```bash
# Verificar que todos são descobertos corretamente
uv run python -c "
from hive.discovery import discover_agents

agents = discover_agents()

yaml_only = []
python_factory = []

# Categorizar agentes
for agent in agents:
    agent_id = getattr(agent, 'id', 'unknown')
    if agent_id in ['teste-yaml', 'researcher']:
        yaml_only.append(agent.name)
    elif agent_id in ['teste-python', 'support-bot', 'code-reviewer']:
        python_factory.append(agent.name)

print(f'✅ Agentes YAML-Only: {len(yaml_only)}')
for name in yaml_only:
    print(f'   • {name}')

print(f'\n✅ Agentes Python Factory: {len(python_factory)}')
for name in python_factory:
    print(f'   • {name}')
"
```

**Resultado Esperado:**
```
✅ Agentes YAML-Only: 2
   • Teste Yaml Agent
   • researcher

✅ Agentes Python Factory: 2
   • Teste Python Agent
   • support-bot
```

**✅ Verificação:** Ambos os tipos coexistem sem conflitos

---

## Teste 5: Exemplos Incluídos

### Objetivo
Verificar que os agentes de exemplo demonstram ambos os padrões.

### Passos

#### 5.1 Verificar Estrutura de Exemplos

```bash
# Verificar exemplos incluídos
ls -la hive/examples/agents/
```

**Resultado Esperado:**
```
total XX
drwxr-xr-x  X user  staff  XXX Nov  6 20:00 .
drwxr-xr-x  X user  staff  XXX Nov  6 20:00 ..
-rw-r--r--  1 user  staff  XXX Nov  6 20:07 README.md
drwxr-xr-x  X user  staff  XXX Nov  6 20:00 code-reviewer/
drwxr-xr-x  X user  staff  XXX Nov  6 20:00 researcher/
drwxr-xr-x  X user  staff  XXX Nov  6 20:00 support-bot/
```

**✅ Verificação:** README.md existe (criado no Grupo C)

#### 5.2 Verificar Padrão do Researcher (YAML-only)

```bash
# Verificar estrutura do researcher
ls -la hive/examples/agents/researcher/

# Resultado esperado: APENAS config.yaml (sem agent.py)
```

**✅ Verificação:** researcher deve ser YAML-only (agent.py removido no Grupo C)

#### 5.3 Verificar Padrão do Support-Bot (Python Factory)

```bash
# Verificar estrutura do support-bot
ls -la hive/examples/agents/support-bot/

# Resultado esperado: config.yaml E agent.py
```

**✅ Verificação:** support-bot deve ter AMBOS os arquivos

#### 5.4 Ler README de Exemplos

```bash
# Visualizar README de exemplos
head -100 hive/examples/agents/README.md
```

**✅ Verificações:**
- [ ] README explica padrão YAML-only
- [ ] README explica padrão Python factory
- [ ] README tem matriz de decisão de padrões
- [ ] README documenta quando usar cada padrão

---

## Teste 6: Migração de Padrões

### Objetivo
Verificar os caminhos de migração entre YAML-only e Python factory.

### Passos

#### 6.1 Migração: YAML-only → Python Factory

```bash
# Começar com agente YAML-only
hive create agent teste-migracao

# Verificar que é YAML-only
ls ai/agents/teste-migracao/
# Resultado: apenas config.yaml

# Agora adicionar Python factory
cat > ai/agents/teste-migracao/agent.py << 'EOF'
"""Teste Migracao Agent Factory"""

from pathlib import Path
import yaml
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_teste_migracao_agent(**kwargs) -> Agent:
    """Create agent with custom logic."""
    # Load base config from YAML
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    agent = Agent(
        name=config["agent"]["name"],
        model=OpenAIChat(id="gpt-4o-mini"),
        instructions=config.get("instructions"),
        description=config["agent"].get("description"),
        **kwargs
    )
    agent.id = config["agent"]["id"]
    return agent
EOF

# Verificar descoberta agora usa Python
uv run python -c "
from hive.discovery import discover_agents
agents = discover_agents()
for agent in agents:
    if agent.id == 'teste-migracao':
        print('✅ Agora descoberto via Python Factory')
        break
"
```

**Resultado Esperado:**
```
  ✅ Loaded agent (Python): Teste Migracao Agent (id: teste-migracao)
✅ Agora descoberto via Python Factory
```

**✅ Verificação:** Migração para Python factory funciona

#### 6.2 Migração: Python Factory → YAML-only

```bash
# Remover agent.py
rm ai/agents/teste-migracao/agent.py

# Verificar que config.yaml ainda existe
ls ai/agents/teste-migracao/
# Resultado: apenas config.yaml

# Verificar descoberta volta para YAML-only
uv run python -c "
from hive.discovery import discover_agents
agents = discover_agents()
for agent in agents:
    if agent.id == 'teste-migracao':
        print('✅ Agora descoberto via YAML-only')
        break
"
```

**Resultado Esperado:**
```
  ✅ Loaded agent (YAML-only): Teste Migracao Agent (id: teste-migracao)
✅ Agora descoberto via YAML-only
```

**✅ Verificação:** Migração de volta para YAML-only funciona

---

## Teste 7: Integração Completa

### Objetivo
Testar agentes em execução real com o servidor de desenvolvimento.

### Passos

#### 7.1 Iniciar Servidor de Desenvolvimento

```bash
# Iniciar servidor em background
make dev &

# OU usar diretamente:
# hive dev &

# Aguardar servidor iniciar (10-15 segundos)
sleep 15

# Verificar que servidor está rodando
curl http://localhost:8886/api/v1/health
```

**Resultado Esperado:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-06T..."
}
```

#### 7.2 Listar Agentes via API

```bash
# Listar todos os agentes disponíveis
curl -s http://localhost:8886/agents | jq
```

**Resultado Esperado:**
```json
{
  "agents": [
    {
      "name": "Teste Yaml Agent",
      "id": "teste-yaml",
      "description": "Teste Yaml Agent",
      ...
    },
    {
      "name": "Teste Python Agent",
      "id": "teste-python",
      "description": "Teste Python Agent",
      ...
    },
    ...
  ]
}
```

**✅ Verificações:**
- [ ] Agentes YAML-only aparecem na lista
- [ ] Agentes Python factory aparecem na lista
- [ ] API retorna status 200

#### 7.3 Executar Agente YAML-only via API

```bash
# Testar agente YAML-only
curl -s -X POST http://localhost:8886/agents/teste-yaml/runs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá! Quem é você?"
  }' | jq
```

**Resultado Esperado:**
```json
{
  "run_id": "...",
  "agent_id": "teste-yaml",
  "messages": [
    {
      "role": "user",
      "content": "Olá! Quem é você?"
    },
    {
      "role": "assistant",
      "content": "Olá! Eu sou Teste Yaml Agent. ..."
    }
  ],
  ...
}
```

**✅ Verificação:** Agente YAML-only responde corretamente

#### 7.4 Executar Agente Python Factory via API

```bash
# Testar agente Python factory
curl -s -X POST http://localhost:8886/agents/teste-python/runs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Olá! Quem é você?"
  }' | jq
```

**Resultado Esperado:**
```json
{
  "run_id": "...",
  "agent_id": "teste-python",
  "messages": [
    {
      "role": "user",
      "content": "Olá! Quem é você?"
    },
    {
      "role": "assistant",
      "content": "Olá! Eu sou Teste Python Agent. ..."
    }
  ],
  ...
}
```

**✅ Verificação:** Agente Python factory responde corretamente

#### 7.5 Parar Servidor

```bash
# Parar servidor
make stop

# OU manualmente:
# pkill -f "uvicorn"
```

---

## Teste 8: Testes Automatizados

### Objetivo
Executar a suite de testes automatizados criada no Grupo C.

### Passos

#### 8.1 Testes de Descoberta YAML-only

```bash
# Executar testes de descoberta YAML-only
uv run pytest tests/hive/discovery/test_yaml_only_discovery.py -v
```

**Resultado Esperado:**
```
tests/hive/discovery/test_yaml_only_discovery.py::test_discover_yaml_only_agent PASSED
tests/hive/discovery/test_yaml_only_discovery.py::test_yaml_only_agent_without_agent_py PASSED
tests/hive/discovery/test_yaml_only_discovery.py::test_yaml_only_with_minimal_config PASSED
...

====== X passed in X.XXs ======
```

**✅ Verificação:** Todos os testes YAML-only devem PASSAR

#### 8.2 Testes de Descoberta Mista

```bash
# Executar testes de descoberta mista
uv run pytest tests/hive/discovery/test_mixed_discovery.py -v
```

**Resultado Esperado:**
```
tests/hive/discovery/test_mixed_discovery.py::test_discover_mixed_agents PASSED
tests/hive/discovery/test_mixed_discovery.py::test_python_factory_takes_precedence PASSED
...

====== X passed in X.XXs ======
```

**✅ Verificação:** Todos os testes de descoberta mista devem PASSAR

#### 8.3 Testes de Regressão (Python Factory)

```bash
# Executar testes de regressão
uv run pytest tests/integration/test_regression_python_factories.py -v
```

**Resultado Esperado:**
```
tests/integration/test_regression_python_factories.py::test_existing_python_factories_still_work PASSED
tests/integration/test_regression_python_factories.py::test_support_bot_discovery PASSED
...

====== X passed in X.XXs ======
```

**✅ Verificação:** Agentes Python existentes continuam funcionando (compatibilidade retroativa)

#### 8.4 Testes CLI

```bash
# Executar testes CLI
uv run pytest tests/hive/cli/test_create_yaml_only.py -v
```

**Resultado Esperado:**
```
tests/hive/cli/test_create_yaml_only.py::test_create_agent_yaml_only_default PASSED
tests/hive/cli/test_create_yaml_only.py::test_create_agent_with_python_flag PASSED
tests/hive/cli/test_create_yaml_only.py::test_yaml_only_creates_only_config PASSED
...

====== X passed in X.XXs ======
```

**✅ Verificação:** Testes CLI devem PASSAR

#### 8.5 Suite Completa

```bash
# Executar todos os testes relacionados
uv run pytest tests/hive/discovery/ tests/hive/cli/test_create_yaml_only.py -v
```

**Resultado Esperado:**
```
====== XX passed in X.XXs ======
```

**✅ Verificação:** TODOS os testes devem PASSAR

---

## Solução de Problemas

### Problema 1: Agente YAML-only não é descoberto

**Sintomas:**
```
⏭️  Skipping teste-yaml (no agent.py or config.yaml)
```

**Soluções:**

1. Verificar que `config.yaml` existe:
```bash
ls -la ai/agents/teste-yaml/config.yaml
```

2. Verificar sintaxe YAML:
```bash
uv run python -c "
import yaml
with open('ai/agents/teste-yaml/config.yaml') as f:
    config = yaml.safe_load(f)
    print('YAML válido:', config)
"
```

3. Verificar campos obrigatórios:
```bash
uv run python -c "
import yaml
with open('ai/agents/teste-yaml/config.yaml') as f:
    config = yaml.safe_load(f)
    assert 'agent' in config, 'Falta campo agent'
    assert 'name' in config['agent'], 'Falta agent.name'
    assert 'id' in config['agent'], 'Falta agent.id'
    print('✅ Campos obrigatórios presentes')
"
```

### Problema 2: Agente Python não é descoberto

**Sintomas:**
```
❌ No factory function found in teste-python/agent.py
```

**Soluções:**

1. Verificar nome da função:
```bash
grep "^def get_" ai/agents/teste-python/agent.py
```

Deve retornar: `def get_teste_python_agent(**kwargs):`

2. Verificar que função retorna Agent:
```bash
grep "return Agent" ai/agents/teste-python/agent.py
```

3. Verificar imports:
```bash
head -10 ai/agents/teste-python/agent.py
```

Deve ter:
```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
```

### Problema 3: Flag --with-python não funciona

**Sintomas:**
```
Error: no such option: --with-python
```

**Soluções:**

1. Verificar mudanças do Grupo B foram aplicadas:
```bash
grep "with_python" hive/cli/create.py
```

2. Verificar versão do CLI:
```bash
hive --version
```

3. Reinstalar:
```bash
uv sync --reinstall
```

### Problema 4: Servidor não inicia

**Sintomas:**
```
Error: Address already in use
```

**Soluções:**

1. Verificar porta ocupada:
```bash
lsof -i :8886
```

2. Matar processo:
```bash
pkill -f "uvicorn"
```

3. Tentar porta diferente:
```bash
hive dev --port 8887
```

### Problema 5: Testes falham

**Sintomas:**
```
FAILED tests/...
```

**Soluções:**

1. Limpar cache pytest:
```bash
rm -rf .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

2. Reinstalar dependências:
```bash
uv sync
```

3. Executar com mais detalhes:
```bash
uv run pytest tests/... -vv --tb=short
```

---

## Checklist Final de Validação

### Funcionalidades Básicas
- [ ] `hive create agent` cria apenas `config.yaml` (YAML-only)
- [ ] `hive create agent --with-python` cria `config.yaml` + `agent.py`
- [ ] Agentes YAML-only são descobertos automaticamente
- [ ] Agentes Python factory são descobertos automaticamente
- [ ] Mensagens de descoberta distinguem os tipos

### Compatibilidade
- [ ] Agentes Python existentes continuam funcionando
- [ ] Ambos os padrões podem coexistir no mesmo projeto
- [ ] Python factory tem precedência quando ambos arquivos existem

### Documentação
- [ ] README.md mostra YAML-only como padrão
- [ ] CLAUDE.md documenta ambos os padrões
- [ ] `hive/examples/agents/README.md` existe e está completo
- [ ] Exemplos demonstram ambos os padrões

### Testes
- [ ] Testes de descoberta YAML-only passam
- [ ] Testes de descoberta mista passam
- [ ] Testes de regressão Python passam
- [ ] Testes CLI passam
- [ ] Suite completa passa sem erros

### Integração
- [ ] Servidor dev inicia sem erros
- [ ] API lista todos os agentes
- [ ] Agentes YAML-only respondem via API
- [ ] Agentes Python factory respondem via API
- [ ] Servidor para graciosamente

---

## Próximos Passos

Após completar todos os testes com sucesso:

### 1. Commit das Mudanças

```bash
# Adicionar todos os arquivos
git add -A

# Criar commit
git commit -m "Wish yaml-only-agents: Complete implementation (Groups A-D)

- Group A: Enhanced discovery to support YAML-only agents
- Group B: Added --with-python flag to CLI
- Group C: Updated examples and comprehensive tests
- Group D: Documentation updates (README.md, CLAUDE.md)

Success criteria met:
✅ YAML-only agents load without agent.py
✅ Python factory agents still work (backward compatible)
✅ Mixed projects (YAML + Python) work correctly
✅ --with-python flag generates both files
✅ Default behavior is YAML-only
✅ Examples demonstrate both patterns
✅ All tests passing (discovery, CLI, regression)
✅ Documentation explains when to use each pattern

Co-Authored-By: Automagik Genie <genie@namastex.ai>"
```

### 2. Limpeza de Testes

```bash
# Remover agentes de teste criados
rm -rf ai/agents/teste-*
rm -rf ai/agents/my-bot*

# Verificar limpeza
git status
```

### 3. Merge (se aplicável)

```bash
# Voltar para dev/main
git checkout dev

# Merge do wish branch
git merge wish/yaml-only-agents

# Push
git push origin dev
```

---

## Referências

- **Wish Document:** `.genie/wishes/yaml-only-agents-wish.md`
- **Death Testament:** `.genie/wishes/yaml-only-agents-wish.md` (final do documento)
- **Examples README:** `hive/examples/agents/README.md`
- **Main README:** `README.md` (Quick Start section)
- **CLAUDE.md:** Agent Development Patterns section

---

**Guia criado em:** 2025-11-06
**Versão:** 1.0.0
**Autor:** Claude Code (Sonnet 4.5)
**Status:** ✅ Pronto para uso
