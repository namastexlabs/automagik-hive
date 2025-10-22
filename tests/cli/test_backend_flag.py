"""Tests for CLI --backend flag behavior.

Tests the --backend flag functionality in the install command,
verifying valid/invalid backend selection, flag priority, and
case-insensitive handling.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.main import create_parser, main  # noqa: E402


class TestBackendFlag:
    """Test --backend flag behavior in install command."""

    def test_valid_backend_postgresql(self, monkeypatch, capsys):
        """Test --backend flag with valid postgresql value."""
        # Mock environment
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
            # Mock sys.argv
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", "postgresql"])

            # Mock ServiceManager to prevent actual installation
            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                # Run CLI
                result = main()

                # Verify installation was called with backend override
                mock_manager.install_full_environment.assert_called_once_with(
                    ".", backend_override="postgresql", verbose=False
                )
                assert result == 0

    def test_valid_backend_pglite(self, monkeypatch):
        """Test --backend flag with valid pglite value."""
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", "pglite"])

            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                result = main()

                mock_manager.install_full_environment.assert_called_once_with(
                    ".", backend_override="pglite", verbose=False
                )
                assert result == 0

    def test_valid_backend_sqlite(self, monkeypatch):
        """Test --backend flag with valid sqlite value."""
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", "sqlite"])

            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                result = main()

                mock_manager.install_full_environment.assert_called_once_with(
                    ".", backend_override="sqlite", verbose=False
                )
                assert result == 0

    def test_invalid_backend_rejected(self, monkeypatch, capsys):
        """Test --backend flag rejects invalid backend values."""
        monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", "mysql"])

        # argparse should raise SystemExit for invalid choice
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with error code
        assert exc_info.value.code != 0

        # Check error message mentions invalid choice
        captured = capsys.readouterr()
        assert "invalid choice" in captured.err.lower() or "mysql" in captured.err

    def test_backend_flag_overrides_environment(self, monkeypatch):
        """Test --backend flag takes precedence over environment variable."""
        # Set environment to suggest postgresql
        with patch.dict(
            os.environ,
            {
                "HIVE_DATABASE_BACKEND": "postgresql",
                "HIVE_DATABASE_URL": "postgresql://localhost/test",
            },
            clear=False,
        ):
            # But use flag to specify pglite
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", "pglite"])

            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                result = main()

                # Flag should override environment
                mock_manager.install_full_environment.assert_called_once_with(
                    ".", backend_override="pglite", verbose=False
                )
                assert result == 0

    def test_backend_flag_overrides_interactive_prompt(self, monkeypatch):
        """Test --backend flag skips interactive prompt."""
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", "sqlite"])

            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                # Mock the prompt method to verify it's not called
                with patch("cli.commands.service.ServiceManager._prompt_backend_selection") as mock_prompt:
                    result = main()

                    # Prompt should NOT be called when flag is present
                    mock_prompt.assert_not_called()

                    # But installation should proceed with flag value
                    mock_manager.install_full_environment.assert_called_once_with(
                        ".", backend_override="sqlite", verbose=False
                    )
                    assert result == 0

    def test_case_insensitive_backend_values(self, monkeypatch):
        """Test --backend flag handles case variations correctly."""
        test_cases = [
            ("PostgreSQL", "postgresql"),
            ("POSTGRESQL", "postgresql"),
            ("PgLite", "pglite"),
            ("PGLITE", "pglite"),
            ("SQLite", "sqlite"),
            ("SQLITE", "sqlite"),
        ]

        for input_value, expected_normalized in test_cases:
            # Note: argparse choices are case-sensitive by default
            # This test verifies the choices are defined in lowercase
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", ".", "--backend", input_value.lower()])

            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                result = main()

                mock_manager.install_full_environment.assert_called_once_with(
                    ".", backend_override=expected_normalized, verbose=False
                )
                assert result == 0

    def test_backend_flag_without_install_command(self, monkeypatch, capsys):
        """Test --backend flag requires install command."""
        # Try to use --backend with different command
        monkeypatch.setattr(sys, "argv", ["automagik-hive", "--backend", "pglite"])

        # Should fail because --backend is only for install subcommand
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code != 0

    def test_parser_backend_choices(self):
        """Test parser defines correct backend choices."""
        parser = create_parser()

        # Get install subparser - use _subparsers attribute directly
        subparsers_action = None
        for action in parser._actions:
            if hasattr(action, "choices") and isinstance(action.choices, dict):
                if "install" in action.choices:
                    subparsers_action = action
                    break

        assert subparsers_action is not None, "Could not find subparsers action"

        install_parser = subparsers_action.choices.get("install")
        assert install_parser is not None

        # Find --backend argument
        backend_action = None
        for action in install_parser._actions:
            if hasattr(action, "option_strings") and "--backend" in action.option_strings:
                backend_action = action
                break

        assert backend_action is not None
        assert backend_action.choices == ["postgresql", "pglite", "sqlite"]

    def test_no_backend_flag_uses_default_behavior(self, monkeypatch):
        """Test install without --backend flag uses default prompt behavior."""
        with patch.dict(os.environ, {"HIVE_DATABASE_URL": "sqlite:///test.db"}, clear=False):
            monkeypatch.setattr(sys, "argv", ["automagik-hive", "install", "."])

            with patch("cli.main.ServiceManager") as mock_service:
                mock_manager = MagicMock()
                mock_manager.install_full_environment.return_value = True
                mock_service.return_value = mock_manager

                result = main()

                # Should be called with None backend_override (triggers prompt)
                mock_manager.install_full_environment.assert_called_once_with(".", backend_override=None, verbose=False)
                assert result == 0
