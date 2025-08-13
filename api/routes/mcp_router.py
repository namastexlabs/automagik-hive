"""
MCP Status API Routes

Simple REST endpoints for MCP server status information.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from lib.logging import logger
from lib.mcp import MCPCatalog, get_mcp_tools

router = APIRouter(prefix="/mcp", tags=["MCP Status"])


@router.get("/status")
async def get_mcp_status() -> dict[str, Any]:
    """
    Get overall MCP system status.

    Returns:
        System status with available servers
    """
    try:
        catalog = MCPCatalog()
        servers = catalog.list_servers()

        return {
            "status": "ok",
            "available_servers": servers,
            "total_servers": len(servers),
            "timestamp": None,
        }
    except Exception as e:
        logger.error(f"🌐 Error getting MCP status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP status: {e}")


@router.get("/servers")
async def list_available_servers() -> dict[str, Any]:
    """
    List all available MCP servers.

    Returns:
        List of available server names and their basic information
    """
    try:
        catalog = MCPCatalog()
        servers = catalog.list_servers()

        # Get additional server information
        server_details = {}
        for server_name in servers:
            try:
                server_info = catalog.get_server_info(server_name)
                server_details[server_name] = {
                    "available": True,
                    "type": server_info.get("type"),
                    "is_sse_server": server_info.get("is_sse_server"),
                    "is_command_server": server_info.get("is_command_server"),
                }
            except Exception as e:
                server_details[server_name] = {"available": False, "error": str(e)}

        return {
            "status": "ok",
            "servers": servers,
            "server_details": server_details,
            "total_servers": len(servers),
        }
    except Exception as e:
        logger.error(f"🌐 Error listing available servers: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing servers: {e}")


@router.get("/servers/{server_name}/test")
async def test_server_connection(server_name: str) -> dict[str, Any]:
    """
    Test connection to a specific MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        Connection test results
    """
    try:
        # Test connection by creating MCP tools
        async with get_mcp_tools(server_name) as tools:
            # Try to list tools to verify connection
            available_tools = []
            if hasattr(tools, "list_tools"):
                try:
                    available_tools = tools.list_tools()
                except Exception as e:
                    logger.warning(f"🌐 Could not list tools for {server_name}: {e}")

            return {
                "status": "ok",
                "server_name": server_name,
                "connection_test": "success",
                "available_tools": len(available_tools),
                "tools": available_tools if available_tools else [],
            }

    except Exception as e:
        logger.error(f"🌐 Connection test failed for {server_name}: {e}")
        return {
            "status": "error",
            "server_name": server_name,
            "connection_test": "failed",
            "error": str(e),
        }


@router.get("/config")
async def get_mcp_configuration() -> dict[str, Any]:
    """
    Get MCP system configuration information.

    Returns:
        Configuration details and available servers from catalog
    """
    try:
        catalog = MCPCatalog()
        servers = catalog.list_servers()

        server_configs = {}
        for server_name in servers:
            try:
                server_info = catalog.get_server_info(server_name)
                server_configs[server_name] = {
                    "type": server_info.get("type"),
                    "is_sse_server": server_info.get("is_sse_server"),
                    "is_command_server": server_info.get("is_command_server"),
                    "url": server_info.get("url"),
                    "command": server_info.get("command"),
                }
            except Exception as e:
                server_configs[server_name] = {"error": str(e)}

        return {
            "status": "ok",
            "catalog_servers": servers,
            "server_configurations": server_configs,
            "total_configured_servers": len(servers),
        }
    except Exception as e:
        logger.error(f"🌐 Error getting MCP configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting configuration: {e}")


# Add router to the main application
def register_mcp_routes(app: "FastAPI") -> None:
    """Register MCP routes with the FastAPI application"""
    app.include_router(router)
