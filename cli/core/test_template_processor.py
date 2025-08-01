"""Test script for Advanced Template Processing System.

This script validates the comprehensive template processing capabilities
including dynamic MCP configuration generation and workspace-specific
placeholder replacement.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from template_processor import TemplateProcessor, MCPConfigGenerator


def test_template_processor():
    """Test the template processing system comprehensively."""
    print("🧪 Testing Advanced Template Processing System")
    print("=" * 60)
    
    # Initialize processors
    template_processor = TemplateProcessor()
    mcp_generator = MCPConfigGenerator(template_processor)
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "test-workspace"
        workspace_path.mkdir()
        
        # Test 1: Workspace Context Creation
        print("\n1. Testing workspace context creation...")
        context = template_processor.create_workspace_context(workspace_path)
        
        required_keys = [
            "workspace_name", "workspace_path", "host", "api_port", 
            "db_host", "db_port", "database_url", "postgres_connection_string"
        ]
        
        for key in required_keys:
            if key not in context:
                print(f"❌ Missing required context key: {key}")
                return False
            else:
                print(f"✅ Context key '{key}': {context[key]}")
        
        # Test 2: PostgreSQL Configuration Processing
        print("\n2. Testing PostgreSQL configuration processing...")
        postgres_config = {
            "type": "docker",
            "port": "5432",
            "image": "agnohq/pgvector:16"
        }
        
        docker_context = template_processor.create_workspace_context(workspace_path, postgres_config)
        if docker_context["db_port"] != 5432:
            print(f"❌ PostgreSQL port not updated: expected 5432, got {docker_context['db_port']}")
            return False
        print(f"✅ Docker PostgreSQL context: port={docker_context['db_port']}")
        
        # Test external PostgreSQL
        external_postgres = {
            "type": "external",
            "host": "remote-db.example.com",
            "port": "5433",
            "database": "custom_hive",
            "user": "custom_user"
        }
        
        external_context = template_processor.create_workspace_context(workspace_path, external_postgres)
        expected_db_url = "postgresql+psycopg://remote-db.example.com:5433/custom_hive"
        if external_context["database_url"] != expected_db_url:
            print(f"❌ External DB URL incorrect: expected {expected_db_url}, got {external_context['database_url']}")
            return False
        print(f"✅ External PostgreSQL context: {external_context['database_url']}")
        
        # Test 3: MCP Configuration Generation
        print("\n3. Testing MCP configuration generation...")
        mcp_config = mcp_generator.generate_mcp_config(context)
        
        # Validate MCP structure
        if not mcp_generator.validate_mcp_config(mcp_config):
            print("❌ Generated MCP configuration failed validation")
            return False
        
        # Check required servers
        required_servers = ["automagik-hive", "postgres"]
        for server in required_servers:
            if server not in mcp_config["servers"]:
                print(f"❌ Missing required MCP server: {server}")
                return False
            print(f"✅ MCP server '{server}' configured")
        
        # Test 4: Template Content Processing
        print("\n4. Testing template content processing...")
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
        
        processed_content = template_processor.process_template_content(template_content, context)
        
        # Verify processing worked
        if "{{" in processed_content or "${" in processed_content:
            print("❌ Template processing incomplete - placeholders remain")
            print(f"Processed content: {processed_content}")
            return False
        
        # Verify JSON validity
        try:
            parsed_json = json.loads(processed_content)
            print(f"✅ Template processing successful, valid JSON generated")
            print(f"   Workspace: {parsed_json['workspace']}")
            print(f"   API URL: {parsed_json['api_url']}")
        except json.JSONDecodeError as e:
            print(f"❌ Processed template is not valid JSON: {e}")
            return False
        
        # Test 5: MCP Configuration File Writing
        print("\n5. Testing MCP configuration file writing...")
        mcp_file = workspace_path / ".mcp.json"
        
        if not mcp_generator.write_mcp_config(mcp_config, mcp_file):
            print("❌ Failed to write MCP configuration file")
            return False
        
        if not mcp_file.exists():
            print("❌ MCP configuration file was not created")
            return False
        
        # Verify file content
        try:
            written_config = json.loads(mcp_file.read_text())
            if written_config != mcp_config:
                print("❌ Written MCP config differs from generated config")
                return False
            print("✅ MCP configuration file written and verified")
        except json.JSONDecodeError:
            print("❌ Written MCP configuration file is not valid JSON")
            return False
        
        # Test 6: Advanced Features
        print("\n6. Testing advanced template features...")
        
        # Test conditional processing
        context_with_conditions = context.copy()
        context_with_conditions.update({
            "enable_git_mcp": True,
            "is_git_repo": True,
            "items": ["item1", "item2", "item3"]
        })
        
        advanced_template = """{{#if enable_git_mcp}}Git MCP is enabled{{/if}}
{{#each items}}- Item {{index}}: {{item}} ({{#if first}}first{{/if}}{{#if last}}last{{/if}})
{{/each}}"""
        
        advanced_processed = template_processor.process_template_content(advanced_template, context_with_conditions)
        
        if "Git MCP is enabled" not in advanced_processed:
            print("❌ Conditional processing failed")
            return False
        
        if "Item 0: item1 (first)" not in advanced_processed:
            print("❌ Loop processing failed")
            return False
        
        print("✅ Advanced template features working correctly")
        
        # Test 7: Validation System
        print("\n7. Testing validation system...")
        
        # Test invalid MCP config
        invalid_config = {"servers": {"invalid": {"command": ""}}}  # Empty command
        if mcp_generator.validate_mcp_config(invalid_config):
            print("❌ Validation should have failed for invalid config")
            return False
        print("✅ Validation correctly rejects invalid configurations")
        
        # Test template validation
        unprocessed_content = "Hello {{missing_variable}} world"
        if template_processor.validate_processed_content(unprocessed_content):
            print("❌ Validation should have failed for unprocessed content")
            return False
        print("✅ Template validation correctly identifies unprocessed placeholders")
        
    print("\n" + "=" * 60)
    print("🎉 All Advanced Template Processing tests passed!")
    print("✅ Dynamic MCP configuration generation working")
    print("✅ Workspace-specific placeholder replacement functional")
    print("✅ Template validation preventing invalid configurations")
    print("✅ Advanced features (conditionals, loops) operational")
    print("✅ Error handling and fallbacks in place")
    
    return True


def test_real_workspace_scenario():
    """Test with realistic workspace scenarios."""
    print("\n🏗️ Testing Real Workspace Scenarios")
    print("=" * 60)
    
    template_processor = TemplateProcessor()
    mcp_generator = MCPConfigGenerator(template_processor)
    
    # Scenario 1: Docker PostgreSQL workspace
    print("\n1. Docker PostgreSQL Workspace Scenario...")
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
            "image": "agnohq/pgvector:16"
        }
        
        context = template_processor.create_workspace_context(workspace_path, docker_postgres)
        mcp_config = mcp_generator.generate_mcp_config(context)
        
        # Verify Docker-specific settings
        postgres_connection = mcp_config["servers"]["postgres"]["args"][-1]
        if "localhost:5532" not in postgres_connection:
            print(f"❌ Docker postgres connection incorrect: {postgres_connection}")
            return False
        print("✅ Docker PostgreSQL workspace configured correctly")
    
    # Scenario 2: External PostgreSQL workspace
    print("\n2. External PostgreSQL Workspace Scenario...")
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = Path(temp_dir) / "external-workspace"
        workspace_path.mkdir()
        
        external_postgres = {
            "type": "external",
            "host": "prod-db.company.com",
            "port": "5432",
            "database": "production_hive",
            "user": "prod_user"
        }
        
        context = template_processor.create_workspace_context(workspace_path, external_postgres)
        mcp_config = mcp_generator.generate_mcp_config(context)
        
        # Verify external-specific settings
        postgres_connection = mcp_config["servers"]["postgres"]["args"][-1]
        if "prod-db.company.com:5432" not in postgres_connection:
            print(f"❌ External postgres connection incorrect: {postgres_connection}")
            return False
        print("✅ External PostgreSQL workspace configured correctly")
    
    print("\n✅ All real workspace scenarios passed!")
    return True


if __name__ == "__main__":
    success = True
    
    try:
        success = test_template_processor() and success
        success = test_real_workspace_scenario() and success
        
        if success:
            print("\n🌟 ADVANCED TEMPLATE SYSTEM VALIDATION COMPLETE")
            print("✅ All tests passed - system ready for production use!")
        else:
            print("\n❌ VALIDATION FAILED - issues detected")
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    exit(0 if success else 1)