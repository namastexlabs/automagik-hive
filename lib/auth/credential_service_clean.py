#!/usr/bin/env python3
"""
Clean Credential Service for Automagik Hive.

ARCHITECTURAL PRINCIPLE: This service ONLY validates and reads credentials.
It NEVER writes environment variables or generates .env files.

CLEAN ARCHITECTURE COMPLIANCE:
- Python applications read configuration, never write it
- All environment variables must exist in .env files created externally  
- Clear error messages when configuration is missing
- Type-safe configuration validation through Pydantic

This replaces the massive credential_service.py (1068+ lines) that violated
the architectural rule: ".env > docker compose yaml specific overrides, and THATS IT"

The old service inappropriately generated complete .env files with infrastructure
variables. This clean service respects boundaries and only validates existing configuration.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from lib.config.settings import get_settings, HiveSettings
from lib.logging import logger


class CleanCredentialService:
    """
    Read-only credential validation service that never writes environment variables.
    
    ARCHITECTURAL COMPLIANCE:
    - NEVER generates .env files (violates ".env > docker compose" rule)  
    - NEVER writes environment variables to any files
    - ONLY validates existing configuration through centralized settings
    - ONLY reads and validates credentials for service health checks
    - Clear error messages when required configuration is missing
    
    This service exists to:
    1. Validate that required credentials exist in .env files
    2. Provide connection information for service health checks  
    3. Validate credential format and security requirements
    4. Replace the massive credential_service.py that violated architecture
    """
    
    def __init__(self, project_root: Optional[Path] = None, env_file: Optional[Path] = None) -> None:
        """
        Initialize clean credential service.
        
        Args:
            project_root: Project root directory (defaults to current working directory)
            env_file: Path to environment file (defaults to .env in project root)
        """
        self.project_root = project_root or Path.cwd()
        self.env_file_path = env_file or (self.project_root / ".env")
        
        logger.debug(
            "Initialized clean credential service",
            project_root=str(self.project_root),
            env_file=str(self.env_file_path)
        )
    
    def validate_env_file_exists(self) -> bool:
        """
        Validate that required .env file exists.
        
        ARCHITECTURAL RULE: This method NEVER creates .env files.
        It only validates existence and provides clear error messages.
        
        Returns:
            True if .env file exists, False otherwise
        """
        exists = self.env_file_path.exists()
        
        if exists:
            logger.info("Environment file validation successful", file=str(self.env_file_path))
        else:
            logger.error(
                "Required .env file missing. Please create from .env.example or run manual setup.",
                file=str(self.env_file_path)
            )
        
        return exists
    
    def validate_database_credentials(self) -> Dict[str, Any]:
        """
        Validate database credentials from centralized settings.
        
        Uses centralized Pydantic settings for validation instead of
        scattered os.getenv() calls with hardcoded defaults.
        
        Returns:
            Dict with validation results and credential information
        """
        logger.debug("Validating database credentials through centralized settings")
        
        try:
            settings = get_settings()
            
            # Validate database URL format
            database_url = settings.hive_database_url
            parsed_url = urlparse(database_url)
            
            if not parsed_url.scheme.startswith('postgresql'):
                return {
                    'valid': False,
                    'error': f'Invalid database URL format: must use postgresql://, got {parsed_url.scheme}'
                }
            
            if not all([parsed_url.hostname, parsed_url.port, parsed_url.path]):
                return {
                    'valid': False, 
                    'error': 'Database URL missing required components (host, port, database)'
                }
            
            logger.info(
                "Database credentials validated successfully",
                host=parsed_url.hostname,
                port=parsed_url.port,
                database=parsed_url.path[1:]  # Remove leading slash
            )
            
            return {
                'valid': True,
                'database_url': database_url,
                'host': parsed_url.hostname,
                'port': parsed_url.port,
                'database': parsed_url.path[1:],  # Remove leading slash
                'user': parsed_url.username
            }
            
        except Exception as e:
            logger.error(f"Database credential validation failed: {e}")
            return {
                'valid': False,
                'error': f'Database credential validation error: {str(e)}'
            }
    
    def validate_api_credentials(self) -> Dict[str, Any]:
        """
        Validate API credentials from centralized settings.
        
        Uses centralized Pydantic settings for validation instead of
        scattered hardcoded defaults.
        
        Returns:
            Dict with validation results and API credential information
        """
        logger.debug("Validating API credentials through centralized settings")
        
        try:
            settings = get_settings()
            
            # Validate API key format (already validated by Pydantic)
            api_key = settings.hive_api_key
            if not api_key.startswith('hive_'):
                return {
                    'valid': False,
                    'error': 'API key format invalid: must start with "hive_" prefix'
                }
            
            if len(api_key) < 37:  # hive_ (5) + minimum token (32)
                return {
                    'valid': False,
                    'error': 'API key format invalid: must be at least 37 characters'
                }
            
            # Validate API port (already validated by Pydantic)
            api_port = settings.hive_api_port
            if not (1024 <= api_port <= 65535):
                return {
                    'valid': False,
                    'error': f'API port out of valid range: must be 1024-65535, got {api_port}'
                }
            
            logger.info(
                "API credentials validated successfully", 
                api_port=api_port,
                key_length=len(api_key)
            )
            
            return {
                'valid': True,
                'api_key': api_key,
                'api_port': api_port,
                'api_host': settings.hive_api_host
            }
            
        except Exception as e:
            logger.error(f"API credential validation failed: {e}")
            return {
                'valid': False,
                'error': f'API credential validation error: {str(e)}'
            }
    
    def validate_all_credentials(self) -> Dict[str, Any]:
        """
        Validate all credentials comprehensively.
        
        Provides complete validation report for service health checks
        and startup validation.
        
        Returns:
            Dict with comprehensive validation results
        """
        logger.info("Starting comprehensive credential validation")
        
        # Check .env file exists first
        env_file_exists = self.validate_env_file_exists()
        
        if not env_file_exists:
            return {
                'valid': False,
                'env_file_exists': False,
                'errors': ['Required .env file missing']
            }
        
        # Validate database credentials
        db_validation = self.validate_database_credentials()
        
        # Validate API credentials  
        api_validation = self.validate_api_credentials()
        
        # Overall validation result
        overall_valid = db_validation['valid'] and api_validation['valid']
        
        result = {
            'valid': overall_valid,
            'env_file_exists': env_file_exists,
            'database': db_validation,
            'api': api_validation
        }
        
        # Collect any errors
        errors = []
        if not db_validation['valid']:
            errors.append(f"Database: {db_validation.get('error', 'Unknown error')}")
        if not api_validation['valid']:
            errors.append(f"API: {api_validation.get('error', 'Unknown error')}")
        
        if errors:
            result['errors'] = errors
        
        if overall_valid:
            logger.info("All credentials validated successfully")
        else:
            logger.error("Credential validation failed", errors=errors)
        
        return result
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection information for service health checks.
        
        SECURITY NOTE: This method does NOT expose passwords or sensitive data.
        It only provides connection endpoints for health check purposes.
        
        Returns:
            Dict with connection information (no passwords)
        """
        logger.debug("Extracting connection information for health checks")
        
        try:
            settings = get_settings()
            
            # Parse database URL for connection info (without password)
            parsed_url = urlparse(settings.hive_database_url)
            
            connection_info = {
                'database': {
                    'host': parsed_url.hostname,
                    'port': parsed_url.port,
                    'user': parsed_url.username,
                    'database': parsed_url.path[1:] if parsed_url.path else None,
                    # SECURITY: Password intentionally excluded from connection info
                },
                'api': {
                    'host': settings.hive_api_host,
                    'port': settings.hive_api_port
                }
            }
            
            logger.debug("Connection information extracted successfully")
            return connection_info
            
        except Exception as e:
            logger.error(f"Failed to extract connection information: {e}")
            return {
                'database': {
                    'error': f'Failed to parse database connection: {str(e)}'
                },
                'api': {
                    'error': f'Failed to get API connection info: {str(e)}'
                }
            }
    
    def check_configuration_health(self) -> Dict[str, Any]:
        """
        Comprehensive configuration health check.
        
        Suitable for service startup validation and health monitoring.
        Replaces the complex credential generation logic with simple validation.
        
        Returns:
            Dict with health check results and recommendations
        """
        logger.info("Starting configuration health check")
        
        # Validate all credentials
        validation_result = self.validate_all_credentials()
        
        # Get connection info for monitoring
        connection_info = self.get_connection_info()
        
        # Calculate overall health
        health_status = "healthy" if validation_result['valid'] else "unhealthy"
        
        health_check = {
            'status': health_status,
            'timestamp': logger.get_timestamp() if hasattr(logger, 'get_timestamp') else 'unknown',
            'validation': validation_result,
            'connections': connection_info
        }
        
        # Add recommendations for unhealthy configurations
        if health_status == "unhealthy":
            recommendations = [
                "Ensure .env file exists and contains all required variables",
                "Check that HIVE_DATABASE_URL follows postgresql+psycopg:// format", 
                "Verify HIVE_API_KEY starts with 'hive_' and is at least 37 characters",
                "Confirm HIVE_API_PORT is in valid range (1024-65535)",
                "See .env.example for reference configuration"
            ]
            health_check['recommendations'] = recommendations
        
        logger.info(f"Configuration health check complete: {health_status}")
        return health_check