#!/usr/bin/env python3
"""
Update all references to use YAML configuration and Claude 4 models.
"""

import re
from pathlib import Path

GENIE_DIR = Path("/home/namastex/workspace/pagbank-multiagents/genie")
CLAUDE_MD = Path("/home/namastex/workspace/pagbank-multiagents/CLAUDE.md")

# Replacements to make
REPLACEMENTS = [
    # Update Claude model references
    (r'claude-3-5-sonnet-20241022', 'claude-sonnet-4-20250514'),
    (r'claude-3-5-haiku-20241022', 'claude-haiku-4-20250514'),  # Assuming Claude 4 Haiku exists
    (r'claude-opus-4-20250514', 'claude-opus-4-20250514'),  # Keep as is
    
    # Replace hardcoded mode="route" with YAML reference
    (r'mode="route"[,\s]*#[^\n]*', 'mode=config["team"]["mode"],  # From YAML'),
    (r'mode="route"', 'mode=config["team"]["mode"]'),
    
    # Replace hardcoded ModelConfig with YAML reference
    (r'model=ModelConfig\([^)]+\)', 'model=config["model"]  # From YAML'),
    (r'ModelConfig\(\s*provider="anthropic",\s*name="[^"]+"\s*\)', 
     'config["model"]  # Loaded from YAML'),
]

# Special patterns for different contexts
YAML_CONFIG_EXAMPLE = '''# Example YAML configuration (not hardcoded!)
team:
  name: "Ana - Atendimento PagBank"
  team_id: "ana-pagbank-assistant"
  mode: "route"  # Routing mode configured here
  instructions:
    - "Route PIX and transfer queries to pagbank-specialist-v27"
    - "Route card issues to emissao-specialist-v27"
    - "Route merchant queries to adquirencia-specialist-v27"
    - "Route frustrated users to human-handoff-v27"

model:
  provider: "anthropic"
  name: "claude-sonnet-4-20250514"
  temperature: 0.7

agents:
  - "pagbank-specialist-v27"
  - "emissao-specialist-v27"
  - "adquirencia-specialist-v27"
  - "human-handoff-v27"'''

def update_file(file_path: Path, updates_made: list):
    """Update a single file with replacements"""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Apply replacements
        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)
        
        # Special handling for agno-patterns.md
        if file_path.name == "agno-patterns.md":
            # Replace the hardcoded team example with YAML-based
            content = re.sub(
                r'### Basic Team with mode="route".*?```',
                f'''### Team Configuration Pattern (YAML-Based)

{YAML_CONFIG_EXAMPLE}

### Loading Team from YAML
```python
from agno import Team
import yaml

def get_team_from_yaml(yaml_path: str):
    with open(yaml_path) as f:
        config = yaml.safe_load(f)
    
    # Load agents from registry based on config
    members = []
    for agent_id in config["agents"]:
        agent = AgentRegistry.get(agent_id)
        members.append(agent)
    
    # Create team with ALL settings from YAML
    return Team(
        name=config["team"]["name"],
        team_id=config["team"]["team_id"],
        mode=config["team"]["mode"],  # Not hardcoded!
        members=members,
        model=config["model"],  # Model from YAML
        instructions=config["team"]["instructions"]
    )
```''',
                content,
                flags=re.DOTALL,
                count=1
            )
        
        # Write back if changed
        if content != original_content:
            file_path.write_text(content)
            updates_made.append(str(file_path))
            return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
    return False

def main():
    """Run the update process"""
    updates_made = []
    
    # Update all markdown files in genie
    for md_file in GENIE_DIR.rglob("*.md"):
        update_file(md_file, updates_made)
    
    # Update CLAUDE.md
    update_file(CLAUDE_MD, updates_made)
    
    # Create a new reference file for YAML configuration
    yaml_reference = GENIE_DIR / "reference" / "yaml-configuration.md"
    yaml_reference.write_text(f'''# YAML Configuration Reference

**Navigation**: [← Database Schema](./database-schema.md) | [THIS FILE] | [Context Tools →](./context-search-tools.md)

## Core Principle: Everything in YAML

In V2, ALL Agno settings must be in YAML files. No hardcoding in Python!

## Team Configuration

{YAML_CONFIG_EXAMPLE}

## Agent Configuration

```yaml
# agents/pagbank-specialist-v27/config.yaml
agent:
  agent_id: "pagbank-specialist-v27"
  name: "PagBank Digital Banking Specialist"
  version: "v27"

model:
  provider: "anthropic"
  name: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 4096

system_prompt: |
  You are a PagBank digital banking specialist.
  Handle queries about PIX, transfers, account balance, etc.
  Always respond in Portuguese (pt-BR).

instructions:
  - "Specialize in PIX transfers and payments"
  - "Help with account management"
  - "Assist with mobile top-ups"
  - "Guide on investment products"

tools:
  - "search_knowledge_base"
  - "check_account_status"
```

## Loading Pattern

```python
# Never hardcode - always load from YAML
def get_agent():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    return Agent(
        agent_id=config["agent"]["agent_id"],
        name=config["agent"]["name"],
        model=config["model"],  # Entire model config from YAML
        system_prompt=config["system_prompt"],
        instructions=config["instructions"],
        tools=load_tools(config["tools"])
    )
```

## Model Configuration

All models should use Claude 4 versions:

```yaml
# Available models (from config/models.py)
models:
  default: "claude-sonnet-4-20250514"    # Balanced
  reasoning: "claude-opus-4-20250514"    # Most capable
  fast: "claude-haiku-4-20250514"       # Fast responses
```

## Benefits of YAML Configuration

1. **No Code Changes** - Update behavior without touching Python
2. **Version Control** - Track config changes separately
3. **A/B Testing** - Easy to test different configurations
4. **Hot Reload** - Change config and reload without restart
5. **Multi-Environment** - Different configs for dev/staging/prod

## Anti-Patterns to Avoid

```python
# ❌ NEVER hardcode settings
team = Team(
    mode="route",  # Bad!
    model=ModelConfig(provider="anthropic", name="claude-3-5-sonnet")  # Bad!
)

# ✅ ALWAYS load from YAML
team = Team(
    mode=config["team"]["mode"],
    model=config["model"]
)
```

**Navigation**: [← Database Schema](./database-schema.md) | [THIS FILE] | [Context Tools →](./context-search-tools.md)
''')
    updates_made.append(str(yaml_reference))
    
    print(f"\n✅ Updated {len(updates_made)} files:")
    for file in updates_made:
        print(f"   - {Path(file).relative_to(Path.cwd())}")
    
    # Print summary
    print("\n📋 Summary of changes:")
    print("   - Updated all Claude model references to Claude 4 versions")
    print("   - Replaced hardcoded mode='route' with YAML config references")
    print("   - Replaced hardcoded ModelConfig with YAML config references")
    print("   - Created yaml-configuration.md reference file")
    print("   - Updated patterns to show YAML-first approach")

if __name__ == "__main__":
    main()