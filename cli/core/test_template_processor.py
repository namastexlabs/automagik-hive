"""Test script for Advanced Template Processing System.

This script validates the comprehensive template processing capabilities
including dynamic MCP configuration generation and workspace-specific
placeholder replacement.
"""

import json
import sys
import tempfile
from pathlib import Path

from template_processor import MCPConfigGenerator, TemplateProcessor


def test_template_processor():
    """Test the template processing system comprehensively."""
    # Initialize processors
    template_processor = TemplateProcessor()
    mcp_generator = MCPConfigGenerator(template_processor)

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test-workspace"
        workspace_path.mkdir()

        # Test 1: Workspace Context Creation
        context = template_processor.create_workspace_context(workspace_path)

        required_keys = [
            "workspace_name",
            "workspace_path",
            "host",
            "api_port",
            "db_host",
            "db_port",
            "database_url",
            "postgres_connection_string",
        ]

        for key in required_keys:
            if key not in context:
                return False

        # Test 2: PostgreSQL Configuration Processing
        postgres_config = {
            "type": "docker",
            "port": "5432",
            "image": "agnohq/pgvector:16",
        }

        docker_context = template_processor.create_workspace_context(
            workspace_path, postgres_config
        )
        if docker_context["db_port"] != 5432:
            return False

        # Test external PostgreSQL
        external_postgres = {
            "type": "external",
            "host": "remote-db.example.com",
            "port": "5433",
            "database": "custom_hive",
            "user": "custom_user",
        }

        external_context = template_processor.create_workspace_context(
            workspace_path, external_postgres
        )
        expected_db_url = "postgresql+psycopg://remote-db.example.com:5433/custom_hive"
        if external_context["database_url"] != expected_db_url:
            return False

        # Test 3: MCP Configuration Generation
        mcp_config = mcp_generator.generate_mcp_config(context)

        # Validate MCP structure
        if not mcp_generator.validate_mcp_config(mcp_config):
            return False

        # Check required servers
        required_servers = ["automagik-hive", "postgres"]
        for server in required_servers:
            if server not in mcp_config["servers"]:
                return False

        # Test 4: Template Content Processing
        template_content = """
        {
            "workspace": "{{workspace_name}}",
            "api_url": "{{api_endpoint}}",
            "database": "{{database_url}}",
            "port": {{api_port}},
            "environment": "${ENVIRONMENT}",
            "{{#if enable_git_mcp}}git_enabled{{/if}}": true
        }
        """

        # Add environment variable for testing
        import os

        os.environ["ENVIRONMENT"] = "test"

        processed_content = template_processor.process_template_content(
            template_content, context
        )

        # Verify processing worked
        if "{{" in processed_content or "${" in processed_content:
            return False

        # Verify JSON validity
        try:
            json.loads(processed_content)
        except json.JSONDecodeError:
            return False

        # Test 5: MCP Configuration File Writing
        mcp_file = workspace_path / ".mcp.json"

        if not mcp_generator.write_mcp_config(mcp_config, mcp_file):
            return False

        if not mcp_file.exists():
            return False

        # Verify file content
        try:
            written_config = json.loads(mcp_file.read_text())
            if written_config != mcp_config:
                return False
        except json.JSONDecodeError:
            return False

        # Test 6: Advanced Features

        # Test conditional processing
        context_with_conditions = context.copy()
        context_with_conditions.update(
            {
                "enable_git_mcp": True,
                "is_git_repo": True,
                "items": ["item1", "item2", "item3"],
            }
        )

        advanced_template = """{{#if enable_git_mcp}}Git MCP is enabled{{/if}}
{{#each items}}- Item {{index}}: {{item}} ({{#if first}}first{{/if}}{{#if last}}last{{/if}})
{{/each}}"""

        advanced_processed = template_processor.process_template_content(
            advanced_template, context_with_conditions
        )

        if "Git MCP is enabled" not in advanced_processed:
            return False

        if "Item 0: item1 (first)" not in advanced_processed:
            return False

        # Test 7: Validation System

        # Test invalid MCP config
        invalid_config = {"servers": {"invalid": {"command": ""}}}  # Empty command
        if mcp_generator.validate_mcp_config(invalid_config):
            return False

        # Test template validation
        unprocessed_content = "Hello {{missing_variable}} world"
        if template_processor.validate_processed_content(unprocessed_content):
            return False

    return True


def test_real_workspace_scenario():
    """Test with realistic workspace scenarios."""
    template_processor = TemplateProcessor()
    mcp_generator = MCPConfigGenerator(template_processor)

    # Scenario 1: Docker PostgreSQL workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "docker-workspace"
        workspace_path.mkdir()

        # Create .env file
        env_content = """
DATABASE_URL=postgresql+psycopg://localhost:5532/hive
HIVE_API_KEY=test-api-key
ENVIRONMENT=development
        """
        (workspace_path / ".env").write_text(env_content.strip())

        docker_postgres = {
            "type": "docker",
            "port": "5532",
            "image": "agnohq/pgvector:16",
        }

        context = template_processor.create_workspace_context(
            workspace_path, docker_postgres
        )
        mcp_config = mcp_generator.generate_mcp_config(context)

        # Verify Docker-specific settings
        postgres_connection = mcp_config["servers"]["postgres"]["args"][-1]
        if "localhost:5532" not in postgres_connection:
            return False

    # Scenario 2: External PostgreSQL workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "external-workspace"
        workspace_path.mkdir()

        external_postgres = {
            "type": "external",
            "host": "prod-db.company.com",
            "port": "5432",
            "database": "production_hive",
            "user": "prod_user",
        }

        context = template_processor.create_workspace_context(
            workspace_path, external_postgres
        )
        mcp_config = mcp_generator.generate_mcp_config(context)

        # Verify external-specific settings
        postgres_connection = mcp_config["servers"]["postgres"]["args"][-1]
        if "prod-db.company.com:5432" not in postgres_connection:
            return False

    return True


if __name__ == "__main__":
    success = True

    try:
        success = test_template_processor() and success
        success = test_real_workspace_scenario() and success

        if success:
            pass
        else:
            pass

    except Exception:
        import traceback

        traceback.print_exc()
        success = False

    sys.exit(0 if success else 1)
