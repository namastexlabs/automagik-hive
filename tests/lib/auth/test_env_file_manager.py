"""
Focused unit tests for EnvFileManager covering:
- Alias-first reads and synchronization
- Template fallback hydration when .env is missing
- Base port extraction from env values
- Error handling paths for read/update
"""

from pathlib import Path

import pytest

from lib.auth.env_file_manager import EnvFileManager


class TestEnvFileResolution:
    def test_master_env_path_prefers_alias(self, tmp_path: Path):
        tmp_path / ".env"
        alias = tmp_path / ".env.master"

        # Only alias exists
        alias.write_text("HIVE_API_KEY=hive_alias\n")

        mgr = EnvFileManager(project_root=tmp_path)
        assert mgr.master_env_path == alias

        # read_master_lines should read from alias
        lines = mgr.read_master_lines()
        assert any(line.startswith("HIVE_API_KEY=") for line in lines)

    def test_refresh_primary_hydrates_from_alias(self, tmp_path: Path):
        primary = tmp_path / ".env"
        alias = tmp_path / ".env.master"
        alias_content = "HIVE_API_KEY=hive_from_alias\n"
        alias.write_text(alias_content)

        mgr = EnvFileManager(project_root=tmp_path)
        out = mgr.refresh_primary(create_if_missing=True)
        assert out == primary
        assert primary.exists()
        assert primary.read_text() == alias_content

    def test_refresh_primary_uses_template_then_syncs_alias(self, tmp_path: Path):
        primary = tmp_path / ".env"
        alias = tmp_path / ".env.master"

        # Provide .env.example template content
        example = tmp_path / ".env.example"
        example.write_text("HIVE_API_PORT=7777\n")

        mgr = EnvFileManager(project_root=tmp_path)
        out = mgr.refresh_primary(create_if_missing=True)
        assert out == primary
        # Hydrated from template
        assert "HIVE_API_PORT=7777" in primary.read_text()
        # Alias synced
        assert alias.exists()
        assert alias.read_text() == primary.read_text()


class TestTemplateFallback:
    def test_default_template_used_when_example_missing(self, tmp_path: Path):
        primary = tmp_path / ".env"
        alias = tmp_path / ".env.master"

        mgr = EnvFileManager(project_root=tmp_path)
        out = mgr.refresh_primary(create_if_missing=True)
        assert out == primary
        content = primary.read_text()
        # Heuristic: a known line from DEFAULT_ENV_TEMPLATE
        assert "HIVE_API_WORKERS=1" in content
        # Alias synced
        assert alias.exists()
        assert alias.read_text() == content


class TestValueUpdates:
    def test_update_values_creates_when_enabled(self, tmp_path: Path):
        mgr = EnvFileManager(project_root=tmp_path)
        ok = mgr.update_values({"HIVE_API_KEY": "hive_abc"}, create_if_missing=True)
        assert ok is True
        assert (tmp_path / ".env").exists()
        # Alias is synced too
        assert (tmp_path / ".env.master").exists()

        lines = (tmp_path / ".env").read_text().splitlines()
        assert any(line == "HIVE_API_KEY=hive_abc" for line in lines)

    def test_update_values_fails_when_create_disabled(self, tmp_path: Path):
        mgr = EnvFileManager(project_root=tmp_path)
        ok = mgr.update_values({"HIVE_API_KEY": "hive_abc"}, create_if_missing=False)
        assert ok is False
        assert not (tmp_path / ".env").exists()


class TestExtractionHelpers:
    def test_extract_base_ports_overrides_defaults(self, tmp_path: Path):
        # Prepare env with db and api ports
        (tmp_path / ".env").write_text(
            "\n".join(
                [
                    "# comment",
                    "HIVE_DATABASE_URL=postgresql+psycopg://u:p@localhost:5777/hive",
                    "HIVE_API_PORT=9999",
                ]
            )
            + "\n"
        )

        mgr = EnvFileManager(project_root=tmp_path)
        defaults = {"db": 5532, "api": 8886}
        ports = mgr.extract_base_ports(defaults, "HIVE_DATABASE_URL", "HIVE_API_PORT")
        assert ports["db"] == 5777
        assert ports["api"] == 9999

    def test_extract_base_ports_uses_defaults_when_missing(self, tmp_path: Path):
        # No env file present
        mgr = EnvFileManager(project_root=tmp_path)
        defaults = {"db": 5532, "api": 8886}
        ports = mgr.extract_base_ports(defaults, "HIVE_DATABASE_URL", "HIVE_API_PORT")
        assert ports == defaults

    def test_extract_postgres_credentials_and_api_key(self, tmp_path: Path):
        (tmp_path / ".env").write_text(
            "\n".join(
                [
                    "HIVE_DATABASE_URL=postgresql+psycopg://user:pass@localhost:6000/hive",
                    "HIVE_API_KEY=hive_k",
                ]
            )
            + "\n"
        )
        mgr = EnvFileManager(project_root=tmp_path)
        creds = mgr.extract_postgres_credentials("HIVE_DATABASE_URL")
        assert creds["user"] == "user"
        assert creds["password"] == "pass"  # noqa: S105 - Test fixture password
        assert creds["port"] == "6000"
        assert creds["database"] == "hive"

        api = mgr.extract_api_key("HIVE_API_KEY")
        assert api == "hive_k"


class TestErrorHandling:
    def test_read_master_lines_ioerror_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Create an env path, but force read_text to raise for this test
        env_file = tmp_path / ".env"
        env_file.write_text("HIVE_API_KEY=k\n")
        mgr = EnvFileManager(project_root=tmp_path)

        def boom(self):  # type: ignore[no-redef]
            raise OSError("boom")

        monkeypatch.setattr(Path, "read_text", boom)
        assert mgr.read_master_lines() == []

    def test_sync_alias_ioerror_is_logged_not_raised(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Force write failure during sync
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\n")
        mgr = EnvFileManager(project_root=tmp_path)

        def fail_write(self, content: str):  # type: ignore[no-redef]
            raise OSError("nope")

        # Patch Path.write_text to fail
        monkeypatch.setattr(Path, "write_text", fail_write)

        # Should not raise
        mgr.sync_alias()
