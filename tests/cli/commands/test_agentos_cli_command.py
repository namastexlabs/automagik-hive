"""CLI tests for the AgentOS config inspection command."""

from __future__ import annotations

import json
import sys

import pytest

from cli.main import main


class TestAgentOSCLICommand:
    """Validate behaviour of the feature-flagged AgentOS CLI command."""

    def test_agentos_cli_requires_feature_flag(self, capsys, monkeypatch):
        """Command should refuse execution when feature flag is disabled."""
        monkeypatch.delenv("HIVE_FEATURE_AGENTOS_CLI", raising=False)
        monkeypatch.setattr(sys, "argv", ["automagik-hive", "agentos-config"])

        exit_code = main()
        output = capsys.readouterr().out.lower()

        assert exit_code == 1
        assert "agentos" in output
        assert "enable" in output

    @pytest.mark.usefixtures("mock_auth_service")
    def test_agentos_cli_outputs_json_snapshot(self, capsys, monkeypatch):
        """Command should print config JSON when feature flag enabled."""
        monkeypatch.setenv("HIVE_FEATURE_AGENTOS_CLI", "1")
        monkeypatch.setattr(sys, "argv", ["automagik-hive", "agentos-config", "--json"])

        exit_code = main()
        output = capsys.readouterr().out

        assert exit_code == 0

        payload = json.loads(output)
        assert payload["os_id"] == "automagik-hive"
        assert "hive_sessions" in payload["databases"]
