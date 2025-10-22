"""Tests for lib.utils.agno_storage_utils."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from lib.utils.agno_storage_utils import (
    create_dynamic_storage,
    get_storage_class,
    get_storage_type_mapping,
    get_supported_storage_types,
    validate_storage_config,
)


class TestTypeMappings:
    """Validate DB type mapping helpers."""

    def test_get_storage_type_mapping_returns_expected_classes(self) -> None:
        mapping = get_storage_type_mapping()

        assert mapping["postgres"] == "agno.db.postgres.PostgresDb"
        assert mapping["sqlite"] == "agno.db.sqlite.SqliteDb"
        assert mapping["mongodb"] == "agno.db.mongo.MongoDb"
        assert mapping["redis"] == "agno.db.redis.RedisDb"
        assert mapping["dynamodb"] == "agno.db.dynamo.DynamoDb"
        assert mapping["json"] == "agno.db.json.JsonDb"
        assert mapping["yaml"] == "agno.db.yaml.YamlDb"
        assert mapping["singlestore"] == "agno.db.singlestore.SingleStoreDb"

    def test_supported_storage_types_matches_mapping(self) -> None:
        mapping = get_storage_type_mapping()
        supported_types = get_supported_storage_types()

        assert isinstance(supported_types, list)
        assert set(supported_types) == set(mapping.keys())


class TestGetStorageClass:
    """Dynamic class resolution should surface helpful errors."""

    @patch("importlib.import_module")
    def test_successful_import(self, mock_import_module: Mock) -> None:
        mock_module = Mock()
        mock_module.PostgresDb = Mock()
        mock_import_module.return_value = mock_module

        resolved = get_storage_class("postgres")

        assert resolved is mock_module.PostgresDb
        mock_import_module.assert_called_once_with("agno.db.postgres")

    def test_unsupported_type(self) -> None:
        with pytest.raises(ValueError, match="Unsupported storage type: unknown"):
            get_storage_class("unknown")

    @patch("importlib.import_module", side_effect=ImportError("boom"))
    def test_import_failure(self, _: Mock) -> None:
        with pytest.raises(ImportError, match="Failed to import postgres storage class"):
            get_storage_class("postgres")


class TestCreateDynamicStorage:
    """Ensure helper returns db + dependencies bundle."""

    @patch("lib.utils.agno_storage_utils.get_storage_class")
    @patch("inspect.signature")
    def test_returns_db_and_dependencies(self, mock_signature: Mock, mock_get_class: Mock) -> None:
        mock_db = Mock(name="PostgresDb")
        mock_instance = Mock()
        mock_db.return_value = mock_instance
        mock_get_class.return_value = mock_db

        param = Mock()
        mock_signature.return_value.parameters = {
            "self": param,
            "db_url": param,
            "session_table": param,
            "memory_table": param,
            "metrics_table": param,
            "eval_table": param,
            "knowledge_table": param,
            "db_schema": param,
            "id": param,
        }

        config = {
            "type": "postgres",
            "db_url": "postgresql://localhost/hive",
            "table_name": "template_agent",
            "schema": "agno",
        }

        result = create_dynamic_storage(
            storage_config=config,
            component_id="template-agent",
            component_mode="agent",
            db_url="postgresql://localhost/hive",
        )

        assert result["db"] is mock_instance
        assert result["dependencies"]["db"] is mock_instance
        mock_db.assert_called_once_with(
            db_url="postgresql://localhost/hive",
            session_table="template_agent",
            memory_table="template_agent_memories",
            metrics_table="template_agent_metrics",
            eval_table="template_agent_evals",
            knowledge_table="template_agent_knowledge",
            db_schema="agno",
            id="agent-template-agent",
        )

    @patch("lib.utils.agno_storage_utils.get_storage_class")
    @patch("inspect.signature")
    def test_uses_fallback_defaults(self, mock_signature: Mock, mock_get_class: Mock) -> None:
        mock_db = Mock()
        mock_instance = Mock()
        mock_db.return_value = mock_instance
        mock_get_class.return_value = mock_db

        param = Mock()
        mock_signature.return_value.parameters = {"self": param, "db_url": param, "session_table": param}

        result = create_dynamic_storage(
            storage_config={"type": "sqlite"},
            component_id="demo",
            component_mode="workflow",
            db_url="sqlite:///tmp.db",
        )

        assert result["db"] is mock_instance
        assert result["dependencies"]["db"] is mock_instance
        mock_db.assert_called_once_with(
            db_url="sqlite:///tmp.db",
            session_table="workflow_demo_sessions",
        )

    @patch("lib.utils.agno_storage_utils.get_storage_class")
    @patch("inspect.signature", side_effect=Exception("bad signature"))
    def test_signature_failure_surfaces_error(self, mock_get_class: Mock, _: Mock) -> None:
        mock_get_class.return_value = Mock()

        with pytest.raises(Exception, match="Failed to introspect postgres storage constructor"):
            create_dynamic_storage(
                storage_config={"type": "postgres"},
                component_id="broken",
                component_mode="agent",
                db_url="postgresql://localhost/hive",
            )

    @patch("lib.utils.agno_storage_utils.get_storage_class", side_effect=ValueError("bad"))
    def test_invalid_storage_type_bubbles_error(self, _: Mock) -> None:
        with pytest.raises(ValueError, match="bad"):
            create_dynamic_storage(
                storage_config={"type": "invalid"},
                component_id="demo",
                component_mode="agent",
                db_url="postgresql://localhost/hive",
            )


class TestValidateStorageConfig:
    """Basic validation helpers should reflect db terminology."""

    def test_validate_storage_config_success(self) -> None:
        result = validate_storage_config({"type": "postgres"})

        assert result == {
            "storage_type": "postgres",
            "is_supported": True,
            "supported_types": get_supported_storage_types(),
            "config_keys": ["type"],
        }

    def test_validate_storage_config_failure(self) -> None:
        result = validate_storage_config({"type": "custom"})

        assert result["is_supported"] is False
        assert result["error"].startswith("Unsupported storage type: custom")
