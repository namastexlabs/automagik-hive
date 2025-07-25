"""
Core authentication service for Automagik Hive.

Provides x-api-key validation and authentication logic.
"""

import os
import secrets
from typing import Optional
from .init_service import AuthInitService


class AuthService:
    """Core authentication service."""
    
    def __init__(self):
        # Initialize API key on startup
        self.init_service = AuthInitService()
        self.api_key = self.init_service.ensure_api_key()
        self.auth_disabled = os.getenv("HIVE_AUTH_DISABLED", "false").lower() == "true"
    
    async def validate_api_key(self, provided_key: Optional[str]) -> bool:
        """
        Validate provided API key against configured key.
        
        Args:
            provided_key: The API key to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if self.auth_disabled:
            return True  # Development bypass
        
        if not provided_key:
            return False
        
        if not self.api_key:
            raise ValueError("HIVE_API_KEY not properly initialized")
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(self.api_key, provided_key)
    
    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return not self.auth_disabled
    
    def get_current_key(self) -> Optional[str]:
        """Get current API key."""
        return self.api_key
    
    def regenerate_key(self) -> str:
        """Regenerate API key."""
        new_key = self.init_service.regenerate_key()
        self.api_key = new_key
        return new_key