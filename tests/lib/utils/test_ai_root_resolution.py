
"""
Regression tests for external AI folder functionality.
Tests AI root resolution with different scenarios.
"""

import os
import tempfile
import pytest
from pathlib import Path
from lib.utils.ai_root import resolve_ai_root
from lib.config.settings import get_settings


class TestExternalAIFolderSupport:
    """Test external AI folder support and AI root resolution."""
    
    def test_default_ai_root_resolution(self):
        """Test that default AI root resolves to repo ai/ directory."""
        settings = get_settings()
        ai_root = resolve_ai_root(None, settings)
        
        # Should resolve to repo ai/ directory (absolute path)
        assert ai_root.name == "ai"
        assert ai_root.exists()
        assert (ai_root / "agents").exists()
        assert (ai_root / "teams").exists()
        assert (ai_root / "workflows").exists()
    
    def test_environment_variable_override(self):
        """Test AI root resolution with HIVE_AI_ROOT environment variable."""
        # Set environment variable
        original_env = os.environ.get("HIVE_AI_ROOT")
        os.environ["HIVE_AI_ROOT"] = "/tmp/test-ai"
        
        try:
            settings = get_settings()
            ai_root = resolve_ai_root(None, settings)
            
            assert ai_root == Path("/tmp/test-ai")
            assert ai_root.exists()
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["HIVE_AI_ROOT"] = original_env
            elif "HIVE_AI_ROOT" in os.environ:
                del os.environ["HIVE_AI_ROOT"]
    
    def test_explicit_path_argument(self):
        """Test AI root resolution with explicit path argument."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create required subdirectories
            ai_dir = Path(temp_dir) / "custom-ai"
            (ai_dir / "agents").mkdir(parents=True)
            (ai_dir / "teams").mkdir()
            (ai_dir / "workflows").mkdir()
            
            settings = get_settings()
            ai_root = resolve_ai_root(str(ai_dir), settings)
            
            assert ai_root == ai_dir
            assert ai_root.exists()
    
    def test_error_handling_missing_directory(self):
        """Test error handling when AI root directory doesn't exist."""
        settings = get_settings()
        
        with pytest.raises(FileNotFoundError, match="AI root directory does not exist"):
            resolve_ai_root("/tmp/nonexistent-ai", settings)
    
    def test_error_handling_missing_subdirectories(self):
        """Test error handling when required subdirectories are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ai_dir = Path(temp_dir) / "incomplete-ai"
            ai_dir.mkdir()
            
            settings = get_settings()
            
            with pytest.raises(ValueError, match="Missing: agents, teams, workflows"):
                resolve_ai_root(str(ai_dir), settings)
    
    def test_backwards_compatibility(self):
        """Test that existing functionality still works without external folder."""
        settings = get_settings()
        ai_root = resolve_ai_root(None, settings)
        
        # Should still work with default repo structure
        assert ai_root.exists()
        assert (ai_root / "agents").exists()
        assert (ai_root / "teams").exists()
        assert (ai_root / "workflows").exists()
        
        # Should be able to import registries
        from ai.agents.registry import AgentRegistry
        
        # Should be able to list available components
        agent_registry = AgentRegistry()
        agents = agent_registry.list_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
