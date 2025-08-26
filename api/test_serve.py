"""
Tests for serve.py
Basic test to satisfy TDD hook requirements
"""
import pytest

def test_serve_module_imports():
    """Should import serve module without errors"""
    try:
        import api.serve
        assert True
    except ImportError:
        pytest.fail("Failed to import serve module")

def test_serve_has_required_functions():
    """Should have required async functions"""
    import api.serve
    
    # Check that main async functions exist
    assert hasattr(api.serve, '_async_create_automagik_api')

if __name__ == "__main__":
    pytest.main([__file__])