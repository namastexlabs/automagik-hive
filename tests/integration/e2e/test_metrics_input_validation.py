"""
Unit tests for metrics service input validation - FIXED VERSION.

Tests updated to work with current HiveSettings implementation:
- Uses correct attribute names (hive_metrics_*)
- Expects ValidationError for boundary values (no clamping)
- Validates current fail-fast behavior
"""

import os
import pytest
from unittest.mock import patch
from pydantic_core import ValidationError

from lib.config.settings import HiveSettings

# Mock missing Settings class for backward compatibility
Settings = HiveSettings


class TestMetricsInputValidation:
    """Test metrics configuration input validation."""

    def _get_base_env(self):
        """Get base environment variables required for HiveSettings."""
        return {
            'HIVE_ENVIRONMENT': 'development',
            'HIVE_API_PORT': '8886',
            'HIVE_DATABASE_URL': 'postgresql://localhost:5432/hive_test',
            'HIVE_API_KEY': 'hive_test_key_1234567890123456789012345678901234567890',
            'HIVE_CORS_ORIGINS': 'http://localhost:3000',
        }

    def test_batch_size_validation_normal_values(self):
        """Test that normal batch size values work correctly."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_BATCH_SIZE": "100"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_batch_size == 100

    def test_batch_size_validation_minimum_bound(self):
        """Test that minimum batch size boundary is enforced."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_BATCH_SIZE": "1"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_batch_size == 1

    def test_batch_size_validation_maximum_bound(self):
        """Test that maximum batch size boundary is enforced."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_BATCH_SIZE": "10000"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_batch_size == 10000

    def test_batch_size_validation_below_minimum_fails(self):
        """Test that batch size below minimum raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_BATCH_SIZE": "0"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Metrics batch size must be between 1-10000" in str(exc_info.value)

    def test_batch_size_validation_above_maximum_fails(self):
        """Test that batch size above maximum raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_BATCH_SIZE": "99999999"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Metrics batch size must be between 1-10000" in str(exc_info.value)

    def test_batch_size_validation_invalid_string_fails(self):
        """Test that invalid string raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_BATCH_SIZE": "not_a_number"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Input should be a valid integer" in str(exc_info.value)

    def test_flush_interval_validation_normal_values(self):
        """Test that normal flush interval values work correctly."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_FLUSH_INTERVAL": "10.0"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_flush_interval == 10.0

    def test_flush_interval_validation_minimum_bound(self):
        """Test that minimum flush interval boundary is enforced."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_FLUSH_INTERVAL": "0.1"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_flush_interval == 0.1

    def test_flush_interval_validation_maximum_bound(self):
        """Test that maximum flush interval boundary is enforced."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_FLUSH_INTERVAL": "3600.0"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_flush_interval == 3600.0

    def test_flush_interval_validation_below_minimum_fails(self):
        """Test that flush interval below minimum raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_FLUSH_INTERVAL": "0.001"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Metrics flush interval must be between 0.1-3600" in str(exc_info.value)

    def test_flush_interval_validation_above_maximum_fails(self):
        """Test that flush interval above maximum raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_FLUSH_INTERVAL": "99999.0"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Metrics flush interval must be between 0.1-3600" in str(exc_info.value)

    def test_flush_interval_validation_invalid_string_fails(self):
        """Test that invalid string raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_FLUSH_INTERVAL": "not_a_float"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Input should be a valid number" in str(exc_info.value)

    def test_queue_size_validation_normal_values(self):
        """Test that normal queue size values work correctly."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_QUEUE_SIZE": "2000"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_queue_size == 2000

    def test_queue_size_validation_minimum_bound(self):
        """Test that minimum queue size boundary is enforced."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_QUEUE_SIZE": "10"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_queue_size == 10

    def test_queue_size_validation_maximum_bound(self):
        """Test that maximum queue size boundary is enforced."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_QUEUE_SIZE": "100000"})
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.hive_metrics_queue_size == 100000

    def test_queue_size_validation_below_minimum_fails(self):
        """Test that queue size below minimum raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_QUEUE_SIZE": "5"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Metrics queue size must be between 10-100000" in str(exc_info.value)

    def test_queue_size_validation_above_maximum_fails(self):
        """Test that queue size above maximum raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_QUEUE_SIZE": "999999"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Metrics queue size must be between 10-100000" in str(exc_info.value)

    def test_queue_size_validation_invalid_string_fails(self):
        """Test that invalid string raises ValidationError."""
        env = self._get_base_env()
        env.update({"HIVE_METRICS_QUEUE_SIZE": "invalid_number"})
        
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Input should be a valid integer" in str(exc_info.value)

    def test_dos_attack_prevention_extreme_values(self):
        """Test prevention of DoS attacks via extreme configuration values."""
        env = self._get_base_env()
        env.update({
            "HIVE_METRICS_BATCH_SIZE": "999999999",
            "HIVE_METRICS_FLUSH_INTERVAL": "0.001", 
            "HIVE_METRICS_QUEUE_SIZE": "99999999999",
        })
        
        # All extreme values should cause validation errors (fail-fast)
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            # Should have multiple validation errors
            errors = exc_info.value.errors()
            assert len(errors) == 3  # One for each invalid field

    def test_enable_metrics_boolean_parsing(self):
        """Test that HIVE_ENABLE_METRICS boolean parsing works correctly."""
        env = self._get_base_env()
        
        # Test true values
        for true_value in ["true", "TRUE", "True", "yes", "1"]:
            env.update({"HIVE_ENABLE_METRICS": true_value})
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.hive_enable_metrics is True

        # Test false values  
        for false_value in ["false", "FALSE", "False", "no", "0"]:
            env.update({"HIVE_ENABLE_METRICS": false_value})
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.hive_enable_metrics is False

    def test_all_defaults_when_no_metrics_env_vars(self):
        """Test that all default values are used when no metrics environment variables are set."""
        env = self._get_base_env()
        # Explicitly don't set any metrics environment variables
        
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()

            # All should use defaults from Field definitions
            assert settings.hive_enable_metrics is True  # Default from Field
            assert settings.hive_metrics_batch_size == 50  # Default from Field
            assert settings.hive_metrics_flush_interval == 5.0  # Default from Field
            assert settings.hive_metrics_queue_size == 1000  # Default from Field


if __name__ == "__main__":
    pytest.main([__file__, "-v"])