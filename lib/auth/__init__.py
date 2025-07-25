"""
Authentication module for Automagik Hive.

Provides simple x-api-key authentication with auto-generated keys.
"""

from .service import AuthService
from .dependencies import require_api_key, optional_api_key
from .init_service import AuthInitService

__all__ = [
    "AuthService",
    "require_api_key", 
    "optional_api_key",
    "AuthInitService"
]