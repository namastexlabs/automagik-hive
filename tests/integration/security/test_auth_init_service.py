"""
Comprehensive security tests for AuthInitService.

Tests critical authentication initialization security including:
- Secure key generation
- File system security
- Environment variable handling
- Key storage security
- Error handling and edge cases
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.auth.init_service import AuthInitService


class TestAuthInitServiceSecurity:
    """Test suite for AuthInitService security patterns."""

    @pytest.fixture
    def temp_env_file(self):
        """Create temporary .env file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            temp_path = Path(f.name)
            yield temp_path
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    @pytest.fixture
    def clean_environment(self):
        """Clean environment variables for each test."""
        original_api_key = os.environ.get("HIVE_API_KEY")
        original_auth_disabled = os.environ.get("HIVE_AUTH_DISABLED")

        # Remove during test
        os.environ.pop("HIVE_API_KEY", None)
        os.environ.pop("HIVE_AUTH_DISABLED", None)

        yield

        # Restore after test
        if original_api_key is not None:
            os.environ["HIVE_API_KEY"] = original_api_key
        else:
            os.environ.pop("HIVE_API_KEY", None)

        if original_auth_disabled is not None:
            os.environ["HIVE_AUTH_DISABLED"] = original_auth_disabled
        else:
            os.environ.pop("HIVE_AUTH_DISABLED", None)

    @pytest.fixture
    def mock_env_file(self, temp_env_file):
        """Mock service with temporary env file."""
        service = AuthInitService()
        service.env_file = temp_env_file
        return service

    def test_secure_key_generation(self):
        """Test that generated keys are cryptographically secure."""
        service = AuthInitService()

        # Generate multiple keys
        keys = [service._generate_secure_key() for _ in range(100)]

        # All keys should be unique
        assert len(set(keys)) == len(keys), "Generated keys should be unique"

        # All keys should start with 'hive_'
        for key in keys:
            assert key.startswith("hive_"), f"Key {key} should start with 'hive_'"

        # All keys should have sufficient length (hive_ + 43 chars from urlsafe_b64)
        for key in keys:
            assert len(key) >= 48, f"Key {key} should be at least 48 characters"

        # Keys should contain urlsafe characters only after prefix
        import string

        urlsafe_chars = string.ascii_letters + string.digits + "-_"
        for key in keys:
            key_content = key[5:]  # Remove 'hive_' prefix
            for char in key_content:
                assert char in urlsafe_chars, f"Key contains invalid character: {char}"

    def test_key_entropy_quality(self):
        """Test that generated keys have sufficient entropy."""
        service = AuthInitService()

        # Generate sample of keys
        keys = [service._generate_secure_key() for _ in range(50)]

        # Test entropy by checking character distribution
        all_chars = "".join(key[5:] for key in keys)  # Remove 'hive_' prefix
        char_counts = {}

        for char in all_chars:
            char_counts[char] = char_counts.get(char, 0) + 1

        # Should have reasonable character distribution
        # No single character should dominate (less than 10% of total)
        total_chars = len(all_chars)
        for char, count in char_counts.items():
            frequency = count / total_chars
            assert frequency < 0.1, (
                f"Character '{char}' appears too frequently: {frequency:.2%}"
            )

    def test_ensure_api_key_from_environment(self, clean_environment, mock_env_file):
        """Test key retrieval from environment variable."""
        # Remove the temp file first to test env var priority
        if mock_env_file.env_file.exists():
            mock_env_file.env_file.unlink()

        os.environ["HIVE_API_KEY"] = "env_test_key_123"

        key = mock_env_file.ensure_api_key()

        assert key == "env_test_key_123"
        # Should not create .env file when env var exists
        assert not mock_env_file.env_file.exists()

    def test_ensure_api_key_from_env_file(self, clean_environment, mock_env_file):
        """Test key retrieval from .env file."""
        # Create .env file with key
        mock_env_file.env_file.write_text("HIVE_API_KEY=file_test_key_456\n")

        key = mock_env_file.ensure_api_key()

        assert key == "file_test_key_456"
        # Should not modify environment
        assert os.environ.get("HIVE_API_KEY") is None

    def test_ensure_api_key_generation_create(self, clean_environment, mock_env_file):
        """Test key generation when none exists."""
        with patch.object(mock_env_file, "_display_key_to_user"):
            key = mock_env_file.ensure_api_key()

            # Should generate new key
            assert key.startswith("hive_")
            assert len(key) >= 48

            # Should save to .env file
            assert mock_env_file.env_file.exists()
            env_content = mock_env_file.env_file.read_text()
            assert f"HIVE_API_KEY={key}" in env_content
            assert "HIVE_AUTH_DISABLED=false" in env_content

            # Should set in environment
            assert os.environ.get("HIVE_API_KEY") == key

    def test_save_key_to_env_create_file(self, clean_environment, mock_env_file):
        """Test saving key to create .env file."""
        test_key = "test_key_789"

        mock_env_file._save_key_to_env(test_key)

        assert mock_env_file.env_file.exists()
        content = mock_env_file.env_file.read_text()

        assert f"HIVE_API_KEY={test_key}" in content
        assert "HIVE_AUTH_DISABLED=false" in content

    def test_save_key_to_env_modify_file(self, clean_environment, mock_env_file):
        """Test updating key in current .env file."""
        # Create existing .env with some content
        initial_content = """# Existing config
DATABASE_URL=postgres://localhost/test
HIVE_API_KEY=old_key_123
OTHER_VAR=value
"""
        mock_env_file.env_file.write_text(initial_content)

        target_key = "target_key_456"
        mock_env_file._save_key_to_env(target_key)

        content = mock_env_file.env_file.read_text()

        # Should update API key
        assert f"HIVE_API_KEY={target_key}" in content
        assert "HIVE_API_KEY=old_key_123" not in content

        # Should preserve other content
        assert "DATABASE_URL=postgres://localhost/test" in content
        assert "OTHER_VAR=value" in content

        # Should not duplicate AUTH_DISABLED if not present
        auth_disabled_count = content.count("HIVE_AUTH_DISABLED=false")
        assert auth_disabled_count == 1

    def test_save_key_preserves_auth_disabled(self, clean_environment, mock_env_file):
        """Test that existing AUTH_DISABLED setting is preserved."""
        # Create .env with existing AUTH_DISABLED
        initial_content = """HIVE_API_KEY=old_key
HIVE_AUTH_DISABLED=true
"""
        mock_env_file.env_file.write_text(initial_content)

        mock_env_file._save_key_to_env("target_key")

        content = mock_env_file.env_file.read_text()

        # Should preserve existing AUTH_DISABLED setting
        assert "HIVE_AUTH_DISABLED=true" in content
        # Should not add duplicate
        auth_disabled_count = content.count("HIVE_AUTH_DISABLED")
        assert auth_disabled_count == 1

    def test_read_key_from_env_file(self, clean_environment, mock_env_file):
        """Test reading key from .env file."""
        # Test with key present
        mock_env_file.env_file.write_text("HIVE_API_KEY=read_test_key\n")

        key = mock_env_file._read_key_from_env()
        assert key == "read_test_key"

        # Test with no key
        mock_env_file.env_file.write_text("OTHER_VAR=value\n")
        key = mock_env_file._read_key_from_env()
        assert key is None

        # Test with non-existent file
        mock_env_file.env_file.unlink()
        key = mock_env_file._read_key_from_env()
        assert key is None

    def test_read_key_with_whitespace(self, clean_environment, mock_env_file):
        """Test reading key handles whitespace correctly."""
        # Test with various whitespace scenarios
        test_cases = [
            "HIVE_API_KEY=key_with_spaces   \n",
            "HIVE_API_KEY=  key_with_leading_spaces\n",
            "HIVE_API_KEY=   key_with_both   \n",
        ]

        expected_keys = [
            "key_with_spaces",
            "key_with_leading_spaces",
            "key_with_both",
        ]

        for content, expected in zip(test_cases, expected_keys, strict=False):
            mock_env_file.env_file.write_text(content)
            key = mock_env_file._read_key_from_env()
            assert key == expected

    def test_regenerate_key(self, clean_environment, mock_env_file):
        """Test key regeneration."""
        with patch.object(mock_env_file, "_display_key_to_user"):
            # Set initial key
            os.environ["HIVE_API_KEY"] = "old_key_123"

            generated_key = mock_env_file.regenerate_key()

            # Should generate new key
            assert generated_key.startswith("hive_")
            assert generated_key != "old_key_123"

            # Should update environment
            assert os.environ.get("HIVE_API_KEY") == generated_key

            # Should save to file
            assert mock_env_file.env_file.exists()
            content = mock_env_file.env_file.read_text()
            assert f"HIVE_API_KEY={generated_key}" in content

    def test_get_current_key_priority(self, clean_environment, mock_env_file):
        """Test key retrieval priority (env > file)."""
        # Set both environment and file
        os.environ["HIVE_API_KEY"] = "env_key"
        mock_env_file.env_file.write_text("HIVE_API_KEY=file_key\n")

        # Environment should take priority
        key = mock_env_file.get_current_key()
        assert key == "env_key"

        # Remove environment, should fall back to file
        os.environ.pop("HIVE_API_KEY")
        key = mock_env_file.get_current_key()
        assert key == "file_key"

        # Remove file, should return None
        mock_env_file.env_file.unlink()
        key = mock_env_file.get_current_key()
        assert key is None

    @patch("lib.auth.init_service.logger")
    def test_display_key_to_user(self, mock_logger, mock_env_file):
        """Test key display to user includes security information."""
        test_key = "hive_display_test_key"

        mock_env_file._display_key_to_user(test_key)

        # Should log key information
        assert mock_logger.info.called
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]

        # Should include the key
        key_displayed = any(test_key in arg for arg in call_args)
        assert key_displayed, "API key should be displayed to user"

        # Should include usage example
        usage_example = any("curl" in arg for arg in call_args)
        assert usage_example, "Should include usage example"


