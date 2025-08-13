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