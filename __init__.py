"""PagBank Multi-Agent System - Financial Assistant with Portuguese Support."""

__version__ = "0.1.0"
__author__ = "Automagik Genie"
__email__ = "genie@namastex.ai"

from .config import db_config, model_config, settings
from .config.database import get_db_session, health_check, init_database
from .config.models import get_claude_client, get_model_params, validate_models
from .config.settings import PROJECT_ROOT, get_setting, get_team_names

__all__ = [
    "settings",
    "model_config", 
    "db_config",
    "init_database",
    "get_db_session",
    "health_check",
    "get_claude_client",
    "get_model_params",
    "validate_models",
    "get_setting",
    "get_team_names",
    "PROJECT_ROOT",
]