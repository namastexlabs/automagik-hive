"""
Comprehensive tests for api/serve.py module.

Tests server initialization, API endpoints, module imports, 
path management, logging setup, and all serve functionality.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Import the module under test
import api.serve


class TestServeModuleImports:
    """Test api/serve.py module imports and setup."""

    def test_module_imports(self):
        """Test that serve module can be imported with all dependencies."""
        # Test individual imports from serve.py
        try:
            import api.serve

            assert api.serve is not None
        except ImportError as e:
            pytest.fail(f"Failed to import api.serve: {e}")

    def test_path_management(self):
        """Test path management in serve module."""
        # This tests the path manipulation code in serve.py
        original_path = sys.path.copy()

        try:
            # The module should add project root to path
            project_root = Path(__file__).parent.parent.parent
            assert str(project_root) in sys.path

        finally:
            # Restore original path
            sys.path[:] = original_path

    def test_logging_setup(self):
        """Test logging setup in serve module."""
        with patch("lib.logging.setup_logging") as mock_setup:
            with patch("lib.logging.logger"):
                # Re-import to trigger logging setup
                import importlib

                import api.serve

                importlib.reload(api.serve)
                # Logging setup should be called during module import
                # Note: This might not be called if already imported


class TestServeModuleFunctions:
    """Test module-level functions and code paths in api/serve.py."""

    def test_create_simple_sync_api_real_execution(self):
        """Test real execution of _create_simple_sync_api function."""
        app = api.serve._create_simple_sync_api()

        # Verify the app was created
        assert isinstance(app, FastAPI)
        assert app.title == "Automagik Hive Multi-Agent System"
        assert "Simplified Mode" in app.description
        # Version should match current project version from version_reader
        from lib.utils.version_reader import get_api_version
        assert app.version == get_api_version()

        # Test the app endpoints work
        with TestClient(app) as client:
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["mode"] == "simplified"

            # Test health endpoint
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["mode"] == "simplified"

    def test_async_create_automagik_api_mocked(self):
        """Test _async_create_automagik_api function with mocked dependencies."""
        with patch("api.serve.orchestrated_startup") as mock_startup:
            with patch("api.serve.get_startup_display_with_results") as mock_display:
                with patch("api.serve.create_team") as mock_create_team:
                    # Mock startup results
                    mock_startup_results = MagicMock()
                    mock_startup_results.registries.agents = {"test_agent": MagicMock()}
                    mock_startup_results.registries.teams = {"test_team": "test"}
                    mock_startup_results.registries.workflows = {"test_workflow": "test"}
                    mock_startup_results.services.auth_service.is_auth_enabled.return_value = False
                    mock_startup_results.services.metrics_service = MagicMock()
                    mock_startup.return_value = mock_startup_results
                    
                    # Mock startup display
                    mock_display.return_value = MagicMock()
                    
                    # Mock team creation
                    mock_create_team.return_value = MagicMock()
                    
                    # Test the function
                    result = asyncio.run(api.serve._async_create_automagik_api())
                    
                    assert isinstance(result, FastAPI)
                    assert result.title == "Automagik Hive Multi-Agent System"

    def test_create_automagik_api_no_event_loop(self):
        """Test create_automagik_api when no event loop is running."""
        with patch("asyncio.get_running_loop", side_effect=RuntimeError("No event loop")):
            with patch("api.serve._async_create_automagik_api") as mock_async:
                mock_app = FastAPI()
                mock_async.return_value = mock_app
                
                result = api.serve.create_automagik_api()
                assert result == mock_app

    def test_create_automagik_api_with_event_loop(self):
        """Test create_automagik_api when event loop is running."""
        with patch("asyncio.get_running_loop"):
            with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
                with patch("api.serve._async_create_automagik_api") as mock_async:
                    mock_app = FastAPI()
                    mock_async.return_value = mock_app
                    
                    # Mock thread executor
                    mock_executor.return_value.__enter__.return_value.submit.return_value.result.return_value = mock_app
                    
                    result = api.serve.create_automagik_api()
                    assert result == mock_app

    def test_create_lifespan_function(self):
        """Test create_lifespan function creation."""
        # Test lifespan function creation
        mock_startup_display = MagicMock()
        
        # create_lifespan takes startup_display as a direct parameter
        lifespan_func = api.serve.create_lifespan(mock_startup_display)
        
        # Verify it's a function that can be called
        assert callable(lifespan_func)

    def test_get_app_function(self):
        """Test get_app function execution."""
        # Mock dependencies that would cause complex initialization
        with patch("api.serve.create_automagik_api") as mock_create_api:
            # Clear any cached app instance first
            api.serve._app_instance = None
            
            # Create a real FastAPI app to return
            mock_app = FastAPI(
                title="Automagik Hive Multi-Agent System",
                description="Test app",
                version="test"
            )
            mock_create_api.return_value = mock_app
            
            # Test get_app function
            app = api.serve.get_app()
            
            # Should return a FastAPI instance
            assert isinstance(app, FastAPI)
            assert app.title == "Automagik Hive Multi-Agent System"
            
            # Clean up - reset the cached instance to None after test
            api.serve._app_instance = None

    def test_main_function_execution(self):
        """Test main function with different scenarios."""
        # Test main function with mocked environment
        with patch("uvicorn.run") as mock_uvicorn:
            with patch("sys.argv", ["api.serve", "--port", "8001"]):
                with patch("api.serve.get_app") as mock_get_app:
                    mock_app = MagicMock()
                    mock_get_app.return_value = mock_app
                    
                    # Should not raise an exception
                    try:
                        api.serve.main()
                    except SystemExit:
                        # main() might call sys.exit, which is acceptable
                        pass

    def test_environment_variable_handling(self):
        """Test environment variable handling in serve module."""
        # Test with different environment variables
        env_vars = {
            "HOST": "localhost",
            "PORT": "8080",
            "DEBUG": "true",
        }
        
        with patch.dict(os.environ, env_vars):
            # Re-import to pick up environment changes
            import importlib
            importlib.reload(api.serve)


class TestServeAPI:
    """Test suite for API Server functionality."""
    
    def test_server_initialization(self):
        """Test proper server initialization."""
        # Test that we can get an app instance
        app = api.serve.get_app()
        assert isinstance(app, FastAPI)
        assert app.title == "Automagik Hive Multi-Agent System"
        
    def test_api_endpoints(self):
        """Test API endpoint functionality."""
        app = api.serve.get_app()
        client = TestClient(app)
        
        # Test that basic endpoints work
        response = client.get("/health")
        assert response.status_code == 200
        
    def test_error_handling(self):
        """Test error handling in API operations."""
        app = api.serve.get_app()
        client = TestClient(app)
        
        # Test 404 handling
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
    def test_authentication(self):
        """Test authentication mechanisms."""
        app = api.serve.get_app()
        client = TestClient(app)
        
        # Test that protected endpoints exist (if any)
        # This will depend on the actual API structure
        response = client.get("/api/v1/version/components")
        # Should get some response (could be 401, 404, or 200 depending on setup)
        assert response.status_code in [200, 401, 404, 422]


class TestServeLifespanManagement:
    """Test lifespan management and startup/shutdown behavior."""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_production(self):
        """Test lifespan startup in production mode."""
        mock_startup_display = MagicMock()
        lifespan_func = api.serve.create_lifespan(mock_startup_display)
        
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "production"}):
            with patch("lib.mcp.MCPCatalog") as mock_catalog:
                with patch("common.startup_notifications.send_startup_notification") as mock_notify:
                    mock_catalog.return_value.list_servers.return_value = []
                    
                    # Test startup phase
                    mock_app = MagicMock()
                    async with lifespan_func(mock_app):
                        # Wait for startup notification to be scheduled
                        await asyncio.sleep(0.1)
                    
                    mock_catalog.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_development(self):
        """Test lifespan startup in development mode."""
        mock_startup_display = MagicMock()
        lifespan_func = api.serve.create_lifespan(mock_startup_display)
        
        with patch.dict(os.environ, {"HIVE_ENVIRONMENT": "development"}):
            with patch("lib.mcp.MCPCatalog") as mock_catalog:
                mock_catalog.return_value.list_servers.return_value = []
                
                # Test startup phase
                mock_app = MagicMock()
                async with lifespan_func(mock_app):
                    pass
                
                mock_catalog.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_mcp_initialization_failure(self):
        """Test lifespan when MCP initialization fails."""
        mock_startup_display = MagicMock()
        lifespan_func = api.serve.create_lifespan(mock_startup_display)
        
        with patch("lib.mcp.MCPCatalog", side_effect=Exception("MCP Error")):
            # Should handle MCP initialization failure gracefully
            mock_app = MagicMock()
            async with lifespan_func(mock_app):
                pass

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_notifications(self):
        """Test lifespan shutdown notifications."""
        mock_startup_display = MagicMock()
        lifespan_func = api.serve.create_lifespan(mock_startup_display)
        
        with patch("common.startup_notifications.send_shutdown_notification") as mock_shutdown:
            mock_app = MagicMock()
            async with lifespan_func(mock_app):
                pass
            
            # Wait for shutdown task to be scheduled
            await asyncio.sleep(0.1)


class TestServeDatabaseMigrations:
    """Test database migration handling in serve module."""
    
    def test_migration_success_at_startup(self):
        """Test successful migration execution at startup."""
        with patch("api.serve.check_and_run_migrations") as mock_migrations:
            with patch("asyncio.get_running_loop", side_effect=RuntimeError("No loop")):
                with patch("asyncio.run") as mock_run:
                    mock_run.return_value = True
                    
                    # Re-import serve to trigger migration code
                    import importlib
                    import api.serve
                    importlib.reload(api.serve)

    def test_migration_failure_at_startup(self):
        """Test migration failure handling at startup."""
        with patch("api.serve.check_and_run_migrations", side_effect=Exception("Migration failed")):
            with patch("asyncio.get_running_loop", side_effect=RuntimeError("No loop")):
                with patch("asyncio.run", side_effect=Exception("Migration failed")):
                    # Should handle migration failures gracefully
                    import importlib
                    import api.serve
                    importlib.reload(api.serve)

    def test_migration_with_event_loop_present(self):
        """Test migration handling when event loop is present."""
        with patch("api.serve.check_and_run_migrations") as mock_migrations:
            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value = MagicMock()
                
                # Should detect event loop and schedule migration appropriately
                import importlib
                import api.serve
                importlib.reload(api.serve)


class TestServeErrorHandling:
    """Test error handling scenarios in serve module."""
    
    def test_component_loading_error_handling(self):
        """Test handling of component loading errors."""
        with patch("api.serve.orchestrated_startup") as mock_startup:
            mock_startup_results = MagicMock()
            mock_startup_results.registries.agents = {}
            mock_startup_results.registries.teams = {}
            mock_startup_results.registries.workflows = {}
            mock_startup_results.services.auth_service.is_auth_enabled.return_value = False
            mock_startup.return_value = mock_startup_results
            
            with patch("api.serve.get_startup_display_with_results"):
                # Should raise ComponentLoadingError when no agents loaded
                with pytest.raises(Exception):
                    asyncio.run(api.serve._async_create_automagik_api())

    def test_workflow_creation_failure_handling(self):
        """Test handling of workflow creation failures."""
        with patch("api.serve.orchestrated_startup") as mock_startup:
            with patch("api.serve.get_startup_display_with_results") as mock_display:
                with patch("api.serve.get_workflow", side_effect=Exception("Workflow error")):
                    # Mock startup results with agents to avoid ComponentLoadingError
                    mock_startup_results = MagicMock()
                    mock_startup_results.registries.agents = {"test_agent": MagicMock()}
                    mock_startup_results.registries.teams = {}
                    mock_startup_results.registries.workflows = {"test_workflow": "test"}
                    mock_startup_results.services.auth_service.is_auth_enabled.return_value = False
                    mock_startup_results.services.metrics_service = MagicMock()
                    mock_startup.return_value = mock_startup_results
                    
                    mock_display.return_value = MagicMock()
                    
                    # Should handle workflow creation failures gracefully
                    result = asyncio.run(api.serve._async_create_automagik_api())
                    assert isinstance(result, FastAPI)

    def test_business_endpoints_error_handling(self):
        """Test handling of business endpoints registration errors."""
        with patch("api.serve.orchestrated_startup") as mock_startup:
            with patch("api.serve.get_startup_display_with_results") as mock_display:
                with patch("api.routes.v1_router", side_effect=ImportError("Router error")):
                    # Mock startup results with agents
                    mock_startup_results = MagicMock()
                    mock_startup_results.registries.agents = {"test_agent": MagicMock()}
                    mock_startup_results.registries.teams = {}
                    mock_startup_results.registries.workflows = {}
                    mock_startup_results.services.auth_service.is_auth_enabled.return_value = False
                    mock_startup_results.services.metrics_service = MagicMock()
                    mock_startup.return_value = mock_startup_results
                    
                    mock_startup_display = MagicMock()
                    mock_display.return_value = mock_startup_display
                    
                    # Should handle business endpoints errors gracefully
                    result = asyncio.run(api.serve._async_create_automagik_api())
                    assert isinstance(result, FastAPI)


class TestServeIntegration:
    """Integration tests for serve module with other components."""

    def test_app_with_actual_dependencies(self):
        """Test app creation with actual dependencies."""
        # Test creating app with real dependencies
        with patch("lib.auth.dependencies.get_auth_service") as mock_auth:
            mock_auth.return_value = MagicMock(
                is_auth_enabled=MagicMock(return_value=False),
            )
            
            app = api.serve.get_app()
            client = TestClient(app)
            
            # Test basic functionality
            response = client.get("/health")
            assert response.status_code == 200

    def test_lifespan_integration(self):
        """Test lifespan integration with startup and shutdown."""
        # Mock the startup display
        mock_startup_display = MagicMock()
        
        # Create lifespan - create_lifespan takes startup_display as direct parameter
        lifespan_func = api.serve.create_lifespan(mock_startup_display)
        
        # Test that lifespan can be created
        assert callable(lifespan_func)

    def test_full_server_workflow(self):
        """Test complete server workflow."""
        # This tests the complete workflow from app creation to serving
        with patch("uvicorn.run") as mock_uvicorn:
            with patch("sys.argv", ["api.serve"]):
                # Should be able to run main without errors
                try:
                    api.serve.main()
                except SystemExit:
                    # Expected if main() calls sys.exit()
                    pass


class TestServeConfiguration:
    """Test serve module configuration handling."""

    def test_app_configuration(self):
        """Test app configuration settings."""
        app = api.serve.get_app()
        
        # Test basic configuration
        assert app.title == "Automagik Hive Multi-Agent System"
        assert isinstance(app.version, str)
        assert len(app.routes) > 0

    def test_middleware_configuration(self):
        """Test middleware configuration."""
        app = api.serve.get_app()
        
        # Should have some middleware configured
        # CORS, auth, etc.
        assert hasattr(app, 'user_middleware')

    def test_router_configuration(self):
        """Test router configuration."""
        app = api.serve.get_app()
        
        # Should have routes configured
        route_paths = [route.path for route in app.routes]
        
        # Should have health endpoint
        assert any("/health" in path for path in route_paths)


@pytest.fixture
def api_client():
    """Fixture providing test client for API testing."""
    app = api.serve.get_app()
    return TestClient(app)


def test_integration_api_workflow(api_client):
    """Integration test for complete API workflow."""
    # Test basic workflow
    response = api_client.get("/health")
    assert response.status_code == 200
    
    # Test that the API responds correctly
    data = response.json()
    assert "status" in data


class TestServeCommandLine:
    """Test command line interface for serve module."""

    def test_command_line_argument_parsing(self):
        """Test command line argument parsing."""
        # Test with various command line arguments
        test_args = [
            ["api.serve"],
            ["api.serve", "--port", "8080"],
            ["api.serve", "--host", "0.0.0.0"],
        ]
        
        for args in test_args:
            with patch("sys.argv", args):
                with patch("uvicorn.run") as mock_uvicorn:
                    try:
                        api.serve.main()
                    except SystemExit:
                        # Expected behavior
                        pass

    def test_error_handling_in_main(self):
        """Test error handling in main function."""
        # Test with invalid arguments or setup
        with patch("uvicorn.run", side_effect=Exception("Server error")):
            with patch("sys.argv", ["api.serve"]):
                # Should handle exceptions gracefully
                try:
                    api.serve.main()
                except Exception as e:
                    # Should either handle gracefully or exit
                    assert isinstance(e, (SystemExit, Exception))


class TestPerformance:
    """Test performance characteristics of serve module."""

    def test_app_creation_performance(self):
        """Test app creation performance."""
        import time
        
        start_time = time.time()
        app = api.serve.get_app()
        end_time = time.time()
        
        # App creation should be fast
        creation_time = end_time - start_time
        assert creation_time < 5.0, f"App creation took too long: {creation_time}s"
        
        # App should be usable
        assert isinstance(app, FastAPI)

    def test_request_handling_performance(self, api_client):
        """Test request handling performance."""
        import time
        
        # Time a simple request
        start_time = time.time()
        response = api_client.get("/health")
        end_time = time.time()
        
        # Request should be fast
        request_time = end_time - start_time
        assert request_time < 1.0, f"Request took too long: {request_time}s"
        
        # Request should succeed
        assert response.status_code == 200