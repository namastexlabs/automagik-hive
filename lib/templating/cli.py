"""
CLI Tool for Template System Management

Provides command-line interface for testing, validating, and managing
the YAML templating system.
"""

import json
from pathlib import Path

import click
import yaml

from .context import ContextProvider
from .processor import get_template_processor


@click.group()
def template_cli():
    """Template system management CLI."""


@template_cli.command()
@click.argument("yaml_path", type=click.Path(exists=True))
@click.option("--user-id", help="User ID for context")
@click.option("--user-name", help="User name for context")
@click.option("--session-id", help="Session ID for context")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--context-file", type=click.Path(exists=True), help="JSON file with context data")
@click.option("--output", type=click.Path(), help="Output file for processed YAML")
def render(yaml_path, user_id, user_name, session_id, debug, context_file, output):
    """Render YAML template with provided context."""

    try:
        # Build context
        context_kwargs = {}

        if user_id:
            context_kwargs["user_id"] = user_id
        if user_name:
            context_kwargs["user_name"] = user_name
        if session_id:
            context_kwargs["session_id"] = session_id
        if debug:
            context_kwargs["debug_mode"] = True

        # Load additional context from file if provided
        if context_file:
            with open(context_file) as f:
                file_context = json.load(f)
                context_kwargs.update(file_context)

        # Process template
        processor = get_template_processor()
        result = processor.process_yaml_file(yaml_path, **context_kwargs)

        # Output result
        output_content = yaml.dump(result, default_flow_style=False, indent=2)

        if output:
            with open(output, "w") as f:
                f.write(output_content)
            click.echo(f"✅ Rendered template saved to {output}")
        else:
            click.echo("📄 Rendered Template:")
            click.echo("=" * 50)
            click.echo(output_content)

    except Exception as e:
        click.echo(f"❌ Error rendering template: {e}", err=True)
        if debug:
            import traceback
            click.echo(traceback.format_exc(), err=True)


@template_cli.command()
@click.argument("yaml_path", type=click.Path(exists=True))
@click.option("--context-file", type=click.Path(exists=True), help="JSON file with sample context")
def validate(yaml_path, context_file):
    """Validate YAML template syntax and structure."""

    try:
        processor = get_template_processor()

        # Load sample context if provided
        context_sample = None
        if context_file:
            with open(context_file) as f:
                context_sample = json.load(f)

        # Validate template
        results = processor.validate_template(yaml_path, context_sample)

        if results["valid"]:
            click.echo("✅ Template validation passed")
        else:
            click.echo("❌ Template validation failed")

        # Show results
        if results["required_variables"]:
            click.echo(f"📋 Required variables: {', '.join(results['required_variables'])}")

        if results["errors"]:
            click.echo("🚨 Errors:")
            for error in results["errors"]:
                click.echo(f"  - {error}")

        if results["warnings"]:
            click.echo("⚠️  Warnings:")
            for warning in results["warnings"]:
                click.echo(f"  - {warning}")

        if results["security_issues"]:
            click.echo("🔒 Security Issues:")
            for issue in results["security_issues"]:
                click.echo(f"  - {issue}")

    except Exception as e:
        click.echo(f"❌ Error validating template: {e}", err=True)


@template_cli.command()
@click.argument("yaml_path", type=click.Path(exists=True))
def variables(yaml_path):
    """Extract template variables from YAML file."""

    try:
        processor = get_template_processor()
        variables = processor.get_template_variables(yaml_path)

        if variables:
            click.echo("📋 Template Variables:")
            for var in sorted(variables):
                click.echo(f"  - {var}")
        else:
            click.echo("ℹ️  No template variables found")

    except Exception as e:
        click.echo(f"❌ Error extracting variables: {e}", err=True)


