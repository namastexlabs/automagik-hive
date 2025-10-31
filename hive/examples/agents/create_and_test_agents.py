#!/usr/bin/env python3
"""Create and test 3 working example agents using REAL AI.

This script:
1. Uses meta-agent to generate agent configs
2. Creates proper directory structure
3. Writes agent.py with correct Agno patterns
4. Tests each agent with REAL LLM calls
5. Provides evidence of successful execution
"""

import os
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv

load_dotenv(project_root / ".env")

# Verify API keys
print("=" * 70)
print("🔑 VERIFYING API KEYS")
print("=" * 70)
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if openai_key:
    print(f"✅ OPENAI_API_KEY: {openai_key[:20]}...")
else:
    print("❌ OPENAI_API_KEY: NOT FOUND")
    sys.exit(1)

if anthropic_key:
    print(f"✅ ANTHROPIC_API_KEY: {anthropic_key[:20]}...")
else:
    print("❌ ANTHROPIC_API_KEY: NOT FOUND")
    sys.exit(1)

print()

# Import after environment is loaded
import yaml

from hive.generators.meta_agent import quick_generate

# Agent specifications
AGENTS = [
    {
        "name": "support-bot",
        "description": "Customer support agent with CSV knowledge base and web search capabilities. "
        "Handles FAQs, searches web for complex issues, and escalates when needed.",
        "test_query": "How do I reset my password?",
    },
    {
        "name": "code-reviewer",
        "description": "Code review agent that analyzes code quality, suggests improvements, "
        "checks for bugs, and follows best practices. Focus on Python code.",
        "test_query": "Review this function: def calc(x,y): return x+y",
    },
    {
        "name": "researcher",
        "description": "Web research agent that searches for information, synthesizes findings, "
        "and provides comprehensive summaries with sources.",
        "test_query": "What are the latest developments in AI agents?",
    },
]


def create_agent_directory(agent_name: str) -> Path:
    """Create agent directory structure."""
    agent_dir = project_root / "hive" / "examples" / "agents" / agent_name
    agent_dir.mkdir(parents=True, exist_ok=True)

    # Create data directory for knowledge files
    data_dir = agent_dir / "data"
    data_dir.mkdir(exist_ok=True)

    return agent_dir


def generate_config_with_ai(agent_name: str, description: str) -> dict:
    """Use meta-agent to generate configuration."""
    print(f"\n🤖 Generating config for {agent_name} using REAL AI...")

    # Add constraints to guide the meta-agent
    analysis = quick_generate(
        description + "\n\nIMPORTANT: Use only available models (gpt-4o-mini, gpt-4o, claude-sonnet-4-20250514) "
        "and basic tools (PythonTools, ShellTools, FileTools).",
        model="gpt-4o-mini",
    )

    print(f"  ✅ Model recommendation: {analysis.model_recommendation}")
    print(f"  ✅ Tools: {', '.join(analysis.tools_recommended)}")
    print(f"  ✅ Complexity: {analysis.complexity_score}/10")

    # Validate and fix model name
    valid_models = {
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4o": "gpt-4o",
        "gpt-4.1-mini": "gpt-4.1-mini",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-opus-4": "gpt-4o",  # Fallback - opus-4 doesn't exist
        "claude-haiku-4": "gpt-4o-mini",  # Fallback
    }

    model_id = analysis.model_recommendation
    for pattern, replacement in valid_models.items():
        if pattern in model_id:
            model_id = replacement
            break

    if model_id not in valid_models.values():
        print(f"  ⚠️  Unknown model {model_id}, using gpt-4o-mini")
        model_id = "gpt-4o-mini"

    # Filter tools to only those we support
    supported_tools = {"PythonTools", "ShellTools", "FileTools"}
    filtered_tools = [t for t in analysis.tools_recommended if t in supported_tools]

    if not filtered_tools:
        print("  ⚠️  No supported tools found, using no tools")

    # Create config structure
    config = {
        "agent": {
            "name": agent_name,
            "id": agent_name,
            "description": description,
        },
        "model": {
            "id": model_id,
            "temperature": 0.7,
        },
        "instructions": analysis.instructions,
        "tools": filtered_tools,
    }

    print(f"  ℹ️  Using model: {model_id}")
    print(f"  ℹ️  Using tools: {', '.join(filtered_tools) if filtered_tools else 'none'}")

    return config


