"""
Authentication module for Automagik Hive.

Provides simple x-api-key authentication with auto-generated keys,
plus comprehensive credential management for PostgreSQL and workspace setup.
"""

from .dependencies import optional_api_key, require_api_key
from .init_service import AuthInitService  
from .service import AuthService
from .credential_service import CredentialService

__all__ = [
    "AuthInitService", 
    "AuthService", 
    "CredentialService",
    "optional_api_key", 
    "require_api_key"
]