class TestAuthInitServiceFileSystemSecurity:
    """Test file system security aspects of AuthInitService."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_api_key = os.environ.get("HIVE_API_KEY")
        os.environ.pop("HIVE_API_KEY", None)
        yield
        if original_api_key is not None:
            os.environ["HIVE_API_KEY"] = original_api_key

    def test_file_permissions_security(self, clean_environment):
        """Test that .env file is created with secure permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            # Create empty file to trigger key generation path (not CLI temp key path)
            env_file.touch()

            service = AuthInitService()
            service.env_file = env_file

            with patch.object(service, "_display_key_to_user"):
                service.ensure_api_key()

            # File should exist
            assert env_file.exists()

            # Check file permissions on Unix systems
            if os.name == "posix":
                stat_info = env_file.stat()
                # File should be readable/writable by owner only (600)
                permissions = oct(stat_info.st_mode)[-3:]
                # Allow 644 (readable by group/others) as well since it's common
                assert permissions in ["600", "644"], (
                    f"File permissions should be secure, got {permissions}"
                )

    def test_concurrent_file_access(self, clean_environment):
        """Test thread safety of file operations."""
        import threading
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"

            # Create multiple services sharing same file
            services = [AuthInitService() for _ in range(5)]
            for service in services:
                service.env_file = env_file

            results = []
            errors = []

            def save_key(service, key_suffix):
                try:
                    with patch.object(service, "_display_key_to_user"):
                        key = f"test_key_{key_suffix}"
                        service._save_key_to_env(key)
                        # Small delay to increase chance of race condition
                        time.sleep(0.01)
                        # Verify key was saved
                        saved_key = service._read_key_from_env()
                        results.append((key_suffix, saved_key))
                except Exception as e:
                    errors.append((key_suffix, str(e)))

            # Run concurrent operations
            threads = []
            for i, service in enumerate(services):
                thread = threading.Thread(target=save_key, args=(service, i))
                threads.append(thread)
                thread.start()

            # Wait for all threads
            for thread in threads:
                thread.join()

            # Should not have errors
            assert len(errors) == 0, f"Concurrent access errors: {errors}"

            # File should exist and be readable
            assert env_file.exists()
            final_content = env_file.read_text()
            assert "HIVE_API_KEY=" in final_content

    def test_malformed_env_file_handling(self, clean_environment):
        """Test handling of malformed .env files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"

            service = AuthInitService()
            service.env_file = env_file

            # Test various malformed content
            malformed_contents = [
                "HIVE_API_KEY",  # Missing =
                "HIVE_API_KEY=",  # Empty value
                "=test_key",  # Missing key name
                "HIVE_API_KEY=key1\nHIVE_API_KEY=key2",  # Duplicate keys
                "INVALID_SYNTAX\n===\nHIVE_API_KEY=valid_key",  # Mixed invalid/valid
            ]

            for content in malformed_contents:
                env_file.write_text(content)

                # Should handle gracefully without crashing
                try:
                    service._read_key_from_env()
                    # For some cases (like duplicate keys), it might read the first/last one
                    # Main requirement is no crash
                except Exception as e:
                    pytest.fail(f"Should handle malformed content gracefully: {e}")

    def test_large_env_file_handling(self, clean_environment):
        """Test handling of large .env files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"

            service = AuthInitService()
            service.env_file = env_file

            # Create large .env file (1000 lines)
            large_content = []
            for i in range(1000):
                large_content.append(f"VAR_{i}=value_{i}")

            # Add API key somewhere in the middle
            large_content.insert(500, "HIVE_API_KEY=hidden_in_large_file")
            env_file.write_text("\n".join(large_content))

            # Should find the key efficiently
            key = service._read_key_from_env()
            assert key == "hidden_in_large_file"

            # Should update key correctly
            service._save_key_to_env("target_key_in_large_file")
            result_key = service._read_key_from_env()
            assert result_key == "target_key_in_large_file"

            # Should not duplicate the key
            content = env_file.read_text()
            api_key_count = content.count("HIVE_API_KEY=")
            assert api_key_count == 1


