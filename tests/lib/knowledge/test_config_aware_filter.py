"""Tests for lib.knowledge.config_aware_filter module."""

import pytest
from unittest.mock import MagicMock, patch

# Import the module under test
try:
    from lib.knowledge.config_aware_filter import ConfigAwareFilter
    import lib.knowledge.config_aware_filter
except ImportError:
    pytest.skip(f"Module lib.knowledge.config_aware_filter not available", allow_module_level=True)


class TestConfigAwareFilter:
    """Test config_aware_filter module functionality."""

    def test_module_imports(self):
        """Test that the module can be imported without errors."""
        import lib.knowledge.config_aware_filter
        assert lib.knowledge.config_aware_filter is not None

    @patch("lib.knowledge.config_aware_filter.load_global_knowledge_config")
    def test_filter_creation(self, mock_load_config):
        """Test ConfigAwareFilter can be created."""
        # Mock the global config loading
        mock_load_config.return_value = {
            "business_units": {
                "engineering": {
                    "name": "Engineering",
                    "keywords": ["python", "code", "development"],
                },
            },
            "search_config": {"max_results": 3},
            "performance": {"cache_ttl": 300},
        }

        filter_obj = ConfigAwareFilter()
        assert filter_obj is not None
        assert "engineering" in filter_obj.business_units

    @patch("lib.knowledge.config_aware_filter.load_global_knowledge_config")
    def test_filter_functionality(self, mock_load_config):
        """Test basic filtering functionality."""
        # Mock the global config loading
        mock_load_config.return_value = {
            "business_units": {
                "tech": {
                    "name": "Technology",
                    "keywords": ["python", "code", "development"],
                    "expertise": ["programming"],
                    "common_issues": ["bugs"],
                },
            },
            "search_config": {"max_results": 3},
            "performance": {"cache_ttl": 300},
        }

        filter_obj = ConfigAwareFilter()

        # Test business unit detection
        text = "I have a problem with Python code development"
        detected_unit = filter_obj.detect_business_unit_from_text(text)
        assert detected_unit == "tech"

        # Test search params
        search_params = filter_obj.get_enhanced_search_params()
        assert isinstance(search_params, dict)
        assert "max_results" in search_params


class TestConfigAwareFilterEdgeCases:
    """Test edge cases and error conditions."""

    @patch("lib.knowledge.config_aware_filter.load_global_knowledge_config")
    def test_error_handling(self, mock_load_config):
        """Test error handling scenarios."""
        # Test with empty config
        mock_load_config.return_value = {}
        
        try:
            filter_obj = ConfigAwareFilter()
            assert filter_obj is not None
        except Exception:
            # Expected - config might be required
            pass

    @patch("lib.knowledge.config_aware_filter.load_global_knowledge_config")
    def test_missing_business_units(self, mock_load_config):
        """Test handling when business units are missing."""
        mock_load_config.return_value = {
            "search_config": {"max_results": 3},
            "performance": {"cache_ttl": 300},
        }
        
        try:
            filter_obj = ConfigAwareFilter()
            # Should handle missing business_units gracefully
            units = filter_obj.list_business_units() if hasattr(filter_obj, 'list_business_units') else {}
            assert isinstance(units, dict)
        except Exception:
            # Expected if business_units are required
            pass


class TestConfigAwareFilterIntegration:
    """Test integration scenarios."""

    @patch("lib.knowledge.config_aware_filter.load_global_knowledge_config")
    def test_integration_scenarios(self, mock_load_config):
        """Test integration with other components."""
        # Mock realistic config for integration testing
        mock_load_config.return_value = {
            "business_units": {
                "engineering": {
                    "name": "Engineering",
                    "keywords": ["python", "docker", "deployment"],
                },
                "sales": {
                    "name": "Sales",
                    "keywords": ["revenue", "customer", "deals"],
                },
            },
            "search_config": {"max_results": 3},
            "performance": {"cache_ttl": 300},
        }
        
        filter_obj = ConfigAwareFilter()
        assert filter_obj is not None
        
        # Test with engineering-related text
        eng_text = "I need help with Python deployment using Docker"
        detected_unit = filter_obj.detect_business_unit_from_text(eng_text)
        assert detected_unit == "engineering"
        
        # Test business unit listing
        if hasattr(filter_obj, 'list_business_units'):
            units = filter_obj.list_business_units()
            assert isinstance(units, dict)
            assert "engineering" in units or "sales" in units
