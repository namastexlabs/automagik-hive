"""
Unit tests for the Agent Versioning System.

Tests the database service, version factory, and API endpoints
for the agent versioning functionality.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from db.services.agent_version_service import AgentVersionService
from db.tables.agent_versions import AgentVersion
from common.version_factory import EnhancedAgentVersionFactory as AgentVersionFactory


class TestAgentVersionService:
    """Test cases for the AgentVersionService class."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def version_service(self, mock_db):
        """Create AgentVersionService instance with mock database."""
        return AgentVersionService(mock_db)
    
    @pytest.fixture
    def sample_config(self):
        """Sample agent configuration."""
        return {
            "agent": {
                "agent_id": "test-specialist",
                "version": 1,
                "name": "Test Specialist"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7
            },
            "instructions": "You are a test specialist agent.",
            "tools": ["test_tool"],
            "storage": {
                "type": "postgres",
                "table_name": "test_specialist"
            }
        }
    
    def test_create_version(self, version_service, sample_config):
        """Test creating a new agent version."""
        # Mock database query to return None (version doesn't exist)
        version_service.db.query.return_value.filter.return_value.first.return_value = None
        
        # Test creation
        result = version_service.create_version(
            agent_id="test-specialist",
            version=1,
            config=sample_config,
            created_by="test_user",
            description="Initial version"
        )
        
        # Verify database operations
        version_service.db.add.assert_called_once()
        version_service.db.commit.assert_called_once()
        version_service.db.refresh.assert_called_once()
    
    def test_create_duplicate_version(self, version_service, sample_config):
        """Test creating a duplicate version raises error."""
        # Mock database query to return existing version
        existing_version = AgentVersion(agent_id="test-specialist", version=1)
        version_service.db.query.return_value.filter.return_value.first.return_value = existing_version
        
        # Test that duplicate creation raises ValueError
        with pytest.raises(ValueError, match="Version 1 already exists"):
            version_service.create_version(
                agent_id="test-specialist",
                version=1,
                config=sample_config
            )
    
    def test_get_version(self, version_service):
        """Test getting a specific version."""
        # Mock database query
        expected_version = AgentVersion(agent_id="test-specialist", version=1)
        version_service.db.query.return_value.filter.return_value.first.return_value = expected_version
        
        result = version_service.get_version("test-specialist", 1)
        
        assert result == expected_version
        version_service.db.query.assert_called_once_with(AgentVersion)
    
    def test_get_active_version(self, version_service):
        """Test getting the active version."""
        # Mock database query
        expected_version = AgentVersion(agent_id="test-specialist", version=2, is_active=True)
        version_service.db.query.return_value.filter.return_value.first.return_value = expected_version
        
        result = version_service.get_active_version("test-specialist")
        
        assert result == expected_version
        version_service.db.query.assert_called_once_with(AgentVersion)
    
    def test_activate_version(self, version_service):
        """Test activating a version."""
        # Mock database queries
        version_to_activate = AgentVersion(agent_id="test-specialist", version=2)
        version_service.db.query.return_value.filter.return_value.first.return_value = version_to_activate
        
        result = version_service.activate_version(
            agent_id="test-specialist",
            version=2,
            changed_by="test_user",
            reason="Testing activation"
        )
        
        assert result.is_active == True
        version_service.db.commit.assert_called_once()
    
    def test_activate_nonexistent_version(self, version_service):
        """Test activating a version that doesn't exist."""
        # Mock database query to return None
        version_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Version 999 not found"):
            version_service.activate_version("test-specialist", 999)
    
    def test_list_versions(self, version_service):
        """Test listing all versions for an agent."""
        # Mock database query
        versions = [
            AgentVersion(agent_id="test-specialist", version=1),
            AgentVersion(agent_id="test-specialist", version=2),
            AgentVersion(agent_id="test-specialist", version=3)
        ]
        version_service.db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = versions
        
        result = version_service.list_versions("test-specialist")
        
        assert len(result) == 3
        assert all(v.agent_id == "test-specialist" for v in result)
    
    def test_deprecate_version(self, version_service):
        """Test deprecating a version."""
        # Mock database query
        version_to_deprecate = AgentVersion(agent_id="test-specialist", version=1, is_active=False)
        version_service.db.query.return_value.filter.return_value.first.return_value = version_to_deprecate
        
        result = version_service.deprecate_version(
            agent_id="test-specialist",
            version=1,
            changed_by="test_user",
            reason="Outdated version"
        )
        
        assert result.is_deprecated == True
        version_service.db.commit.assert_called_once()
    
    def test_deprecate_active_version(self, version_service):
        """Test deprecating an active version raises error."""
        # Mock database query to return active version
        active_version = AgentVersion(agent_id="test-specialist", version=2, is_active=True)
        version_service.db.query.return_value.filter.return_value.first.return_value = active_version
        
        with pytest.raises(ValueError, match="Cannot deprecate active version"):
            version_service.deprecate_version("test-specialist", 2)
    
    def test_clone_version(self, version_service, sample_config):
        """Test cloning a version."""
        # Mock database queries
        source_version = AgentVersion(agent_id="test-specialist", version=1, config=sample_config)
        version_service.db.query.return_value.filter.return_value.first.side_effect = [source_version, None]
        
        result = version_service.clone_version(
            agent_id="test-specialist",
            source_version=1,
            target_version=2,
            created_by="test_user",
            description="Cloned version"
        )
        
        # Verify database operations
        version_service.db.add.assert_called_once()
        version_service.db.commit.assert_called_once()
    
    def test_record_metrics(self, version_service):
        """Test recording metrics for a version."""
        result = version_service.record_metrics(
            agent_id="test-specialist",
            version=1,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=1500,
            escalation_rate=10,
            user_satisfaction=8
        )
        
        # Verify database operations
        version_service.db.add.assert_called_once()
        version_service.db.commit.assert_called_once()
        version_service.db.refresh.assert_called_once()


