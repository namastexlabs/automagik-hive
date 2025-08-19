"""
Comprehensive Test Suite for DevMode Module

Tests for development mode environment control, including:
- Environment variable detection and validation
- Mode description generation
- Edge cases with various environment values
- Case sensitivity handling
- Default behavior validation
"""

import os
from unittest.mock import patch

import pytest

from lib.versioning.dev_mode import DevMode


class TestDevMode:
    """Test suite for DevMode environment control functionality."""

    def test_is_enabled_default_false(self):
        """Test is_enabled returns False when HIVE_DEV_MODE is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove HIVE_DEV_MODE if it exists
            if "HIVE_DEV_MODE" in os.environ:
                del os.environ["HIVE_DEV_MODE"]
            
            assert DevMode.is_enabled() is False

    def test_is_enabled_true_lowercase(self):
        """Test is_enabled returns True for 'true' (lowercase)."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            assert DevMode.is_enabled() is True

    def test_is_enabled_true_uppercase(self):
        """Test is_enabled returns True for 'TRUE' (uppercase)."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "TRUE"}):
            assert DevMode.is_enabled() is True

    def test_is_enabled_true_mixed_case(self):
        """Test is_enabled returns True for mixed case variations."""
        test_cases = ["True", "TrUe", "tRuE", "TRue"]
        
        for value in test_cases:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is True, f"Failed for value: {value}"

    def test_is_enabled_false_for_false_string(self):
        """Test is_enabled returns False for 'false' string."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "false"}):
            assert DevMode.is_enabled() is False

    def test_is_enabled_false_for_empty_string(self):
        """Test is_enabled returns False for empty string."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": ""}):
            assert DevMode.is_enabled() is False

    def test_is_enabled_false_for_invalid_values(self):
        """Test is_enabled returns False for various invalid values."""
        invalid_values = [
            "1", "0", "yes", "no", "on", "off", 
            "enabled", "disabled", "active", "inactive",
            "True ", " true", "true\n", "\ttrue",
            "True!", "true?", "truee", "tru"
        ]
        
        for value in invalid_values:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is False, f"Should be False for value: '{value}'"

    def test_is_enabled_false_for_numeric_values(self):
        """Test is_enabled returns False for numeric values."""
        numeric_values = ["1", "0", "-1", "100", "0.0", "1.0"]
        
        for value in numeric_values:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is False, f"Should be False for numeric: '{value}'"

    def test_is_enabled_false_for_special_characters(self):
        """Test is_enabled returns False for special characters and symbols."""
        special_values = [
            "!", "@", "#", "$", "%", "^", "&", "*", 
            "(", ")", "-", "_", "+", "=", "[", "]",
            "{", "}", "|", "\\", ":", ";", "\"", "'",
            "<", ">", ",", ".", "?", "/", "`", "~"
        ]
        
        for value in special_values:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is False, f"Should be False for special char: '{value}'"

    def test_get_mode_description_dev_mode(self):
        """Test get_mode_description returns dev mode description when enabled."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            description = DevMode.get_mode_description()
            
            assert "DEV MODE" in description
            assert "YAML only" in description
            assert "no database sync" in description

    def test_get_mode_description_production_mode(self):
        """Test get_mode_description returns production mode description when disabled."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "false"}):
            description = DevMode.get_mode_description()
            
            assert "PRODUCTION MODE" in description
            assert "bidirectional" in description
            assert "DATABASE sync" in description

    def test_get_mode_description_no_env_var(self):
        """Test get_mode_description returns production mode when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            if "HIVE_DEV_MODE" in os.environ:
                del os.environ["HIVE_DEV_MODE"]
            
            description = DevMode.get_mode_description()
            
            assert "PRODUCTION MODE" in description
            assert "bidirectional" in description
            assert "DATABASE sync" in description

    def test_mode_consistency_between_methods(self):
        """Test that is_enabled and get_mode_description are consistent."""
        test_scenarios = [
            ("true", True, "DEV MODE"),
            ("false", False, "PRODUCTION MODE"),
            ("", False, "PRODUCTION MODE"),
            ("invalid", False, "PRODUCTION MODE"),
        ]
        
        for env_value, expected_enabled, expected_mode in test_scenarios:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": env_value}):
                is_enabled = DevMode.is_enabled()
                description = DevMode.get_mode_description()
                
                assert is_enabled == expected_enabled, f"is_enabled mismatch for '{env_value}'"
                assert expected_mode in description, f"Description mismatch for '{env_value}'"


