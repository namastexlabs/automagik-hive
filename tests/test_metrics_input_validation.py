"""
Unit tests for metrics service input validation edge cases.

Tests ensure that malicious environment variables cannot crash the service
or cause DoS attacks through resource exhaustion.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from lib.logging import logger

from lib.config.settings import Settings


class TestMetricsInputValidation:
    """Test metrics configuration input validation."""
    
    def test_batch_size_validation_normal_values(self):
        """Test that normal batch size values work correctly."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "100"}):
            settings = Settings()
            assert settings.metrics_batch_size == 100
    
    def test_batch_size_validation_minimum_clamp(self):
        """Test that batch size is clamped to minimum value."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "0"}):
            settings = Settings()
            assert settings.metrics_batch_size == 1  # Clamped to minimum
    
    def test_batch_size_validation_negative_clamp(self):
        """Test that negative batch size is clamped to minimum."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "-999999"}):
            settings = Settings()
            assert settings.metrics_batch_size == 1  # Clamped to minimum
    
    def test_batch_size_validation_maximum_clamp(self):
        """Test that batch size is clamped to maximum value."""
        with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "99999999"}):
            settings = Settings()
            assert settings.metrics_batch_size == 10000  # Clamped to maximum
    
    def test_batch_size_validation_invalid_string(self):
        """Test that invalid string falls back to default."""
        with patch('lib.logging.logger') as mock_logger:
            with patch.dict(os.environ, {"HIVE_METRICS_BATCH_SIZE": "not_a_number"}):
                settings = Settings()
                assert settings.metrics_batch_size == 50  # Default value
                mock_logger.error.assert_called()
    
    def test_flush_interval_validation_normal_values(self):
        """Test that normal flush interval values work correctly."""
        with patch.dict(os.environ, {"HIVE_METRICS_FLUSH_INTERVAL": "10.0"}):
            settings = Settings()
            assert settings.metrics_flush_interval == 10.0
    
    def test_flush_interval_validation_minimum_clamp(self):
        """Test that flush interval is clamped to minimum value."""
        with patch.dict(os.environ, {"HIVE_METRICS_FLUSH_INTERVAL": "0.001"}):
            settings = Settings()
            assert settings.metrics_flush_interval == 0.1  # Clamped to minimum
    
    def test_flush_interval_validation_negative_clamp(self):
        """Test that negative flush interval is clamped to minimum."""
        with patch.dict(os.environ, {"HIVE_METRICS_FLUSH_INTERVAL": "-5.0"}):
            settings = Settings()
            assert settings.metrics_flush_interval == 0.1  # Clamped to minimum
    
    def test_flush_interval_validation_maximum_clamp(self):
        """Test that flush interval is clamped to maximum value."""
        with patch.dict(os.environ, {"HIVE_METRICS_FLUSH_INTERVAL": "99999.0"}):
            settings = Settings()
            assert settings.metrics_flush_interval == 3600.0  # Clamped to maximum
    
    def test_flush_interval_validation_invalid_string(self):
        """Test that invalid string falls back to default."""
        with patch('lib.logging.logger') as mock_logger:
            with patch.dict(os.environ, {"HIVE_METRICS_FLUSH_INTERVAL": "not_a_float"}):
                settings = Settings()
                assert settings.metrics_flush_interval == 5.0  # Default value
                mock_logger.error.assert_called()
    
    def test_queue_size_validation_normal_values(self):
        """Test that normal queue size values work correctly."""
        with patch.dict(os.environ, {"HIVE_METRICS_QUEUE_SIZE": "2000"}):
            settings = Settings()
            assert settings.metrics_queue_size == 2000
    
    def test_queue_size_validation_minimum_clamp(self):
        """Test that queue size is clamped to minimum value."""
        with patch.dict(os.environ, {"HIVE_METRICS_QUEUE_SIZE": "5"}):
            settings = Settings()
            assert settings.metrics_queue_size == 10  # Clamped to minimum
    
    def test_queue_size_validation_negative_clamp(self):
        """Test that negative queue size is clamped to minimum."""
        with patch.dict(os.environ, {"HIVE_METRICS_QUEUE_SIZE": "-1000"}):
            settings = Settings()
            assert settings.metrics_queue_size == 10  # Clamped to minimum
    
    def test_queue_size_validation_maximum_clamp(self):
        """Test that queue size is clamped to maximum value."""
        with patch.dict(os.environ, {"HIVE_METRICS_QUEUE_SIZE": "999999"}):
            settings = Settings()
            assert settings.metrics_queue_size == 100000  # Clamped to maximum
    
    def test_queue_size_validation_invalid_string(self):
        """Test that invalid string falls back to default."""
        with patch('lib.logging.logger') as mock_logger:
            with patch.dict(os.environ, {"HIVE_METRICS_QUEUE_SIZE": "invalid_number"}):
                settings = Settings()
                assert settings.metrics_queue_size == 1000  # Default value
                mock_logger.error.assert_called()
    
    def test_dos_attack_prevention_extreme_values(self):
        """Test prevention of DoS attacks via extreme configuration values."""
        # Test extreme values that could cause resource exhaustion
        with patch('lib.logging.logger') as mock_logger:
            with patch.dict(os.environ, {
                "HIVE_METRICS_BATCH_SIZE": "999999999",
                "HIVE_METRICS_FLUSH_INTERVAL": "0.001",
                "HIVE_METRICS_QUEUE_SIZE": "99999999999"
            }):
                settings = Settings()
                
                # All values should be clamped to safe limits
                assert settings.metrics_batch_size == 10000
                assert settings.metrics_flush_interval == 0.1
                assert settings.metrics_queue_size == 100000
                
                # Should log warnings about clamping
                assert mock_logger.warning.call_count >= 3
    
    def test_type_error_handling(self):
        """Test handling of type errors in environment variable parsing."""
        with patch('lib.logging.logger') as mock_logger:
            # Mock os.getenv to return non-string values (edge case)
            with patch('os.getenv') as mock_getenv:
                # Return None for all metrics environment variables
                def getenv_side_effect(key, default=None):
                    if key.startswith("HIVE_METRICS_"):
                        return None
                    return default
                
                mock_getenv.side_effect = getenv_side_effect
                
                settings = Settings()
                
                # Should fall back to defaults
                assert settings.metrics_batch_size == 50
                assert settings.metrics_flush_interval == 5.0
                assert settings.metrics_queue_size == 1000
    
    def test_logging_of_clamped_values(self):
        """Test that clamped values are properly logged."""
        with patch('lib.logging.logger') as mock_logger:
            with patch.dict(os.environ, {
                "HIVE_METRICS_BATCH_SIZE": "20000",  # Will be clamped to 10000
                "HIVE_METRICS_FLUSH_INTERVAL": "0.01",  # Will be clamped to 0.1
                "HIVE_METRICS_QUEUE_SIZE": "200000"  # Will be clamped to 100000
            }):
                settings = Settings()
                
                # Check that warning messages contain clamping information
                warning_calls = mock_logger.warning.call_args_list
                assert len(warning_calls) == 3
                
                # Verify specific clamping messages
                messages = [str(call) for call in warning_calls]
                assert any("HIVE_METRICS_BATCH_SIZE clamped from 20000 to 10000" in msg for msg in messages)
                assert any("HIVE_METRICS_FLUSH_INTERVAL clamped from 0.01 to 0.1" in msg for msg in messages)
                assert any("HIVE_METRICS_QUEUE_SIZE clamped from 200000 to 100000" in msg for msg in messages)
    
    def test_enable_metrics_boolean_parsing(self):
        """Test that HIVE_ENABLE_METRICS boolean parsing works correctly."""
        # Test true values
        for true_value in ["true", "TRUE", "True", "yes", "1"]:
            with patch.dict(os.environ, {"HIVE_ENABLE_METRICS": true_value}):
                settings = Settings()
                assert settings.enable_metrics is True
        
        # Test false values
        for false_value in ["false", "FALSE", "False", "no", "0", "disabled"]:
            with patch.dict(os.environ, {"HIVE_ENABLE_METRICS": false_value}):
                settings = Settings()
                assert settings.enable_metrics is False
    
    def test_all_defaults_when_no_env_vars(self):
        """Test that all default values are used when no environment variables are set."""
        # Clear all metrics-related environment variables
        metrics_env_vars = [
            "HIVE_ENABLE_METRICS",
            "HIVE_METRICS_BATCH_SIZE", 
            "HIVE_METRICS_FLUSH_INTERVAL",
            "HIVE_METRICS_QUEUE_SIZE"
        ]
        
        with patch.dict(os.environ, {var: "" for var in metrics_env_vars}, clear=False):
            # Remove the variables entirely
            for var in metrics_env_vars:
                if var in os.environ:
                    del os.environ[var]
            
            settings = Settings()
            
            # All should use defaults
            assert settings.enable_metrics is True  # Default true
            assert settings.metrics_batch_size == 50
            assert settings.metrics_flush_interval == 5.0
            assert settings.metrics_queue_size == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])