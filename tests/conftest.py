"""Pytest configuration and fixtures for PagBank tests."""

import asyncio

import pytest

from config.database import db_config, init_database
from config.models import model_config
from config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Initialize test database connection."""
    # Initialize database with PgVector
    init_database()
    return db_config


@pytest.fixture(scope="session")
def claude_client():
    """Get Claude client for testing."""
    return model_config.get_anthropic_client()


@pytest.fixture(scope="session")
def test_settings():
    """Get test settings."""
    return settings


@pytest.fixture
def db_session(test_db):
    """Get database session for testing."""
    session = test_db.get_session()
    yield session
    session.close()


@pytest.fixture
def sample_user_message():
    """Sample user message for testing."""
    return {
        "content": "Olá, gostaria de saber sobre meu saldo",
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "timestamp": "2024-01-01T10:00:00Z",
        "language": "pt-BR"
    }


@pytest.fixture
def sample_knowledge_entries():
    """Sample knowledge entries for testing."""
    return [
        {
            "id": "test_001",
            "category": "conta",
            "subcategory": "saldo",
            "question": "Como consultar saldo?",
            "answer": "Para consultar seu saldo, acesse o app PagBank...",
            "keywords": ["saldo", "consultar", "conta"],
            "team_filter": "digital_account"
        },
        {
            "id": "test_002", 
            "category": "cartao",
            "subcategory": "fatura",
            "question": "Como pagar fatura do cartão?",
            "answer": "Para pagar sua fatura, acesse a área de cartões...",
            "keywords": ["fatura", "cartão", "pagar"],
            "team_filter": "cards"
        }
    ]


@pytest.fixture
def sample_memory_entries():
    """Sample memory entries for testing."""
    return [
        {
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "content": "Usuário perguntou sobre saldo",
            "type": "user_query",
            "timestamp": "2024-01-01T10:00:00Z",
            "metadata": {"team": "digital_account", "resolved": True}
        },
        {
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "content": "Informações sobre conta digital fornecidas",
            "type": "agent_response",
            "timestamp": "2024-01-01T10:01:00Z",
            "metadata": {"team": "digital_account", "satisfaction": "positive"}
        }
    ]


@pytest.fixture
def sample_teams():
    """Sample team configurations for testing."""
    return {
        "test_cards": {
            "name": "Test Cards Team",
            "description": "Test team for card-related queries",
            "knowledge_filters": ["cartao", "credito", "debito"],
            "max_agents": 2
        },
        "test_digital_account": {
            "name": "Test Digital Account Team",
            "description": "Test team for account-related queries",
            "knowledge_filters": ["conta", "saldo", "pix"],
            "max_agents": 2
        }
    }


# Health check fixtures
@pytest.fixture
def health_check_services():
    """Services to check for health tests."""
    return [
        "database",
        "pgvector",
        "anthropic_api",
        "memory_system",
        "knowledge_base"
    ]


# Performance test fixtures
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "response_time_ms": 5000,  # 5 seconds
        "memory_usage_mb": 512,    # 512 MB
        "db_query_time_ms": 1000,  # 1 second
        "knowledge_search_ms": 2000, # 2 seconds
    }


# Mock fixtures
@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    return {
        "content": [
            {
                "type": "text",
                "text": "Olá! Seu saldo atual é R$ 1.234,56. Posso ajudá-lo com mais alguma coisa?"
            }
        ],
        "model": "claude-sonnet-4-20250514",
        "role": "assistant",
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "type": "message",
        "usage": {
            "input_tokens": 50,
            "output_tokens": 30
        }
    }


@pytest.fixture
def mock_embedding_response():
    """Mock embedding response."""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # 500-dimensional mock embedding


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup code would go here
    # For now, we'll just pass since we're using a test database


# Integration test fixtures
@pytest.fixture
def integration_test_flow():
    """Complete integration test flow data."""
    return {
        "user_message": "Preciso de ajuda com meu cartão de crédito",
        "expected_team": "cards",
        "expected_response_type": "helpful_response",
        "expected_memory_entries": 2,
        "expected_knowledge_searches": 1
    }