@template_cli.command()
@click.option("--component-id", help="Specific component to test")
@click.option("--component-type", type=click.Choice(["agent", "team", "workflow"]), default="agent")
@click.option("--user-id", default="test-user")
@click.option("--user-name", default="Test User")
@click.option("--session-id", default="test-session")
def test_integration(component_id, component_type, user_id, user_name, session_id):
    """Test template integration with VersionFactory."""

    try:
        from lib.utils.version_factory import get_version_factory

        from .integration import integrate_templating_with_version_factory

        # Get factory and integrate templating
        factory = get_version_factory()
        integrated_factory = integrate_templating_with_version_factory(factory)

        if not component_id:
            # Discover available components
            type_dirs = {
                "agent": "ai/agents",
                "team": "ai/teams",
                "workflow": "ai/workflows"
            }

            components_dir = Path(type_dirs[component_type])
            if components_dir.exists():
                components = [d.name for d in components_dir.iterdir() if d.is_dir()]
                if components:
                    component_id = components[0]
                    click.echo(f"ℹ️  Using component: {component_id}")
                else:
                    click.echo("❌ No components found")
                    return
            else:
                click.echo(f"❌ Components directory not found: {components_dir}")
                return

        # Test component creation
        click.echo(f"🧪 Testing {component_type} creation: {component_id}")

        component = integrated_factory.create_versioned_component(
            component_id=component_id,
            component_type=component_type,
            user_id=user_id,
            user_name=user_name,
            session_id=session_id,
            debug_mode=True
        )

        click.echo(f"✅ Successfully created {component_type}: {component}")
        click.echo(f"   Type: {type(component)}")

        # Show component details if available
        if hasattr(component, "name"):
            click.echo(f"   Name: {component.name}")
        if hasattr(component, "description"):
            click.echo(f"   Description: {component.description}")

    except Exception as e:
        click.echo(f"❌ Integration test failed: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)






@template_cli.command()
@click.option("--user-id", default="sample-user")
@click.option("--user-name", default="Sample User")
@click.option("--email", default="user@example.com")
@click.option("--output", type=click.Path(), help="Output file for context JSON")
def generate_context(user_id, user_name, email, output):
    """Generate sample context data for testing."""

    try:
        provider = ContextProvider()

        context = provider.build_context(
            user_id=user_id,
            user_name=user_name,
            email=email,
            session_id="sample-session",
            tenant_id="sample-tenant",
            agent_id="sample-agent",
            debug_mode=True,
            permissions=["user", "read"],
            business_units=["sales", "support"],
            user_preferences={"creativity_level": 0.3},
            custom_greeting="Hello from template system!"
        )

        context_dict = context.to_dict()

        # Output context
        output_content = json.dumps(context_dict, indent=2, default=str)

        if output:
            with open(output, "w") as f:
                f.write(output_content)
            click.echo(f"✅ Sample context saved to {output}")
        else:
            click.echo("📋 Sample Context Data:")
            click.echo("=" * 50)
            click.echo(output_content)

    except Exception as e:
        click.echo(f"❌ Error generating context: {e}", err=True)


@template_cli.command()
def system_info():
    """Show template system information."""

    try:
        processor = get_template_processor()
        click.echo("🎯 Template System Information:")
        click.echo("  Template processing enabled")

        # Environment info
        import os
        click.echo("\n🌍 Environment:")
        click.echo(f"  Templating Enabled: {os.getenv('ENABLE_YAML_TEMPLATING', 'true')}")
        click.echo(f"  Environment: {os.getenv('ENVIRONMENT', 'development')}")

        # Component directories
        click.echo("\n📁 Component Directories:")
        for comp_type, path in [("agents", "ai/agents"), ("teams", "ai/teams"), ("workflows", "ai/workflows")]:
            comp_path = Path(path)
            if comp_path.exists():
                count = len([d for d in comp_path.iterdir() if d.is_dir()])
                click.echo(f"  {comp_type}: {count} components in {path}")
            else:
                click.echo(f"  {comp_type}: directory not found ({path})")

    except Exception as e:
        click.echo(f"❌ Error getting system info: {e}", err=True)


if __name__ == "__main__":
    template_cli()
