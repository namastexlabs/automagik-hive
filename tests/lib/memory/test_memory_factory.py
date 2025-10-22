"""Tests for the memory factory helpers."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from lib.exceptions import MemoryFactoryError
from lib.memory.memory_factory import create_agent_memory, create_memory_instance


class TestMemoryFactory:
    """Validate MemoryManager creation flows."""

    @patch("lib.memory.memory_factory.resolve_model")
    def test_create_agent_memory_reuses_shared_db(self, mock_resolve_model: MagicMock) -> None:
        mock_model = MagicMock()
        mock_resolve_model.return_value = mock_model
        shared_db = MagicMock(name="shared_db")

        manager = create_agent_memory("alpha", db=shared_db)

        assert manager.db is shared_db
        mock_resolve_model.assert_called_once()

    @patch("lib.memory.memory_factory._build_memory_db")
    @patch("lib.memory.memory_factory.resolve_model")
    def test_create_agent_memory_builds_db_when_missing(
        self,
        mock_resolve_model: MagicMock,
        mock_build_db: MagicMock,
    ) -> None:
        mock_db = MagicMock(name="db_instance")
        mock_build_db.return_value = mock_db
        mock_resolve_model.return_value = MagicMock()

        manager = create_agent_memory("beta", db_url="postgresql://localhost/hive")

        mock_build_db.assert_called_once()
        assert manager.db is mock_db

    @patch("lib.memory.memory_factory.resolve_model")
    def test_create_memory_instance_requires_db_url_when_not_provided(self, mock_resolve_model: MagicMock) -> None:
        mock_resolve_model.return_value = MagicMock()

        with patch.dict(os.environ, {"HIVE_DATABASE_URL": ""}):
            with pytest.raises(MemoryFactoryError):
                create_memory_instance("demo", db_url=None, db=None)
