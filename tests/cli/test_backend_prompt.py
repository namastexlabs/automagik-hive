"""Tests for CLI interactive backend selection prompt.

Tests the _prompt_backend_selection() method behavior including
prompt display, user input validation, default selection, and
environment file updates.
"""

import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.commands.service import ServiceManager  # noqa: E402


class TestBackendPrompt:
    """Test interactive backend selection prompt."""

    def test_prompt_displays_all_three_options(self, capsys):
        """Test prompt displays PostgreSQL, PGlite, and SQLite options."""
        service_manager = ServiceManager()

        # Mock input to select default
        with patch("builtins.input", return_value=""):
            _ = service_manager._prompt_backend_selection()  # Result intentionally unused

        # Capture output
        captured = capsys.readouterr()

        # Verify all three options are displayed
        assert "PostgreSQL" in captured.out
        assert "PGlite" in captured.out
        assert "SQLite" in captured.out

        # Verify option descriptions
        assert "Docker" in captured.out
        assert "WebAssembly" in captured.out
        assert "file-based" in captured.out

    def test_default_selection_pglite(self):
        """Test default selection is PGlite when user presses Enter."""
        service_manager = ServiceManager()

        # Empty input = default = PGlite
        with patch("builtins.input", return_value=""):
            backend = service_manager._prompt_backend_selection()

        assert backend == "pglite"

    def test_explicit_selection_pglite(self):
        """Test explicit selection of PGlite (option B)."""
        service_manager = ServiceManager()

        with patch("builtins.input", return_value="B"):
            backend = service_manager._prompt_backend_selection()

        assert backend == "pglite"

    def test_explicit_selection_postgresql(self):
        """Test explicit selection of PostgreSQL (option A)."""
        service_manager = ServiceManager()

        with patch("builtins.input", return_value="A"):
            backend = service_manager._prompt_backend_selection()

        assert backend == "postgresql"

    def test_explicit_selection_sqlite(self):
        """Test explicit selection of SQLite (option C)."""
        service_manager = ServiceManager()

        with patch("builtins.input", return_value="C"):
            backend = service_manager._prompt_backend_selection()

        assert backend == "sqlite"

    def test_lowercase_input_accepted(self):
        """Test lowercase input is accepted."""
        service_manager = ServiceManager()

        test_cases = [
            ("a", "postgresql"),
            ("b", "pglite"),
            ("c", "sqlite"),
        ]

        for input_val, expected_backend in test_cases:
            with patch("builtins.input", return_value=input_val):
                backend = service_manager._prompt_backend_selection()
                assert backend == expected_backend

    def test_invalid_input_reprompts(self, capsys):
        """Test invalid input causes reprompt."""
        service_manager = ServiceManager()

        # First invalid, then valid
        inputs = ["X", "B"]
        input_iter = iter(inputs)

        with patch("builtins.input", side_effect=lambda _: next(input_iter)):
            backend = service_manager._prompt_backend_selection()

        assert backend == "pglite"

        # Verify error message was shown
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out or "❌" in captured.out

    def test_multiple_invalid_inputs(self):
        """Test multiple invalid inputs before valid selection."""
        service_manager = ServiceManager()

        # Multiple invalid inputs, then valid
        inputs = ["D", "1", "yes", "A"]
        input_iter = iter(inputs)

        with patch("builtins.input", side_effect=lambda _: next(input_iter)):
            backend = service_manager._prompt_backend_selection()

        assert backend == "postgresql"

    def test_keyboard_interrupt_returns_default(self):
        """Test Ctrl+C during prompt returns default (PGlite)."""
        service_manager = ServiceManager()

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            backend = service_manager._prompt_backend_selection()

        # Should return default for automated scenarios
        assert backend == "pglite"

    def test_eof_error_returns_default(self):
        """Test EOF during prompt returns default (PGlite)."""
        service_manager = ServiceManager()

        with patch("builtins.input", side_effect=EOFError):
            backend = service_manager._prompt_backend_selection()

        # Should return default for automated scenarios
        assert backend == "pglite"

    def test_prompt_not_called_when_backend_flag_provided(self, monkeypatch):
        """Test prompt is skipped when --backend flag is present."""
        # This is tested via integration - the install flow should skip prompt
        # when backend_override is provided
        service_manager = ServiceManager()

        with patch("cli.commands.service.ServiceManager._prompt_backend_selection") as mock_prompt:
            # When backend_override is provided, prompt should not be called
            with patch.object(service_manager, "main_service") as mock_main:
                mock_main.install_main_environment.return_value = True
                with patch.object(service_manager, "_store_backend_choice"):
                    with patch.object(service_manager, "_resolve_install_root", return_value=Path(".")):
                        with patch("lib.auth.credential_service.CredentialService"):
                            # Call install with backend override
                            service_manager.install_full_environment(".", backend_override="pglite")

            # Prompt should never be called
            mock_prompt.assert_not_called()

    def test_prompt_called_when_no_backend_flag(self):
        """Test prompt is called when no --backend flag is provided."""
        service_manager = ServiceManager()

        with patch.object(service_manager, "_prompt_backend_selection", return_value="pglite") as mock_prompt:
            with patch.object(service_manager, "main_service") as mock_main:
                mock_main.install_main_environment.return_value = True
                with patch.object(service_manager, "_store_backend_choice"):
                    with patch.object(service_manager, "_resolve_install_root", return_value=Path(".")):
                        with patch("lib.auth.credential_service.CredentialService"):
                            with patch.object(service_manager, "_prompt_deployment_choice", return_value="full_docker"):
                                # Call install without backend override
                                service_manager.install_full_environment(".", backend_override=None)

            # Prompt should be called
            mock_prompt.assert_called_once()

    def test_store_backend_choice_updates_env_file(self, tmp_path):
        """Test _store_backend_choice updates .env file correctly."""
        service_manager = ServiceManager()

        # Create temporary .env file
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=your_database_url_here\n")

        # Store backend choice
        service_manager._store_backend_choice(tmp_path, "pglite")

        # Read updated .env
        env_content = env_file.read_text()

        # Verify backend was added
        assert "HIVE_DATABASE_BACKEND=pglite" in env_content

        # Verify URL was updated
        assert "pglite://" in env_content

    def test_store_backend_choice_preserves_existing_content(self, tmp_path):
        """Test _store_backend_choice preserves other .env content."""
        service_manager = ServiceManager()

        # Create .env with existing content
        env_file = tmp_path / ".env"
        original_content = """# Existing content
HIVE_API_KEY=test_key
HIVE_DATABASE_URL=your_database_url_here
OTHER_VAR=value
"""
        env_file.write_text(original_content)

        # Store backend choice
        service_manager._store_backend_choice(tmp_path, "sqlite")

        # Read updated .env
        env_content = env_file.read_text()

        # Verify existing content preserved
        assert "HIVE_API_KEY=test_key" in env_content
        assert "OTHER_VAR=value" in env_content

        # Verify backend was added
        assert "HIVE_DATABASE_BACKEND=sqlite" in env_content
        assert "sqlite://" in env_content

    def test_store_backend_choice_postgresql_url(self, tmp_path):
        """Test PostgreSQL backend generates correct URL."""
        service_manager = ServiceManager()

        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_DATABASE_URL=your_database_url_here\n")

        service_manager._store_backend_choice(tmp_path, "postgresql")

        env_content = env_file.read_text()

        # Verify PostgreSQL URL format
        assert "postgresql+psycopg://" in env_content
        assert "localhost" in env_content

    def test_store_backend_choice_no_env_file(self, tmp_path):
        """Test _store_backend_choice handles missing .env file gracefully."""
        service_manager = ServiceManager()

        # Call with non-existent .env file
        service_manager._store_backend_choice(tmp_path, "pglite")

        # Should not crash, just return silently
        # (actual .env creation is handled by install flow)

    def test_prompt_header_formatting(self, capsys):
        """Test prompt displays formatted header."""
        service_manager = ServiceManager()

        with patch("builtins.input", return_value=""):
            service_manager._prompt_backend_selection()

        captured = capsys.readouterr()

        # Verify header formatting
        assert "DATABASE BACKEND SELECTION" in captured.out
        assert "=" in captured.out  # Header separator

    def test_prompt_shows_recommendations(self, capsys):
        """Test prompt shows recommendations for each backend."""
        service_manager = ServiceManager()

        with patch("builtins.input", return_value=""):
            service_manager._prompt_backend_selection()

        captured = capsys.readouterr()

        # Verify recommendations
        assert "production" in captured.out.lower()
        assert "development" in captured.out.lower() or "testing" in captured.out.lower()

    def test_backend_choice_values_are_lowercase(self):
        """Test all backend return values are lowercase."""
        service_manager = ServiceManager()

        inputs = ["A", "B", "C", "a", "b", "c", ""]
        expected = ["postgresql", "pglite", "sqlite", "postgresql", "pglite", "sqlite", "pglite"]

        for input_val, expected_backend in zip(inputs, expected, strict=False):
            with patch("builtins.input", return_value=input_val):
                backend = service_manager._prompt_backend_selection()
                assert backend == expected_backend
                assert backend.islower()
