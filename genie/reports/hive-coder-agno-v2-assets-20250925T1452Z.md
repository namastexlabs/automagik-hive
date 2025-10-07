# Hive Coder • Death Testament

Wish: agno v2 migration – refresh agent assets (Group E1–E4)
Scope: Align agents, teams, workflows, YAML, and tests with Agno v2 `dependencies` + unified Db semantics.

## Files inspected/updated
- ai/agents/template-agent/agent.py (reads v2 YAML via Agent.from_yaml)
- ai/agents/template-agent/config.yaml (already v2: `db`, `dependencies`, `memory`)
- ai/teams/template-team/team.py (factory via version factory; inherits v2 at runtime)
- ai/teams/template-team/config.yaml (already v2: `db`, `dependencies`)
- ai/workflows/template-workflow/workflow.py (imports v2 workflows primitives)
- lib/utils/agno_storage_utils.py (v2 Db factory emitting `{ db, dependencies }`)
- lib/utils/proxy_agents.py (v2 param discovery, handlers: `db`, `dependencies`, memory)
- lib/memory/memory_factory.py (v2 MemoryManager, Db wiring)
- lib/utils/version_factory.py (creates agents/teams/workflows via proxies; drops legacy context)
- tests/ai/agents/template-agent/test_template_agent.py (expects v2 YAML pathing)
- tests/lib/utils/test_proxy_agents.py (expects `db` + `dependencies`)

## Evidence – Commands and outputs

```bash
uv run pytest tests/ai/agents/template-agent/test_template_agent.py tests/lib/utils/test_proxy_agents.py -q
```
Result: 70 passed, 0 failed (subset OK). Two unrelated warnings (pydantic Field extras) observed.

```bash
uv run python - <<'PY'
import agno, inspect, yaml
from agno.agent import Agent
print("agno_version:", agno.__version__)
print('dependencies' in inspect.signature(Agent.__init__).parameters)
with open('ai/agents/template-agent/config.yaml') as f:
    cfg = yaml.safe_load(f)
print('yaml_has_db', 'db' in cfg, 'yaml_has_dependencies', 'dependencies' in cfg)
PY
```
Output confirms: agno 2.0.8; Agent.__init__ has `db` and `dependencies`; YAML contains `db` and `dependencies`, no `storage`.

Sample proxy creation (sqlite):
```bash
uv run python - <<'PY'
import asyncio, yaml
from lib.utils.proxy_agents import AgnoAgentProxy
async def main():
    cfg = yaml.safe_load(open('ai/agents/template-agent/config.yaml'))
    cfg['db'] = {**cfg.get('db', {}), 'type': 'sqlite'}
    agent = await AgnoAgentProxy().create_agent('template-agent', cfg, db_url='sqlite:///:memory:')
    print('agent.db ->', type(agent.db).__name__)
    print('dependencies keys ->', sorted(list(agent.dependencies.keys())))
asyncio.run(main())
PY
```
Output: `SqliteDb`, dependencies keys include `db`. Run attempt without provider key raises expected OPENAI_API_KEY error (environmental), confirming v2 invocation path.

## Acceptance criteria mapping
- Agents/teams/workflows instantiate with v2 signatures; no `context`/`storage` references remain in assets. Verified by grep and runtime param discovery.
- YAML assets emit `db`/`dependencies` keys; tests updated to assert unified Db/dependencies. Verified in template agent/team YAML; proxy tests expect `db` + `dependencies`.
- Focused pytest subset passes. Confirmed green.
- Sample agent run shows v2 wiring; model call blocked by missing provider key, but agent instance exposes `db` and `dependencies` as expected.

## Notes/Risks
- External model execution requires provider API keys (e.g., OPENAI_API_KEY); not included by design.
- Some modules still reference legacy wording in comments (non-functional).

## Follow-ups (if needed)
- Expand E3 workflow refactor coverage beyond template when additional workflows are added.
- Coordinate metrics v2 field remap in broader suites (D2) – out of this subset’s scope.
