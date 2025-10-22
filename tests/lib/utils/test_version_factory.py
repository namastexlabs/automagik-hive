"""Tests for lib.utils.version_factory module.

Tests the simplified version factory with inheritance system removed.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from lib.utils.user_context_helper import create_user_context_state
from lib.utils.version_factory import VersionFactory


class TestVersionFactory:
    """Test VersionFactory simplified implementation."""

    def test_init(self):
        """Test VersionFactory initialization."""
        factory = VersionFactory()
        assert factory is not None

    @patch("lib.utils.version_factory.logger")
    def test_apply_team_inheritance_passthrough(self, mock_logger):
        """Test team inheritance returns config unchanged."""
        factory = VersionFactory()
        config = {"name": "test", "version": "1.0.0"}

        result = factory._apply_team_inheritance("test-agent", config)

        assert result == config
        mock_logger.debug.assert_called_once()

    @patch("lib.utils.version_factory.logger")
    def test_validate_team_inheritance_disabled(self, mock_logger):
        """Test team inheritance validation is disabled."""
        factory = VersionFactory()
        config = {"name": "test", "version": "1.0.0"}

        result = factory._validate_team_inheritance("test-team", config)

        # Should return config unchanged (validation disabled)
        assert result == config
        mock_logger.debug.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_uses_session_state(self):
        """VersionFactory should provide session_state instead of legacy context."""
        factory = VersionFactory()

        dummy_agent = SimpleNamespace(metadata={}, session_state=None)

        async def _create_agent_side_effect(*args, **kwargs):
            config = kwargs["config"]
            dummy_agent.session_state = config.get("session_state")
            dummy_agent.passed_config = config
            return dummy_agent

        with (
            patch("lib.utils.agno_proxy.get_agno_proxy") as mock_get_proxy,
            patch.object(factory, "_apply_team_inheritance", side_effect=lambda cid, cfg: cfg),
            patch.object(factory, "_load_agent_tools", return_value=[]),
        ):
            mock_proxy = Mock()
            mock_proxy.create_agent = AsyncMock(side_effect=_create_agent_side_effect)
            mock_proxy.get_supported_parameters.return_value = set()
            mock_get_proxy.return_value = mock_proxy

            agent = await factory._create_agent(
                component_id="template-agent",
                config={"agent": {"name": "Template"}},
                session_id="session-1",
                debug_mode=False,
                user_id="user-123",
                metrics_service=None,
                user_name="Test User",
                phone_number="+551199999999",
            )

        expected_state = create_user_context_state(
            user_id="user-123",
            user_name="Test User",
            phone_number="+551199999999",
        )

        assert agent.session_state == expected_state

        passed_config = mock_proxy.create_agent.call_args.kwargs["config"]
        assert "context" not in passed_config
        assert passed_config.get("session_state") == expected_state
        assert agent.metadata.get("runtime_context_keys") == sorted(expected_state["user_context"].keys())
