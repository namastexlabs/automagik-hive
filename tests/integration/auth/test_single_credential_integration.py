#!/usr/bin/env python3
"""Integration tests for single credential source implementation."""

from lib.auth.credential_service import CredentialService


class TestSingleCredentialIntegration:
    """Integration coverage for master env orchestration flows."""

    def test_fresh_install_creates_primary_and_master_alias(self, tmp_path):
        """Fresh installs should hydrate .env and its master alias consistently."""
        service = CredentialService(project_root=tmp_path)

        result = service.install_all_modes(force_regenerate=True)

        workspace_creds = result["workspace"]
        assert workspace_creds["postgres_user"]
        assert workspace_creds["postgres_password"]
        assert workspace_creds["api_key"].startswith("hive_")

        primary_env = tmp_path / ".env"
        master_alias = tmp_path / ".env.master"

        assert primary_env.exists(), "Expected primary .env to be created"
        assert master_alias.exists(), "Expected master env alias to be created"
        assert master_alias.read_text() == primary_env.read_text()

    def test_rerun_reuses_existing_credentials_from_master_alias(self, tmp_path):
        """Re-running without force should reuse credentials even when only alias exists."""
        service = CredentialService(project_root=tmp_path)
        first_run = service.install_all_modes(force_regenerate=True)["workspace"]

        primary_env = tmp_path / ".env"
        master_alias = tmp_path / ".env.master"
        assert primary_env.exists()
        assert master_alias.exists()

        # Simulate legacy layout where the alias is the canonical master env
        master_alias.write_text(primary_env.read_text())
        primary_env.unlink()

        rerun_service = CredentialService(project_root=tmp_path)
        reused_creds = rerun_service.install_all_modes(force_regenerate=False)["workspace"]

        assert reused_creds["postgres_user"] == first_run["postgres_user"]
        assert reused_creds["postgres_password"] == first_run["postgres_password"]
        assert reused_creds["api_key"] == first_run["api_key"]

    def test_force_regenerate_replaces_credentials_when_alias_only(self, tmp_path):
        """Force regenerate should issue new secrets and refresh both env files."""
        service = CredentialService(project_root=tmp_path)
        baseline = service.install_all_modes(force_regenerate=True)["workspace"]

        primary_env = tmp_path / ".env"
        master_alias = tmp_path / ".env.master"
        assert primary_env.exists()
        assert master_alias.exists()

        canonical_contents = primary_env.read_text()
        master_alias.write_text(canonical_contents)
        primary_env.unlink()

        regen_service = CredentialService(project_root=tmp_path)
        regenerated = regen_service.install_all_modes(force_regenerate=True)["workspace"]

        assert regenerated["postgres_user"] != baseline["postgres_user"]
        assert regenerated["postgres_password"] != baseline["postgres_password"]
        assert regenerated["api_key"] != baseline["api_key"]

        refreshed_env = tmp_path / ".env"
        assert refreshed_env.exists(), "Force regenerate should recreate primary env"
        assert master_alias.exists(), "Master alias should persist after regeneration"
        assert master_alias.read_text() == refreshed_env.read_text()
