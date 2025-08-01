"""
FastAPI authentication dependencies.

Provides dependency injection for x-api-key authentication.
"""

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from .service import AuthService

# Global auth service instance
auth_service: AuthService = AuthService()

# API Key security scheme for OpenAPI docs
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def require_api_key(x_api_key: str | None = Depends(api_key_header)) -> bool:
    """
    Require valid x-api-key header for endpoint access.

    Args:
        x_api_key: API key from x-api-key header

    Returns:
        bool: True if valid

    Raises:
        HTTPException: 401 if invalid or missing API key
    """
    is_valid = await auth_service.validate_api_key(x_api_key)

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing x-api-key header",
            headers={"WWW-Authenticate": "x-api-key"},
        )

    return True


async def optional_api_key(x_api_key: str | None = Depends(api_key_header)) -> bool:
    """
    Optional API key validation for endpoints that can be public.

    Args:
        x_api_key: API key from x-api-key header

    Returns:
        bool: True if valid key provided, False if no key or invalid
    """
    if not x_api_key:
        return False

    return await auth_service.validate_api_key(x_api_key)


def get_auth_service() -> AuthService:
    """
    Get the global authentication service.

    Returns:
        AuthService: The authentication service instance
    """
    return auth_service
