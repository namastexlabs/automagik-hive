"""Advanced Template Processing System for Automagik Hive.

This module provides comprehensive template processing capabilities with 
dynamic configuration generation, workspace-specific placeholders, and 
validation systems for workspace initialization.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Union


class TemplateProcessor:
    """Advanced template processing with workspace-specific configuration."""
    
    def __init__(self):
        self.placeholder_patterns = {
            'simple': r'\{\{(\w+)\}\}',                          # {{variable}}
            'nested': r'\{\{(\w+)\.(\w+)\}\}',                   # {{object.property}}
            'env': r'\$\{(\w+)\}',                               # ${ENV_VAR}
            'conditional': r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}', # {{#if condition}}content{{/if}}
            'loop': r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}',  # {{#each items}}content{{/each}}
        }
    
    def process_template_file(self, template_path: Path, context: Dict[str, Any], output_path: Path) -> bool:
        """Process a template file with the given context and write to output path."""
        try:
            if not template_path.exists():
                print(f"❌ Template file not found: {template_path}")
                return False
            
            template_content = template_path.read_text()
            processed_content = self.process_template_content(template_content, context)
            
            if not self.validate_processed_content(processed_content):
                print(f"⚠️ Template processing validation failed for {template_path}")
                return False
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(processed_content)
            
            print(f"✅ Processed template: {template_path} → {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Template processing error for {template_path}: {e}")
            return False
    
    def process_template_content(self, content: str, context: Dict[str, Any]) -> str:
        """Process template content with advanced placeholder replacement."""
        try:
            processed_content = content
            
            # Process in order of complexity (simple → complex)
            processed_content = self._process_simple_placeholders(processed_content, context)
            processed_content = self._process_nested_placeholders(processed_content, context)
            processed_content = self._process_environment_variables(processed_content)
            processed_content = self._process_conditional_blocks(processed_content, context)
            processed_content = self._process_loop_blocks(processed_content, context)
            
            return processed_content
            
        except Exception as e:
            print(f"❌ Template content processing error: {e}")
            return content  # Return original on error
    
    def _process_simple_placeholders(self, content: str, context: Dict[str, Any]) -> str:
        """Process simple {{variable}} placeholders."""
        def replace_simple(match):
            key = match.group(1)
            value = context.get(key, f"MISSING_{key}")
            if str(value).startswith("MISSING_"):
                print(f"⚠️ Warning: Missing template variable: {key}")
            return str(value)
        
        return re.sub(self.placeholder_patterns['simple'], replace_simple, content)
    
    def _process_nested_placeholders(self, content: str, context: Dict[str, Any]) -> str:
        """Process nested {{object.property}} placeholders."""
        def replace_nested(match):
            obj_key, prop_key = match.group(1), match.group(2)
            obj = context.get(obj_key, {})
            
            if isinstance(obj, dict):
                value = obj.get(prop_key, f"MISSING_{obj_key}.{prop_key}")
            elif hasattr(obj, prop_key):
                value = getattr(obj, prop_key)
            else:
                value = f"MISSING_{obj_key}.{prop_key}"
            
            if str(value).startswith("MISSING_"):
                print(f"⚠️ Warning: Missing nested template variable: {obj_key}.{prop_key}")
            
            return str(value)
        
        return re.sub(self.placeholder_patterns['nested'], replace_nested, content)
    
    def _process_environment_variables(self, content: str) -> str:
        """Process ${ENV_VAR} environment variable placeholders."""
        def replace_env(match):
            env_var = match.group(1)
            value = os.getenv(env_var, f"MISSING_ENV_{env_var}")
            if value == f"MISSING_ENV_{env_var}":
                print(f"⚠️ Warning: Missing environment variable: {env_var}")
            return str(value)
        
        return re.sub(self.placeholder_patterns['env'], replace_env, content)
    
    def _process_conditional_blocks(self, content: str, context: Dict[str, Any]) -> str:
        """Process {{#if condition}}content{{/if}} conditional blocks."""
        def replace_conditional(match):
            condition = match.group(1)
            block_content = match.group(2)
            
            condition_value = context.get(condition, False)
            
            # Handle various truthy/falsy values
            if isinstance(condition_value, str):
                condition_value = condition_value.lower() not in ['false', '0', '', 'no']
            elif isinstance(condition_value, (int, float)):
                condition_value = condition_value != 0
            elif condition_value is None:
                condition_value = False
            
            return block_content if condition_value else ""
        
        return re.sub(self.placeholder_patterns['conditional'], replace_conditional, content, flags=re.DOTALL)
    
    def _process_loop_blocks(self, content: str, context: Dict[str, Any]) -> str:
        """Process {{#each items}}content{{/each}} loop blocks."""
        def replace_loop(match):
            items_key = match.group(1)
            block_content = match.group(2)
            
            items = context.get(items_key, [])
            if not isinstance(items, (list, tuple)):
                print(f"⚠️ Warning: Loop variable '{items_key}' is not a list/tuple")
                return ""
            
            result_parts = []
            for i, item in enumerate(items):
                # Create item context
                item_context = context.copy()
                if isinstance(item, dict):
                    item_context.update(item)
                else:
                    item_context['item'] = item
                
                item_context['index'] = i
                item_context['first'] = (i == 0)
                item_context['last'] = (i == len(items) - 1)
                
                # Process the block content with item context
                processed_block = self.process_template_content(block_content, item_context)
                result_parts.append(processed_block)
            
            return "".join(result_parts)
        
        return re.sub(self.placeholder_patterns['loop'], replace_loop, content, flags=re.DOTALL)
    
    def validate_processed_content(self, content: str) -> bool:
        """Validate that template processing completed successfully."""
        # Check for unprocessed placeholders
        unprocessed_patterns = [
            r'\{\{\w+\}\}',           # {{variable}}
            r'\{\{\w+\.\w+\}\}',      # {{object.property}}
            r'\$\{\w+\}',             # ${ENV_VAR}
            r'MISSING_\w+',           # Missing variables
            r'\{\{#if\s+\w+\}\}',     # Unprocessed conditionals
            r'\{\{#each\s+\w+\}\}',   # Unprocessed loops
        ]
        
        for pattern in unprocessed_patterns:
            matches = re.findall(pattern, content)
            if matches:
                print(f"⚠️ Warning: Unprocessed template placeholders found: {matches}")
                return False
        
        return True
    
    def create_workspace_context(self, workspace_path: Path, postgres_config: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create comprehensive workspace context for template processing."""
        context = {
            # Workspace information
            "workspace_name": workspace_path.name,
            "workspace_path": str(workspace_path.absolute()),
            "workspace_parent": str(workspace_path.parent.absolute()),
            
            # Server configuration
            "host": "127.0.0.1",
            "api_port": 8886,
            "mcp_port": 8887,
            
            # Database configuration
            "db_host": "localhost",
            "db_port": 5532,
            "db_name": "hive",
            "db_user": "hive_user",
            
            # Feature flags
            "enable_additional_mcps": False,
            "enable_filesystem_mcp": True,
            "enable_git_mcp": True,
            
            # Environment context
            "is_git_repo": (workspace_path / ".git").exists(),
            "has_docker": self._check_docker_available(),
            "has_uv": self._check_uv_available(),
        }
        
        # Override with postgres configuration if provided
        if postgres_config:
            context.update(self._process_postgres_config(postgres_config))
        
        # Generate dynamic URLs
        context.update(self._generate_dynamic_urls(context))
        
        # Load environment variables if .env exists
        env_file = workspace_path / ".env"
        if env_file.exists():
            context.update(self._parse_env_file(env_file))
        
        return context
    
    def _process_postgres_config(self, postgres_config: Dict[str, str]) -> Dict[str, Any]:
        """Process postgres configuration for template context."""
        config_updates = {}
        
        if postgres_config.get("type") == "docker":
            port = postgres_config.get("port", 5532)
            config_updates.update({
                "db_port": int(port),
                "db_type": "docker",
                "postgres_image": postgres_config.get("image", "agnohq/pgvector:16")
            })
            
        elif postgres_config.get("type") == "external":
            host = postgres_config.get("host", "localhost")
            port = postgres_config.get("port", "5432")
            database = postgres_config.get("database", "hive")
            user = postgres_config.get("user", "hive_user")
            
            config_updates.update({
                "db_host": host,
                "db_port": int(port),
                "db_name": database,
                "db_user": user,
                "db_type": "external"
            })
        
        return config_updates
    
    def _generate_dynamic_urls(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate dynamic URLs based on workspace configuration."""
        db_host = context["db_host"]
        db_port = context["db_port"]
        db_name = context["db_name"]
        
        return {
            "database_url": f"postgresql+psycopg://{db_host}:{db_port}/{db_name}",
            "postgres_connection_string": f"postgresql://{db_host}:{db_port}/{db_name}",
            "api_endpoint": f"http://{context['host']}:{context['api_port']}",
            "mcp_endpoint": f"http://{context['host']}:{context['mcp_port']}"
        }
    
    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse .env file for template variables."""
        env_vars = {}
        try:
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ Warning: Could not parse .env file: {e}")
        
        return env_vars
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            import subprocess
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, check=False)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def _check_uv_available(self) -> bool:
        """Check if UV is available."""
        try:
            import subprocess
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, check=False)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False


class MCPConfigGenerator:
    """Specialized MCP configuration generator with validation."""
    
    def __init__(self, template_processor: TemplateProcessor):
        self.template_processor = template_processor
    
    def generate_mcp_config(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate dynamic MCP configuration using template context."""
        config = {
            "servers": {
                "automagik-hive": {
                    "command": "uv",
                    "args": [
                        "run", "uvicorn", "api.serve:app", 
                        "--host", context["host"], 
                        "--port", str(context["api_port"])
                    ],
                    "env": {
                        "DATABASE_URL": context["database_url"],
                        "HIVE_DATABASE_URL": context["database_url"]
                    }
                },
                "postgres": {
                    "command": "uv",
                    "args": [
                        "run", "mcp-server-postgres", 
                        "--connection-string", context["postgres_connection_string"]
                    ]
                }
            }
        }
        
        # Add optional servers based on workspace configuration
        if context.get("enable_additional_mcps", False):
            config["servers"].update(self._generate_additional_mcp_servers(context))
        
        return config
    
    def _generate_additional_mcp_servers(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate additional MCP servers based on workspace needs."""
        additional_servers = {}
        
        # Add filesystem MCP if enabled
        if context.get("enable_filesystem_mcp", True):
            additional_servers["filesystem"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", context["workspace_path"]]
            }
        
        # Add git MCP if workspace is a git repository and enabled
        if context.get("is_git_repo", False) and context.get("enable_git_mcp", True):
            additional_servers["git"] = {
                "command": "npx", 
                "args": ["-y", "@modelcontextprotocol/server-git", "--repository", context["workspace_path"]]
            }
        
        return additional_servers
    
    def validate_mcp_config(self, config: Dict[str, Any]) -> bool:
        """Validate MCP configuration structure and required fields."""
        try:
            # Check top-level structure
            if "servers" not in config:
                print("❌ MCP config validation failed: missing 'servers' key")
                return False
            
            servers = config["servers"]
            if not isinstance(servers, dict):
                print("❌ MCP config validation failed: 'servers' must be a dictionary")
                return False
            
            # Validate each server configuration
            for server_name, server_config in servers.items():
                if not self._validate_server_config(server_name, server_config):
                    return False
            
            print("✅ MCP configuration validation passed")
            return True
            
        except Exception as e:
            print(f"❌ MCP config validation error: {e}")
            return False
    
    def _validate_server_config(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Validate individual server configuration."""
        required_fields = ["command", "args"]
        
        for field in required_fields:
            if field not in config:
                print(f"❌ Server '{server_name}' missing required field: {field}")
                return False
        
        # Validate command exists (basic check)
        command = config["command"]
        if not isinstance(command, str) or not command.strip():
            print(f"❌ Server '{server_name}' has invalid command")
            return False
        
        # Validate args is a list
        args = config["args"]
        if not isinstance(args, list):
            print(f"❌ Server '{server_name}' args must be a list")
            return False
        
        return True
    
    def write_mcp_config(self, config: Dict[str, Any], output_path: Path) -> bool:
        """Write MCP configuration to file with validation."""
        try:
            if not self.validate_mcp_config(config):
                print("❌ MCP configuration validation failed, cannot write config")
                return False
            
            output_path.write_text(json.dumps(config, indent=2))
            print(f"✅ Created MCP configuration: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to write MCP configuration: {e}")
            return False