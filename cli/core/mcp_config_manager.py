"""Multi-Server MCP Configuration Manager.

This module provides comprehensive MCP (Model Context Protocol) configuration
management with multi-server support, auto-detection, IDE-specific templates,
and fallback configurations for missing services.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cli.core.postgres_service import PostgreSQLService
from cli.core.docker_service import DockerService


class MCPConfigManager:
    """Advanced MCP configuration manager with multi-server orchestration.
    
    Features:
    - Multi-server MCP configuration generation
    - Auto-detection of available MCP servers
    - IDE-specific configuration templates
    - Fallback configurations for missing services
    - Health checking and validation
    """

    def __init__(self):
        self.postgres_service = PostgreSQLService()
        self.docker_service = DockerService()
        
        # MCP server definitions with health checks
        self.mcp_servers = {
            "automagik-hive": {
                "type": "command",
                "command": "uvx",
                "args": ["automagik-tools@0.8.17", "tool", "automagik-hive"],
                "env_vars": ["HIVE_API_BASE_URL", "HIVE_API_KEY", "HIVE_TIMEOUT"],
                "health_check": self._check_automagik_hive_health,
                "fallback": True,
                "description": "Automagik Hive agent management and interaction"
            },
            "automagik-forge": {
                "type": "sse",
                "url": "http://localhost:8889/sse",
                "health_check": self._check_automagik_forge_health,
                "fallback": True,
                "description": "Project and task management system"
            },
            "postgres": {
                "type": "command",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
                "connection_required": True,
                "health_check": self._check_postgres_health,
                "fallback": True,
                "description": "PostgreSQL database interface"
            },
            "ask-repo-agent": {
                "type": "sse",
                "url": "https://mcp.deepwiki.com/sse",
                "health_check": self._check_external_sse_health,
                "fallback": False,
                "description": "GitHub repository Q&A agent"
            },
            "search-repo-docs": {
                "type": "command",
                "command": "npx",
                "args": ["-y", "@upstash/context7-mcp"],
                "health_check": self._check_npm_package_health,
                "fallback": False,
                "description": "External library documentation search"
            },
            "send_whatsapp_message": {
                "type": "command",
                "command": "uvx",
                "args": ["automagik-tools@0.7.8", "tool", "evolution-api"],
                "env_vars": ["EVOLUTION_API_BASE_URL", "EVOLUTION_API_API_KEY", "EVOLUTION_API_INSTANCE"],
                "health_check": self._check_whatsapp_health,
                "fallback": False,
                "description": "WhatsApp message integration via Evolution API"
            },
            "wait": {
                "type": "command",
                "command": "uvx",
                "args": ["automagik-tools@0.7.8", "tool", "wait"],
                "health_check": self._check_wait_tool_health,
                "fallback": False,
                "description": "Workflow delay and timing control"
            }
        }

    def generate_mcp_config(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str],
        ide_type: str = "claude-code",
        include_fallbacks: bool = True,
        health_check: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive MCP configuration with auto-detection.
        
        Args:
            workspace_path: Path to the workspace
            credentials: Workspace credentials dictionary
            ide_type: Target IDE type (claude-code, cursor, etc.)
            include_fallbacks: Include fallback configurations
            health_check: Perform health checks before including servers
            
        Returns:
            Complete MCP configuration dictionary
        """
        print("🔍 Detecting available MCP servers...")
        
        # Auto-detect available servers
        available_servers = self._detect_available_servers(
            workspace_path, 
            credentials, 
            health_check
        )
        
        # Generate IDE-specific configuration
        mcp_config = self._generate_ide_config(
            available_servers, 
            credentials,
            ide_type
        )
        
        # Add fallback configurations if requested
        if include_fallbacks:
            mcp_config = self._add_fallback_configurations(
                mcp_config, 
                available_servers,
                credentials
            )
        
        print(f"✅ Generated MCP configuration with {len(mcp_config.get('mcpServers', {}))} servers")
        
        return mcp_config

    def _detect_available_servers(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str],
        health_check: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Auto-detect available MCP servers with health checking.
        
        Returns:
            Dictionary of available servers with their configurations
        """
        available_servers = {}
        
        for server_name, server_config in self.mcp_servers.items():
            print(f"  Checking {server_name}...")
            
            # Skip health check if disabled
            if not health_check:
                available_servers[server_name] = {
                    **server_config,
                    "status": "unknown",
                    "config": self._build_server_config(server_name, server_config, credentials)
                }
                continue
            
            # Perform health check
            is_healthy, status_info = server_config["health_check"](
                workspace_path, 
                credentials
            )
            
            if is_healthy or server_config.get("fallback", False):
                available_servers[server_name] = {
                    **server_config,
                    "status": "healthy" if is_healthy else "fallback",
                    "status_info": status_info,
                    "config": self._build_server_config(server_name, server_config, credentials)
                }
                print(f"    ✅ {server_name}: {'Available' if is_healthy else 'Fallback mode'}")
            else:
                print(f"    ❌ {server_name}: {status_info}")
        
        return available_servers

    def _build_server_config(
        self, 
        server_name: str, 
        server_config: Dict[str, Any], 
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build individual server configuration.
        
        Args:
            server_name: Name of the MCP server
            server_config: Server configuration template
            credentials: Workspace credentials
            
        Returns:
            Complete server configuration
        """
        config = {}
        
        if server_config["type"] == "command":
            config["command"] = server_config["command"]
            config["args"] = server_config["args"].copy()
            
            # Add connection string for postgres
            if server_name == "postgres" and "database_url" in credentials:
                db_url = credentials["database_url"]
                config["args"].append(db_url)
            
            # Add environment variables
            if "env_vars" in server_config:
                config["env"] = self._build_env_vars(server_name, server_config["env_vars"], credentials)
        
        elif server_config["type"] == "sse":
            config["type"] = "sse"
            config["url"] = server_config["url"]
            
            # Handle dynamic URLs
            if server_name == "automagik-forge":
                # Use discovered IP or fallback to localhost
                forge_url = self._get_automagik_forge_url()
                config["url"] = forge_url
        
        return config

    def _build_env_vars(
        self, 
        server_name: str, 
        env_var_names: List[str], 
        credentials: Dict[str, str]
    ) -> Dict[str, str]:
        """Build environment variables for MCP server.
        
        Args:
            server_name: Name of the MCP server
            env_var_names: List of required environment variable names
            credentials: Workspace credentials
            
        Returns:
            Environment variables dictionary
        """
        env_vars = {}
        
        # Automagik Hive specific environment
        if server_name == "automagik-hive":
            env_vars.update({
                "HIVE_API_BASE_URL": "http://localhost:8886",
                "HIVE_API_KEY": credentials.get("hive_api_key", ""),
                "HIVE_TIMEOUT": "300"
            })
        
        # WhatsApp Evolution API specific environment
        elif server_name == "send_whatsapp_message":
            env_vars.update({
                "EVOLUTION_API_BASE_URL": "http://localhost:8080",
                "EVOLUTION_API_API_KEY": "your-evolution-api-key-here",
                "EVOLUTION_API_INSTANCE": "default",
                "EVOLUTION_API_FIXED_RECIPIENT": ""
            })
        
        return env_vars

    def _generate_ide_config(
        self, 
        available_servers: Dict[str, Dict[str, Any]], 
        credentials: Dict[str, str],
        ide_type: str = "claude-code"
    ) -> Dict[str, Any]:
        """Generate IDE-specific MCP configuration.
        
        Args:
            available_servers: Dictionary of available servers
            credentials: Workspace credentials
            ide_type: Target IDE type
            
        Returns:
            IDE-specific MCP configuration
        """
        if ide_type == "claude-code":
            return self._generate_claude_code_config(available_servers)
        elif ide_type == "cursor":
            return self._generate_cursor_config(available_servers)
        else:
            # Generic configuration
            return self._generate_generic_config(available_servers)

    def _generate_claude_code_config(
        self, 
        available_servers: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Claude Code specific MCP configuration.
        
        Args:
            available_servers: Dictionary of available servers
            
        Returns:
            Claude Code MCP configuration
        """
        mcp_servers = {}
        
        for server_name, server_info in available_servers.items():
            mcp_servers[server_name] = server_info["config"]
        
        return {"mcpServers": mcp_servers}

    def _generate_cursor_config(
        self, 
        available_servers: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Cursor IDE specific MCP configuration.
        
        Args:
            available_servers: Dictionary of available servers
            
        Returns:
            Cursor IDE MCP configuration
        """
        # Cursor might have different configuration structure
        servers = {}
        
        for server_name, server_info in available_servers.items():
            servers[server_name] = {
                **server_info["config"],
                "description": server_info.get("description", "")
            }
        
        return {
            "mcp": {
                "servers": servers
            }
        }

    def _generate_generic_config(
        self, 
        available_servers: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate generic MCP configuration.
        
        Args:
            available_servers: Dictionary of available servers
            
        Returns:
            Generic MCP configuration
        """
        return self._generate_claude_code_config(available_servers)

    def _add_fallback_configurations(
        self, 
        mcp_config: Dict[str, Any], 
        available_servers: Dict[str, Dict[str, Any]],
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """Add fallback configurations for missing critical services.
        
        Args:
            mcp_config: Current MCP configuration
            available_servers: Available servers information
            credentials: Workspace credentials
            
        Returns:
            MCP configuration with fallbacks
        """
        fallback_added = False
        servers = mcp_config.get("mcpServers", {})
        
        # Add fallback for postgres if missing
        if "postgres" not in servers and "database_url" in credentials:
            servers["postgres-fallback"] = {
                "command": "echo",
                "args": ["PostgreSQL MCP server not available - install @modelcontextprotocol/server-postgres"]
            }
            fallback_added = True
        
        # Add fallback for automagik-hive if missing
        if "automagik-hive" not in servers:
            servers["automagik-hive-fallback"] = {
                "command": "echo",
                "args": ["Automagik Hive MCP server not available - ensure server is running"]
            }
            fallback_added = True
        
        if fallback_added:
            print("⚠️ Added fallback configurations for unavailable services")
        
        mcp_config["mcpServers"] = servers
        return mcp_config

    def write_mcp_config(
        self, 
        workspace_path: Path, 
        mcp_config: Dict[str, Any],
        filename: str = ".mcp.json"
    ) -> bool:
        """Write MCP configuration to file.
        
        Args:
            workspace_path: Path to workspace
            mcp_config: MCP configuration dictionary
            filename: Configuration filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config_file = workspace_path / filename
            config_file.write_text(json.dumps(mcp_config, indent=2))
            print(f"✅ MCP configuration written to {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to write MCP configuration: {e}")
            return False

    def validate_mcp_config(
        self, 
        workspace_path: Path, 
        filename: str = ".mcp.json"
    ) -> Tuple[bool, List[str]]:
        """Validate existing MCP configuration.
        
        Args:
            workspace_path: Path to workspace
            filename: Configuration filename
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        config_file = workspace_path / filename
        
        if not config_file.exists():
            issues.append(f"MCP configuration file {filename} not found")
            return False, issues
        
        try:
            config = json.loads(config_file.read_text())
        except json.JSONDecodeError as e:
            issues.append(f"Invalid JSON in {filename}: {e}")
            return False, issues
        
        # Validate structure
        if "mcpServers" not in config:
            issues.append("Missing 'mcpServers' section in configuration")
            return False, issues
        
        # Validate server configurations
        for server_name, server_config in config["mcpServers"].items():
            server_issues = self._validate_server_config(server_name, server_config)
            issues.extend(server_issues)
        
        is_valid = len(issues) == 0
        return is_valid, issues

    def _validate_server_config(
        self, 
        server_name: str, 
        server_config: Dict[str, Any]
    ) -> List[str]:
        """Validate individual server configuration.
        
        Args:
            server_name: Name of the server
            server_config: Server configuration
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for required fields
        if "command" in server_config:
            if "args" not in server_config:
                issues.append(f"{server_name}: Missing 'args' for command-based server")
        elif "type" in server_config and server_config["type"] == "sse":
            if "url" not in server_config:
                issues.append(f"{server_name}: Missing 'url' for SSE server")
        else:
            issues.append(f"{server_name}: Invalid server configuration - missing command or SSE type")
        
        return issues

    # Health check methods
    def _check_automagik_hive_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check Automagik Hive server health."""
        try:
            import requests
            response = requests.get("http://localhost:8886/health", timeout=5)
            return response.status_code == 200, "Server responding"
        except Exception as e:
            return False, f"Server not accessible: {str(e)}"

    def _check_automagik_forge_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check Automagik Forge server health."""
        try:
            import requests
            url = self._get_automagik_forge_url().replace("/sse", "/health")
            response = requests.get(url, timeout=5)
            return response.status_code == 200, "Forge server responding"
        except Exception as e:
            return False, f"Forge server not accessible: {str(e)}"

    def _check_postgres_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check PostgreSQL health."""
        if "database_url" not in credentials:
            return False, "No database URL configured"
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(credentials["database_url"])
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    def _check_external_sse_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check external SSE endpoint health."""
        try:
            import requests
            response = requests.get("https://mcp.deepwiki.com/health", timeout=10)
            return response.status_code == 200, "External service available"
        except Exception as e:
            return False, f"External service not available: {str(e)}"

    def _check_npm_package_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check NPM package availability."""
        try:
            result = subprocess.run(
                ["npx", "-y", "@upstash/context7-mcp", "--help"],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0, "NPM package available"
        except Exception as e:
            return False, f"NPM package not available: {str(e)}"

    def _check_whatsapp_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check WhatsApp Evolution API health."""
        try:
            result = subprocess.run(
                ["uvx", "automagik-tools@0.7.8", "tool", "evolution-api", "--help"],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0, "WhatsApp tool available"
        except Exception as e:
            return False, f"WhatsApp tool not available: {str(e)}"

    def _check_wait_tool_health(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Tuple[bool, str]:
        """Check wait tool health."""
        try:
            result = subprocess.run(
                ["uvx", "automagik-tools@0.7.8", "tool", "wait", "--help"],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0, "Wait tool available"
        except Exception as e:
            return False, f"Wait tool not available: {str(e)}"

    def _get_automagik_forge_url(self) -> str:
        """Get Automagik Forge URL with IP discovery."""
        # Try to detect the current IP from the existing .mcp.json if available
        try:
            with open(".mcp.json", "r") as f:
                current_config = json.load(f)
                forge_config = current_config.get("mcpServers", {}).get("automagik-forge", {})
                if "url" in forge_config:
                    return forge_config["url"]
        except Exception:
            pass
        
        # Fallback to localhost
        return "http://localhost:8889/sse"

    def health_check_all_servers(
        self, 
        workspace_path: Path, 
        credentials: Dict[str, str]
    ) -> Dict[str, Tuple[bool, str]]:
        """Perform health check on all configured MCP servers.
        
        Args:
            workspace_path: Path to workspace
            credentials: Workspace credentials
            
        Returns:
            Dictionary mapping server names to (is_healthy, status_message)
        """
        print("🩺 Performing comprehensive MCP server health check...")
        
        health_results = {}
        
        for server_name, server_config in self.mcp_servers.items():
            print(f"  Checking {server_name}...")
            
            is_healthy, status_message = server_config["health_check"](
                workspace_path, 
                credentials
            )
            
            health_results[server_name] = (is_healthy, status_message)
            
            status_icon = "✅" if is_healthy else "❌"
            print(f"    {status_icon} {server_name}: {status_message}")
        
        healthy_count = sum(1 for is_healthy, _ in health_results.values() if is_healthy)
        total_count = len(health_results)
        
        print(f"\n📊 Health Check Summary: {healthy_count}/{total_count} servers healthy")
        
        return health_results