class TestAgentVersionFactory:
    """Test cases for the AgentVersionFactory class."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def version_factory(self, mock_db_session):
        """Create AgentVersionFactory instance with mock database."""
        return AgentVersionFactory(mock_db_session)
    
    @pytest.fixture
    def sample_config(self):
        """Sample agent configuration."""
        return {
            "agent": {
                "agent_id": "test-specialist",
                "version": 1,
                "name": "Test Specialist"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "instructions": "You are a test specialist agent.",
            "tools": ["test_tool"],
            "storage": {
                "type": "postgres",
                "table_name": "test_specialist",
                "auto_upgrade_schema": True
            },
            "memory": {
                "add_history_to_messages": True,
                "num_history_runs": 5
            },
            "markdown": False,
            "show_tool_calls": True
        }
    
    @patch('common.version_factory.get_db')
    @patch('common.version_factory.AgentVersionService')
    def test_load_config_from_db(self, mock_service_class, mock_get_db, version_factory, sample_config):
        """Test loading configuration from database."""
        # Mock service
        mock_service = Mock()
        mock_service.get_config.return_value = sample_config
        mock_service_class.return_value = mock_service
        
        # Test loading config
        result = version_factory._load_config_from_db("test-specialist", 1)
        
        assert result == sample_config
        mock_service.get_config.assert_called_once_with("test-specialist", 1)
    
    @patch('common.version_factory.Path')
    @patch('common.version_factory.yaml.safe_load')
    @patch('builtins.open')
    def test_load_config_from_file(self, mock_open, mock_yaml_load, mock_path, version_factory, sample_config):
        """Test loading configuration from file."""
        # Mock file operations
        mock_path.return_value.parent = Mock()
        mock_path.return_value.parent.__truediv__.return_value.__truediv__.return_value.exists.return_value = True
        mock_yaml_load.return_value = sample_config
        
        # Test loading config
        result = version_factory._load_config_from_file("test-specialist")
        
        assert result == sample_config
        mock_open.assert_called_once()
        mock_yaml_load.assert_called_once()
    
    @patch('common.version_factory.Claude')
    def test_create_model(self, mock_claude, version_factory):
        """Test creating model instance."""
        model_config = {
            "id": "claude-sonnet-4-20250514",
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        result = version_factory._create_model(model_config)
        
        mock_claude.assert_called_once_with(
            id="claude-sonnet-4-20250514",
            temperature=0.7,
            max_tokens=2000
        )
    
    @patch('common.version_factory.PostgresStorage')
    def test_create_storage(self, mock_postgres, version_factory, sample_config):
        """Test creating storage instance."""
        db_url = "postgresql://user:pass@localhost/db"
        
        result = version_factory._create_storage(sample_config, db_url)
        
        mock_postgres.assert_called_once_with(
            table_name="test_specialist",
            db_url=db_url,
            auto_upgrade_schema=True
        )
    
    @patch('common.version_factory.Agent')
    @patch('common.version_factory.get_db')
    @patch('common.version_factory.AgentVersionService')
    def test_create_agent_from_db(self, mock_service_class, mock_get_db, mock_agent, version_factory, sample_config):
        """Test creating agent from database configuration."""
        # Mock service
        mock_service = Mock()
        mock_service.get_config.return_value = sample_config
        mock_service_class.return_value = mock_service
        
        # Mock database URL
        with patch('common.version_factory.db_url', "postgresql://test"):
            result = version_factory.create_agent(
                agent_id="test-specialist",
                version=1,
                session_id="test-session",
                debug_mode=True
            )
        
        # Verify agent creation
        mock_agent.assert_called_once()
        call_args = mock_agent.call_args
        assert call_args[1]['name'] == "Test Specialist"
        assert call_args[1]['agent_id'] == "test-specialist"
        assert call_args[1]['session_id'] == "test-session"
        assert call_args[1]['debug_mode'] == True
    
    @patch('common.version_factory.get_db')
    @patch('common.version_factory.AgentVersionService')
    def test_create_agent_not_found(self, mock_service_class, mock_get_db, version_factory):
        """Test creating agent that doesn't exist."""
        # Mock service to return None
        mock_service = Mock()
        mock_service.get_config.return_value = None
        mock_service_class.return_value = mock_service
        
        with pytest.raises(ValueError, match="Agent 'nonexistent' not found"):
            version_factory.create_agent(
                agent_id="nonexistent",
                version=1,
                fallback_to_file=False
            )
    
    @patch('common.version_factory.get_db')
    @patch('common.version_factory.AgentVersionService')
    def test_migrate_file_to_database(self, mock_service_class, mock_get_db, version_factory, sample_config):
        """Test migrating file configuration to database."""
        # Mock service
        mock_service = Mock()
        mock_service.create_version.return_value = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock file loading
        with patch.object(version_factory, '_load_config_from_file', return_value=sample_config):
            result = version_factory.migrate_file_to_database(
                agent_id="test-specialist",
                version=1,
                created_by="test_user"
            )
        
        assert result == True
        mock_service.create_version.assert_called_once()
    
    @patch('common.version_factory.get_db')
    @patch('common.version_factory.AgentVersionService')
    def test_list_available_agents(self, mock_service_class, mock_get_db, version_factory):
        """Test listing available agents."""
        # Mock service
        mock_service = Mock()
        mock_service.get_all_agents.return_value = ["test-specialist", "another-specialist"]
        mock_service.list_versions.return_value = [
            Mock(version=1),
            Mock(version=2)
        ]
        mock_service.get_active_version.return_value = Mock(version=2)
        mock_service_class.return_value = mock_service
        
        # Mock file system
        with patch('common.version_factory.Path') as mock_path:
            mock_path.return_value.parent.iterdir.return_value = []
            
            result = version_factory.list_available_agents()
        
        assert "test-specialist" in result
        assert "another-specialist" in result
        assert result["test-specialist"]["source"] == "database"
        assert result["test-specialist"]["versions"] == [1, 2]
        assert result["test-specialist"]["active_version"] == 2


