"""Integration tests for PagBank infrastructure setup."""

import pytest
from sqlalchemy import text

from pagbank.config.database import db_config, health_check
from pagbank.config.models import validate_models
from pagbank.config.settings import validate_environment


class TestInfrastructureIntegration:
    """Test infrastructure components integration."""
    
    def test_database_health_check(self, test_db):
        """Test database connection and PgVector extension."""
        health = health_check()
        
        assert health["connection"] is True, "Database connection should be healthy"
        assert health["pgvector"] is True, "PgVector extension should be available"
        assert "postgresql" in health["url"], "Database URL should contain postgresql"
    
    def test_model_validation(self):
        """Test AI model configurations."""
        validation = validate_models()
        
        assert validation["anthropic_api_key"] is True, "Anthropic API key should be valid"
        assert validation["embedding_model"] is True, "Embedding model should be available"
    
    def test_environment_validation(self):
        """Test environment setup."""
        validation = validate_environment()
        
        assert validation["data_dir"] is True, "Data directory should exist"
        assert validation["logs_dir"] is True, "Logs directory should exist"
        assert validation["knowledge_dir"] is True, "Knowledge directory should exist"
        assert validation["anthropic_api_key"] is True, "Anthropic API key should be set"
        assert validation["valid_port"] is True, "API port should be valid"
        assert validation["valid_workers"] is True, "Worker count should be valid"
        assert validation["valid_timeout"] is True, "Timeout should be valid"
    
    def test_database_operations(self, db_session):
        """Test basic database operations."""
        # Test basic query
        result = db_session.execute(text("SELECT 1 as test_value;"))
        assert result.fetchone()[0] == 1
        
        # Test PgVector operations
        result = db_session.execute(text("SELECT vector_dims(vector '[1,2,3,4,5]');"))
        assert result.fetchone()[0] == 5
        
        # Test table creation (temporary)
        db_session.execute(text("""
            CREATE TEMPORARY TABLE test_embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT,
                embedding VECTOR(5)
            );
        """))
        
        # Insert test data
        db_session.execute(text("""
            INSERT INTO test_embeddings (content, embedding) 
            VALUES ('test content', '[1,2,3,4,5]');
        """))
        
        # Query test data
        result = db_session.execute(text("""
            SELECT content, embedding FROM test_embeddings WHERE id = 1;
        """))
        row = result.fetchone()
        assert row[0] == "test content"
        assert len(str(row[1])) > 0  # Vector should be stored
        
        db_session.commit()
    
    def test_claude_client_integration(self, claude_client):
        """Test Claude client integration."""
        # Test basic message
        response = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=20,
            messages=[
                {"role": "user", "content": "Hello, respond with exactly 'Integration test success'"}
            ]
        )
        
        assert len(response.content) > 0
        assert response.content[0].type == "text"
        assert "success" in response.content[0].text.lower()
    
    def test_settings_integration(self, test_settings):
        """Test settings configuration."""
        # Test team configurations
        teams = test_settings.team_configs
        assert len(teams) == 5  # Should have 5 teams
        assert "cards" in teams
        assert "digital_account" in teams
        assert "investments" in teams
        assert "credit" in teams
        assert "insurance" in teams
        
        # Test knowledge filters
        filters = test_settings.get_all_knowledge_filters()
        assert len(filters) > 0
        assert "cartao" in filters
        assert "conta" in filters
        assert "investimento" in filters
        
        # Test demo scenarios
        scenarios = test_settings.demo_scenarios
        assert len(scenarios) == 6
        assert "Consulta de Saldo e Extrato" in scenarios
        assert "Problemas com Cartão de Crédito" in scenarios
    
    def test_full_infrastructure_stack(self, test_db, claude_client, test_settings):
        """Test complete infrastructure stack integration."""
        # Test database
        health = health_check()
        assert health["connection"] and health["pgvector"]
        
        # Test models
        validation = validate_models()
        assert validation["anthropic_api_key"]
        
        # Test settings
        env_validation = validate_environment()
        assert all(env_validation.values())
        
        # Test combined operations
        with db_config.get_session() as session:
            # Create a test table with vector column
            session.execute(text("""
                CREATE TEMPORARY TABLE integration_test (
                    id SERIAL PRIMARY KEY,
                    user_message TEXT,
                    ai_response TEXT,
                    embedding VECTOR(5),
                    team_assigned TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Insert test data
            session.execute(text("""
                INSERT INTO integration_test 
                (user_message, ai_response, embedding, team_assigned) 
                VALUES 
                ('Olá, preciso de ajuda', 'Como posso ajudá-lo?', '[1,2,3,4,5]', 'cards');
            """))
            
            # Query and verify
            result = session.execute(text("""
                SELECT user_message, ai_response, team_assigned 
                FROM integration_test 
                WHERE id = 1;
            """))
            row = result.fetchone()
            assert row[0] == "Olá, preciso de ajuda"
            assert row[1] == "Como posso ajudá-lo?"
            assert row[2] == "cards"
            
            session.commit()
    
    @pytest.mark.asyncio
    async def test_async_operations(self, test_db):
        """Test async database operations."""
        import asyncpg

        # Test async connection
        conn = await asyncpg.connect(
            host="localhost",
            port=5532,
            database="ai",
            user="ai",
            password="ai"
        )
        
        # Test basic async query
        result = await conn.fetchval("SELECT 1;")
        assert result == 1
        
        # Test PgVector async operations
        result = await conn.fetchval("SELECT vector_dims(vector '[1,2,3]');")
        assert result == 3
        
        await conn.close()
    
    def test_performance_benchmarks(self, test_db, claude_client, performance_thresholds):
        """Test performance benchmarks."""
        import time

        # Test database query performance
        start_time = time.time()
        with db_config.get_session() as session:
            for _ in range(10):
                session.execute(text("SELECT 1;"))
        db_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        assert db_time < performance_thresholds["db_query_time_ms"], f"Database queries too slow: {db_time}ms"
        
        # Test Claude API performance
        start_time = time.time()
        claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        api_time = (time.time() - start_time) * 1000
        
        assert api_time < performance_thresholds["response_time_ms"], f"Claude API too slow: {api_time}ms"
    
    def test_error_handling(self, test_db):
        """Test error handling in infrastructure."""
        # Test database error handling
        with pytest.raises(Exception):
            with db_config.get_session() as session:
                session.execute(text("SELECT * FROM nonexistent_table;"))
        
        # Test model error handling
        with pytest.raises(Exception):
            from pagbank.config.models import ModelConfig
            config = ModelConfig()
            config.anthropic_api_key = "invalid_key"
            config.validate_api_key()
    
    def test_concurrent_operations(self, test_db):
        """Test concurrent database operations."""
        import threading
        
        results = []
        
        def db_operation():
            with db_config.get_session() as session:
                result = session.execute(text("SELECT 1;")).fetchone()[0]
                results.append(result)
        
        # Run 5 concurrent operations
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=db_operation)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert len(results) == 5
        assert all(result == 1 for result in results)
    
    def test_memory_usage(self, test_db, claude_client):
        """Test memory usage within acceptable limits."""
        import gc

        import psutil

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        for _ in range(10):
            with db_config.get_session() as session:
                session.execute(text("SELECT 1;"))
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = current_memory - baseline_memory
        
        # Should not increase more than 100MB
        assert memory_increase < 100, f"Memory usage increased too much: {memory_increase}MB"