"""MCP Configuration Test CLI Commands.

This module provides testing commands for the multi-server MCP integration
system to validate configuration generation, server detection, and health checking.
"""

import json
from pathlib import Path
from typing import Dict, Any

from cli.core.mcp_config_manager import MCPConfigManager


class MCPTestCommands:
    """MCP configuration testing command implementations."""

    def __init__(self):
        self.mcp_config_manager = MCPConfigManager()

    def test_mcp_generation(self, workspace_path: str = ".") -> bool:
        """Test MCP configuration generation with mock credentials.
        
        Args:
            workspace_path: Path to test workspace (default: current directory)
            
        Returns:
            True if test successful, False otherwise
        """
        print("🧪 Testing MCP Configuration Generation...")
        
        workspace_path_obj = Path(workspace_path).resolve()
        print(f"📁 Test workspace: {workspace_path_obj}")
        
        # Mock credentials for testing
        test_credentials = {
            "database_url": "postgresql+psycopg://test_user:test_pass@localhost:5532/test_hive",
            "hive_api_key": "hive_test_key_12345"
        }
        
        try:
            # Test configuration generation
            print("\n🔧 Generating MCP configuration...")
            mcp_config = self.mcp_config_manager.generate_mcp_config(
                workspace_path=workspace_path_obj,
                credentials=test_credentials,
                ide_type="claude-code",
                include_fallbacks=True,
                health_check=False  # Skip health checks for testing
            )
            
            print("✅ MCP configuration generated successfully")
            print(f"   • Found {len(mcp_config.get('mcpServers', {}))} MCP servers")
            
            # Display generated configuration
            print("\n📋 Generated Configuration Preview:")
            for server_name in mcp_config.get('mcpServers', {}):
                print(f"   • {server_name}")
            
            # Test validation
            print("\n🔍 Validating configuration...")
            is_valid, issues = self.mcp_config_manager.validate_mcp_config(
                workspace_path_obj, 
                ".mcp.json.test"
            )
            
            # Write test configuration
            test_config_file = workspace_path_obj / ".mcp.json.test"
            test_config_file.write_text(json.dumps(mcp_config, indent=2))
            print(f"📝 Test configuration written to: {test_config_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ MCP configuration test failed: {e}")
            return False

    def test_health_checks(self, workspace_path: str = ".") -> bool:
        """Test MCP server health checking functionality.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if test successful, False otherwise
        """
        print("🩺 Testing MCP Server Health Checks...")
        
        workspace_path_obj = Path(workspace_path).resolve()
        
        # Mock credentials for health checking
        test_credentials = {
            "database_url": "postgresql+psycopg://test_user:test_pass@localhost:5532/test_hive",
            "hive_api_key": "hive_test_key_12345"
        }
        
        try:
            # Perform health checks
            health_results = self.mcp_config_manager.health_check_all_servers(
                workspace_path_obj,
                test_credentials
            )
            
            print(f"\n📊 Health Check Results:")
            for server_name, (is_healthy, status) in health_results.items():
                status_icon = "✅" if is_healthy else "❌"
                print(f"   {status_icon} {server_name}: {status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Health check test failed: {e}")
            return False

    def test_ide_configs(self, workspace_path: str = ".") -> bool:
        """Test IDE-specific configuration generation.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if test successful, False otherwise
        """
        print("🖥️ Testing IDE-Specific Configuration Generation...")
        
        workspace_path_obj = Path(workspace_path).resolve()
        
        # Mock credentials
        test_credentials = {
            "database_url": "postgresql+psycopg://test_user:test_pass@localhost:5532/test_hive",
            "hive_api_key": "hive_test_key_12345"
        }
        
        ide_types = ["claude-code", "cursor", "generic"]
        
        try:
            for ide_type in ide_types:
                print(f"\n🔧 Testing {ide_type} configuration...")
                
                mcp_config = self.mcp_config_manager.generate_mcp_config(
                    workspace_path=workspace_path_obj,
                    credentials=test_credentials,
                    ide_type=ide_type,
                    include_fallbacks=True,
                    health_check=False
                )
                
                # Write IDE-specific test config
                config_file = workspace_path_obj / f".mcp.{ide_type}.test.json"
                config_file.write_text(json.dumps(mcp_config, indent=2))
                print(f"   ✅ {ide_type} config written to: {config_file}")
            
            print(f"\n🎉 All {len(ide_types)} IDE configurations generated successfully")
            return True
            
        except Exception as e:
            print(f"❌ IDE configuration test failed: {e}")
            return False

    def cleanup_test_files(self, workspace_path: str = ".") -> bool:
        """Clean up test configuration files.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if cleanup successful, False otherwise
        """
        print("🧹 Cleaning up test files...")
        
        workspace_path_obj = Path(workspace_path).resolve()
        
        test_files = [
            ".mcp.json.test",
            ".mcp.claude-code.test.json",
            ".mcp.cursor.test.json", 
            ".mcp.generic.test.json"
        ]
        
        cleaned_count = 0
        
        for test_file in test_files:
            file_path = workspace_path_obj / test_file
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"   🗑️ Removed: {test_file}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   ⚠️ Could not remove {test_file}: {e}")
        
        if cleaned_count > 0:
            print(f"✅ Cleaned up {cleaned_count} test files")
        else:
            print("ℹ️ No test files found to clean up")
        
        return True

    def run_full_test_suite(self, workspace_path: str = ".") -> bool:
        """Run complete MCP configuration test suite.
        
        Args:
            workspace_path: Path to workspace (default: current directory)
            
        Returns:
            True if all tests pass, False otherwise
        """
        print("🚀 Running Full MCP Configuration Test Suite...")
        print("=" * 60)
        
        tests = [
            ("Configuration Generation", self.test_mcp_generation),
            ("Health Checks", self.test_health_checks),
            ("IDE Configurations", self.test_ide_configs),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            print("-" * 40)
            
            try:
                if test_func(workspace_path):
                    print(f"✅ {test_name}: PASSED")
                    passed_tests += 1
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! MCP integration is working correctly.")
        else:
            print("⚠️ Some tests failed. Check the output above for details.")
        
        # Cleanup test files
        self.cleanup_test_files(workspace_path)
        
        return passed_tests == total_tests