class TestAgentVersioningAPI:
    """Test cases for the agent versioning API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def sample_config(self):
        """Sample agent configuration."""
        return {
            "agent": {
                "agent_id": "test-specialist",
                "version": 1,
                "name": "Test Specialist"
            },
            "model": {
                "provider": "anthropic",
                "id": "claude-sonnet-4-20250514"
            },
            "instructions": "You are a test specialist agent."
        }
    
    @patch('api.routes.agent_versions.get_db')
    @patch('api.routes.agent_versions.AgentVersionService')
    def test_create_agent_version_endpoint(self, mock_service_class, mock_get_db, client, sample_config):
        """Test creating agent version via API."""
        # Mock service
        mock_service = Mock()
        mock_version = Mock()
        mock_version.id = 1
        mock_version.agent_id = "test-specialist"
        mock_version.version = 1
        mock_version.config = sample_config
        mock_version.created_at = datetime.now()
        mock_version.created_by = "api"
        mock_version.is_active = False
        mock_version.is_deprecated = False
        mock_version.description = "Test version"
        mock_service.create_version.return_value = mock_version
        mock_service_class.return_value = mock_service
        
        # Test API call
        response = client.post("/v1/agents/", json={
            "agent_id": "test-specialist",
            "version": 1,
            "config": sample_config,
            "description": "Test version",
            "is_active": False,
            "created_by": "api"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "test-specialist"
        assert data["version"] == 1
        assert data["config"] == sample_config
    
    @patch('api.routes.agent_versions.get_db')
    @patch('api.routes.agent_versions.AgentVersionService')
    def test_list_agent_versions_endpoint(self, mock_service_class, mock_get_db, client):
        """Test listing agent versions via API."""
        # Mock service
        mock_service = Mock()
        mock_version = Mock()
        mock_version.id = 1
        mock_version.agent_id = "test-specialist"
        mock_version.version = 1
        mock_version.config = {}
        mock_version.created_at = datetime.now()
        mock_version.created_by = "api"
        mock_version.is_active = True
        mock_version.is_deprecated = False
        mock_version.description = "Test version"
        mock_service.list_versions.return_value = [mock_version]
        mock_service_class.return_value = mock_service
        
        # Test API call
        response = client.get("/v1/agents/test-specialist/versions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_id"] == "test-specialist"
        assert data[0]["version"] == 1
    
    @patch('api.routes.agent_versions.get_db')
    @patch('api.routes.agent_versions.AgentVersionService')
    def test_activate_agent_version_endpoint(self, mock_service_class, mock_get_db, client):
        """Test activating agent version via API."""
        # Mock service
        mock_service = Mock()
        mock_version = Mock()
        mock_version.id = 1
        mock_version.agent_id = "test-specialist"
        mock_version.version = 1
        mock_version.config = {}
        mock_version.created_at = datetime.now()
        mock_version.created_by = "api"
        mock_version.is_active = True
        mock_version.is_deprecated = False
        mock_version.description = "Test version"
        mock_service.activate_version.return_value = mock_version
        mock_service_class.return_value = mock_service
        
        # Test API call
        response = client.put("/v1/agents/test-specialist/versions/1/activate", json={
            "reason": "Testing activation",
            "changed_by": "api"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True
        assert data["version"] == 1
    
    @patch('api.routes.agent_versions.create_versioned_agent')
    def test_run_agent_endpoint(self, mock_create_agent, client):
        """Test running agent via API."""
        # Mock agent
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_agent.run.return_value = mock_response
        mock_agent.metadata = {"version": 1, "loaded_from": "database"}
        mock_create_agent.return_value = mock_agent
        
        # Test API call
        response = client.post("/v1/agents/test-specialist/run", json={
            "message": "Hello, agent!",
            "session_id": "test-session",
            "debug_mode": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response"
        assert data["agent_id"] == "test-specialist"
        assert data["session_id"] == "test-session"


if __name__ == "__main__":
    pytest.main([__file__])