class TestDevModeEdgeCases:
    """Test edge cases and boundary conditions for DevMode."""

    def test_is_enabled_with_whitespace_only(self):
        """Test is_enabled handles whitespace-only values correctly."""
        whitespace_values = [" ", "\t", "\n", "\r", "\r\n", "   ", "\t\t\t"]
        
        for value in whitespace_values:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is False, f"Should be False for whitespace: '{repr(value)}'"

    def test_is_enabled_with_very_long_string(self):
        """Test is_enabled handles very long strings correctly."""
        long_string = "true" + "x" * 10000  # Long string starting with "true"
        
        with patch.dict(os.environ, {"HIVE_DEV_MODE": long_string}):
            assert DevMode.is_enabled() is False

    def test_is_enabled_with_special_escape_sequences(self):
        """Test is_enabled handles escape sequences correctly."""
        escape_values = ["true\\n", "true\\t", "true\\r", "\\true", "true\\x"]
        
        for value in escape_values:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is False, f"Should be False for escape sequence: '{repr(value)}'"

    def test_is_enabled_case_sensitivity_boundary(self):
        """Test is_enabled case sensitivity at word boundaries."""
        boundary_cases = [
            "trUE",   # Mixed case
            "truE",   # Different mixed case
            "TRue",   # Another mixed case
            "tRUe",   # Yet another mixed case
        ]
        
        for value in boundary_cases:
            with patch.dict(os.environ, {"HIVE_DEV_MODE": value}):
                assert DevMode.is_enabled() is True, f"Should be True for mixed case: '{value}'"

    def test_get_mode_description_consistency(self):
        """Test get_mode_description returns consistent format."""
        # Test both modes have consistent description format
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            dev_desc = DevMode.get_mode_description()
        
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "false"}):
            prod_desc = DevMode.get_mode_description()
        
        # Both descriptions should contain "MODE"
        assert "MODE" in dev_desc
        assert "MODE" in prod_desc
        
        # Both should have parenthetical explanations
        assert "(" in dev_desc and ")" in dev_desc
        assert "(" in prod_desc and ")" in prod_desc

    def test_get_mode_description_immutable(self):
        """Test get_mode_description returns the same value for same environment."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            desc1 = DevMode.get_mode_description()
            desc2 = DevMode.get_mode_description()
            
            assert desc1 == desc2

    def test_environment_variable_isolation(self):
        """Test that DevMode doesn't interfere with other environment variables."""
        original_path = os.environ.get("PATH")
        
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            DevMode.is_enabled()
            DevMode.get_mode_description()
            
            # PATH should remain unchanged
            assert os.environ.get("PATH") == original_path

    def test_multiple_rapid_calls(self):
        """Test DevMode stability under rapid successive calls."""
        with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
            results = [DevMode.is_enabled() for _ in range(100)]
            descriptions = [DevMode.get_mode_description() for _ in range(100)]
            
            # All results should be identical
            assert all(r is True for r in results)
            assert all(d == descriptions[0] for d in descriptions)

    def test_thread_safety_simulation(self):
        """Test DevMode behavior under simulated concurrent access."""
        import threading
        import time
        
        results = []
        descriptions = []
        
        def worker():
            with patch.dict(os.environ, {"HIVE_DEV_MODE": "true"}):
                time.sleep(0.001)  # Small delay to simulate race conditions
                results.append(DevMode.is_enabled())
                descriptions.append(DevMode.get_mode_description())
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All results should be consistent
        assert all(r is True for r in results)
        assert all(d == descriptions[0] for d in descriptions)


class TestDevModeIntegration:
    """Integration tests for DevMode with system environment."""

    def test_real_environment_variable_handling(self):
        """Test DevMode with actual environment variable manipulation."""
        # Store original value
        original_value = os.environ.get("HIVE_DEV_MODE")
        
        try:
            # Test setting environment variable directly
            os.environ["HIVE_DEV_MODE"] = "true"
            assert DevMode.is_enabled() is True
            assert "DEV MODE" in DevMode.get_mode_description()
            
            # Test changing environment variable
            os.environ["HIVE_DEV_MODE"] = "false"
            assert DevMode.is_enabled() is False
            assert "PRODUCTION MODE" in DevMode.get_mode_description()
            
            # Test removing environment variable
            del os.environ["HIVE_DEV_MODE"]
            assert DevMode.is_enabled() is False
            assert "PRODUCTION MODE" in DevMode.get_mode_description()
            
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["HIVE_DEV_MODE"] = original_value
            elif "HIVE_DEV_MODE" in os.environ:
                del os.environ["HIVE_DEV_MODE"]

    def test_environment_variable_persistence(self):
        """Test that environment variable changes persist across method calls."""
        original_value = os.environ.get("HIVE_DEV_MODE")
        
        try:
            # Set environment variable
            os.environ["HIVE_DEV_MODE"] = "true"
            
            # Multiple calls should return consistent results
            assert DevMode.is_enabled() is True
            assert DevMode.is_enabled() is True
            assert "DEV MODE" in DevMode.get_mode_description()
            assert "DEV MODE" in DevMode.get_mode_description()
            
            # Change environment variable
            os.environ["HIVE_DEV_MODE"] = "false"
            
            # Results should immediately reflect the change
            assert DevMode.is_enabled() is False
            assert "PRODUCTION MODE" in DevMode.get_mode_description()
            
        finally:
            # Restore original value
            if original_value is not None:
                os.environ["HIVE_DEV_MODE"] = original_value
            elif "HIVE_DEV_MODE" in os.environ:
                del os.environ["HIVE_DEV_MODE"]