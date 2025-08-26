"""Tests for Jack Retrieval Agent __init__.py

Test module imports and exports.
"""

import pytest


class TestJackRetrievalAgentInit:
    """Test cases for jack_retrieval module initialization."""
    
    def test_import_get_jack_retrieval_agent(self):
        """Test that get_jack_retrieval_agent can be imported."""
        from ai.agents.jack_retrieval import get_jack_retrieval_agent
        
        # Should import without error
        assert get_jack_retrieval_agent is not None
        assert callable(get_jack_retrieval_agent)
    
    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        import ai.agents.jack_retrieval as jack_retrieval_module
        
        # Should have __all__ defined
        assert hasattr(jack_retrieval_module, "__all__")
        assert "get_jack_retrieval_agent" in jack_retrieval_module.__all__
        assert len(jack_retrieval_module.__all__) == 1
    
    def test_module_docstring(self):
        """Test that module has appropriate docstring."""
        import ai.agents.jack_retrieval as jack_retrieval_module
        
        assert jack_retrieval_module.__doc__ is not None
        assert "Jack Retrieval Agent" in jack_retrieval_module.__doc__
        assert "WhatsApp" in jack_retrieval_module.__doc__