def write_agent_py(agent_dir: Path, agent_name: str, config: dict):
    """Write agent.py with proper Agno factory pattern."""

    # Map tool names to Agno imports - only use tools that exist
    tool_imports = {
        "PythonTools": "from agno.tools.python import PythonTools",
        "ShellTools": "from agno.tools.shell import ShellTools",
        "FileTools": "from agno.tools.file import FileTools",
        # Skip tools that require extra dependencies we don't have
        # "DuckDuckGoTools": requires ddgs
        # "TavilyTools": requires tavily
        # "CSVTools": doesn't exist in agno
        # "WebpageTools": may require extra deps
    }

    # Build imports
    imports = []
    tool_instances = []
    for tool in config.get("tools", []):
        if tool in tool_imports:
            imports.append(tool_imports[tool])
            tool_instances.append(f"{tool}()")

    imports_str = "\n".join(imports) if imports else ""
    tools_str = "[" + ", ".join(tool_instances) + "]" if tool_instances else "[]"

    # Detect model provider
    model_id = config["model"]["id"]
    if model_id.startswith("gpt") or model_id.startswith("o1"):
        model_import = "from agno.models.openai import OpenAIChat"
        model_class = "OpenAIChat"
    elif model_id.startswith("claude"):
        model_import = "from agno.models.anthropic import Claude"
        model_class = "Claude"
    else:
        model_import = "from agno.models.openai import OpenAIChat"
        model_class = "OpenAIChat"

    agent_py = f'''"""
{agent_name.replace("-", " ").title()} Agent

Generated using Automagik Hive meta-agent generator.
"""

from pathlib import Path
from agno.agent import Agent
{model_import}
{imports_str}
import yaml


def get_{agent_name.replace("-", "_")}_agent(**kwargs) -> Agent:
    """Create {agent_name} agent with YAML configuration.

    Args:
        **kwargs: Runtime overrides (session_id, user_id, debug_mode, etc.)

    Returns:
        Agent: Configured agent instance
    """
    # Load YAML configuration
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Extract config sections
    agent_config = config.get("agent", {{}})
    model_config = config.get("model", {{}})

    # Create Model instance
    model = {model_class}(
        id=model_config.get("id"),
        temperature=model_config.get("temperature", 0.7)
    )

    # Prepare tools
    tools = {tools_str}

    # Build agent parameters
    agent_params = {{
        "name": agent_config.get("name"),
        "model": model,
        "instructions": config.get("instructions"),
        "description": agent_config.get("description"),
        "tools": tools if tools else None,
        **kwargs
    }}

    # Create agent
    agent = Agent(**agent_params)

    # Set agent id as instance attribute (NOT in constructor)
    if agent_config.get("id"):
        agent.id = agent_config.get("id")

    return agent


# Quick test function
if __name__ == "__main__":
    print("Testing {agent_name} agent...")

    agent = get_{agent_name.replace("-", "_")}_agent()
    print(f"✅ Agent created: {{agent.name}}")
    print(f"✅ Model: {{agent.model.id}}")
    print(f"✅ Agent ID: {{agent.id}}")

    # Test with a simple query
    response = agent.run("Hello, what can you help me with?")
    print(f"\\n📝 Response:\\n{{response.content}}")
'''

    # Write the file
    agent_py_path = agent_dir / "agent.py"
    with open(agent_py_path, "w", encoding="utf-8") as f:
        f.write(agent_py)

    print(f"  ✅ Created {agent_py_path}")


def write_config_yaml(agent_dir: Path, config: dict):
    """Write config.yaml file."""
    config_path = agent_dir / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"  ✅ Created {config_path}")


def write_readme(agent_dir: Path, agent_name: str, description: str, config: dict):
    """Write README.md."""
    readme = f"""# {agent_name.replace("-", " ").title()}

{description}

## Configuration

- **Model**: {config["model"]["id"]}
- **Tools**: {", ".join(config.get("tools", []))}
- **Temperature**: {config["model"]["temperature"]}

## Usage

```python
from agent import get_{agent_name.replace("-", "_")}_agent

# Create agent
agent = get_{agent_name.replace("-", "_")}_agent()

# Run query
response = agent.run("Your query here")
print(response.content)
```

## Testing

```bash
python agent.py
```

## Generated

This agent was generated using Automagik Hive's meta-agent generator with REAL AI.
"""

    readme_path = agent_dir / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"  ✅ Created {readme_path}")


def test_agent(agent_dir: Path, agent_name: str, test_query: str):
    """Test the agent with a real query."""
    print(f"\n🧪 Testing {agent_name} with REAL LLM call...")

    # Import the agent module dynamically
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"{agent_name}_module", agent_dir / "agent.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Get the factory function
    factory_name = f"get_{agent_name.replace('-', '_')}_agent"
    get_agent = getattr(module, factory_name)

    # Create agent
    agent = get_agent()
    print(f"  ✅ Agent created: {agent.name}")
    print(f"  ✅ Model: {agent.model.id}")
    print(f"  ✅ Agent ID: {agent.id}")

    # Test with query
    print(f"\n  📤 Query: {test_query}")
    response = agent.run(test_query)
    print(f"\n  📥 Response:\n{'-' * 70}")
    print(f"  {response.content[:500]}...")
    print(f"{'-' * 70}")

    return True


def main():
    """Main execution."""
    print("\n" + "=" * 70)
    print("🚀 CREATING 3 WORKING EXAMPLE AGENTS WITH REAL AI")
    print("=" * 70)

    results = []

    for agent_spec in AGENTS:
        agent_name = agent_spec["name"]
        description = agent_spec["description"]
        test_query = agent_spec["test_query"]

        print(f"\n{'=' * 70}")
        print(f"📦 CREATING: {agent_name}")
        print(f"{'=' * 70}")

        try:
            # 1. Create directory
            agent_dir = create_agent_directory(agent_name)
            print(f"✅ Created directory: {agent_dir}")

            # 2. Generate config with AI
            config = generate_config_with_ai(agent_name, description)

            # 3. Write files
            write_config_yaml(agent_dir, config)
            write_agent_py(agent_dir, agent_name, config)
            write_readme(agent_dir, agent_name, description, config)

            # 4. Test the agent
            success = test_agent(agent_dir, agent_name, test_query)

            results.append({"name": agent_name, "success": success, "directory": agent_dir})

            print(f"\n✅ {agent_name} COMPLETE!")

        except Exception as e:
            print(f"\n❌ Error creating {agent_name}: {e}")
            import traceback

            traceback.print_exc()
            results.append({"name": agent_name, "success": False, "error": str(e)})

    # Print summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)

    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['name']}")
        if result["success"]:
            print(f"   Directory: {result['directory']}")

    successful = sum(1 for r in results if r["success"])
    print(f"\n✅ {successful}/{len(AGENTS)} agents created and tested successfully!")

    if successful == len(AGENTS):
        print("\n🎉 ALL AGENTS WORKING!")
        return 0
    else:
        print("\n⚠️  Some agents failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