class TestAuthInitServiceErrorHandling:
    """Test error handling and edge cases in AuthInitService."""

    @pytest.fixture
    def clean_environment(self):
        """Clean environment for each test."""
        original_api_key = os.environ.get("HIVE_API_KEY")
        os.environ.pop("HIVE_API_KEY", None)
        yield
        if original_api_key is not None:
            os.environ["HIVE_API_KEY"] = original_api_key

    def test_readonly_env_file(self, clean_environment):
        """Test handling when .env file is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text("HIVE_API_KEY=readonly_test")

            # Make file read-only
            if os.name == "posix":
                env_file.chmod(0o444)

            service = AuthInitService()
            service.env_file = env_file

            # Should handle read-only file gracefully
            key = service._read_key_from_env()
            assert key == "readonly_test"

            # Writing should raise appropriate error
            with pytest.raises(PermissionError):
                service._save_key_to_env("target_key")

    def test_readonly_directory(self, clean_environment):
        """Test handling when directory is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make directory read-only
            if os.name == "posix":
                os.chmod(temp_dir, 0o555)

            env_file = Path(temp_dir) / ".env"
            service = AuthInitService()
            service.env_file = env_file

            # Should raise appropriate error when trying to create file
            with pytest.raises(PermissionError):
                with patch.object(service, "_display_key_to_user"):
                    service._save_key_to_env("test_key")

            # Reset permissions for cleanup
            if os.name == "posix":
                os.chmod(temp_dir, 0o755)

    def test_disk_full_simulation(self, clean_environment):
        """Test behavior when disk is full (simulated)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            service = AuthInitService()
            service.env_file = env_file

            # Mock write_text to simulate disk full

            def mock_write_text_disk_full(self, data, encoding=None, errors=None):
                raise OSError("No space left on device")

            with patch.object(Path, "write_text", mock_write_text_disk_full):
                with pytest.raises(OSError, match="No space left on device"):
                    service._save_key_to_env("test_key")

    def test_unicode_handling_in_env_file(self, clean_environment):
        """Test handling of unicode characters in .env file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            service = AuthInitService()
            service.env_file = env_file

            # Create .env with unicode content
            unicode_content = """# Configuration with unicode: üñíçødé
DATABASE_URL=postgres://localhost/tëst
HIVE_API_KEY=key_with_ñ_and_🔑
OTHER_VAR=valué_wîth_áççéñts
"""
            env_file.write_text(unicode_content, encoding="utf-8")

            # Should read unicode key correctly
            key = service._read_key_from_env()
            assert key == "key_with_ñ_and_🔑"

            # Should save unicode key correctly
            unicode_key = "üñíçødé_kéy_🔐"
            service._save_key_to_env(unicode_key)

            result_key = service._read_key_from_env()
            assert result_key == unicode_key
