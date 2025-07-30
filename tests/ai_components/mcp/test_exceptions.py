"""
Tests for lib/mcp/exceptions.py - MCP Exception classes
"""

import pytest

from lib.mcp.exceptions import MCPConnectionError, MCPException


class TestMCPException:
    """Test base MCP exception class."""

    def test_basic_exception_creation(self) -> None:
        """Test creating a basic MCP exception."""
        message = "Test MCP error"
        exception = MCPException(message)

        assert str(exception) == message
        assert isinstance(exception, Exception)

    def test_inheritance_chain(self) -> None:
        """Test that MCPException inherits from Exception."""
        exception = MCPException("test")

        assert isinstance(exception, Exception)
        assert isinstance(exception, MCPException)

    def test_exception_can_be_raised(self) -> None:
        """Test that MCPException can be raised and caught."""
        message = "Test exception message"

        with pytest.raises(MCPException) as exc_info:
            raise MCPException(message)

        assert str(exc_info.value) == message

    def test_exception_with_empty_message(self) -> None:
        """Test MCPException with empty message."""
        exception = MCPException("")
        assert str(exception) == ""

    def test_exception_with_none_message(self) -> None:
        """Test MCPException with None message."""
        exception = MCPException(None)
        assert str(exception) == "None"


class TestMCPConnectionError:
    """Test MCP connection error exception class."""

    def test_basic_connection_error_creation(self) -> None:
        """Test creating a basic MCP connection error."""
        message = "Connection failed"
        exception = MCPConnectionError(message)

        assert str(exception) == message
        assert isinstance(exception, MCPException)
        assert isinstance(exception, Exception)
        assert isinstance(exception, MCPConnectionError)
        assert exception.server_name is None

    def test_connection_error_with_server_name(self) -> None:
        """Test creating MCP connection error with server name."""
        message = "Connection to server failed"
        server_name = "test-server"
        exception = MCPConnectionError(message, server_name=server_name)

        assert str(exception) == message
        assert exception.server_name == server_name

    def test_connection_error_positional_server_name(self) -> None:
        """Test creating MCP connection error with positional server name."""
        message = "Connection failed"
        server_name = "my-server"
        exception = MCPConnectionError(message, server_name)

        assert str(exception) == message
        assert exception.server_name == server_name

    def test_inheritance_chain(self) -> None:
        """Test that MCPConnectionError inherits from MCPException."""
        exception = MCPConnectionError("test")

        assert isinstance(exception, Exception)
        assert isinstance(exception, MCPException)
        assert isinstance(exception, MCPConnectionError)

    def test_connection_error_can_be_raised(self) -> None:
        """Test that MCPConnectionError can be raised and caught."""
        message = "Connection timeout"
        server_name = "timeout-server"

        with pytest.raises(MCPConnectionError) as exc_info:
            raise MCPConnectionError(message, server_name=server_name)

        assert str(exc_info.value) == message
        assert exc_info.value.server_name == server_name

    def test_catch_as_base_exception(self) -> None:
        """Test that MCPConnectionError can be caught as MCPException."""
        message = "Network error"
        server_name = "network-server"

        with pytest.raises(MCPException) as exc_info:
            raise MCPConnectionError(message, server_name=server_name)

        # Should be caught as MCPException but still be MCPConnectionError
        assert isinstance(exc_info.value, MCPConnectionError)
        assert str(exc_info.value) == message
        assert exc_info.value.server_name == server_name

    def test_server_name_attribute_access(self) -> None:
        """Test direct access to server_name attribute."""
        server_name = "attribute-test-server"
        exception = MCPConnectionError("test message", server_name=server_name)

        # Test attribute access
        assert hasattr(exception, "server_name")
        assert exception.server_name == server_name

        # Test attribute modification
        new_server_name = "modified-server"
        exception.server_name = new_server_name
        assert exception.server_name == new_server_name

    def test_empty_server_name(self) -> None:
        """Test MCPConnectionError with empty server name."""
        exception = MCPConnectionError("test", server_name="")
        assert exception.server_name == ""

    def test_none_server_name_explicit(self) -> None:
        """Test MCPConnectionError with explicit None server name."""
        exception = MCPConnectionError("test", server_name=None)
        assert exception.server_name is None

    def test_exception_str_representation(self) -> None:
        """Test string representation of exceptions."""
        # Test basic exception
        basic_exception = MCPException("Basic error")
        assert str(basic_exception) == "Basic error"

        # Test connection error without server name
        conn_exception = MCPConnectionError("Connection error")
        assert str(conn_exception) == "Connection error"

        # Test connection error with server name
        conn_with_server = MCPConnectionError("Server connection failed", "my-server")
        assert str(conn_with_server) == "Server connection failed"
        # Note: server_name is stored as attribute but doesn't change str representation

    def test_exception_repr_representation(self) -> None:
        """Test repr representation of exceptions."""
        exception = MCPConnectionError("Test error", "test-server")
        repr_str = repr(exception)

        # Should contain the class name and message
        assert "MCPConnectionError" in repr_str
        assert "Test error" in repr_str


if __name__ == "__main__":
    pytest.main([__file__])
