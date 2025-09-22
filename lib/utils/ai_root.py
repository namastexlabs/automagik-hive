from pathlib import Path
from typing import Union
import os

from lib.config.settings import HiveSettings


def resolve_ai_root(explicit_path: Union[str, Path, None], settings: HiveSettings) -> Path:
    """
    Resolve the AI root directory path following precedence rules.
    
    Precedence:
    1. explicit_path (CLI argument)
    2. HIVE_AI_ROOT environment variable
    3. settings.hive_ai_root (defaults to "ai")
    
    Validates that the resolved path exists and contains required directories:
    - agents/
    - teams/
    - workflows/
    
    Args:
        explicit_path: Explicit path from CLI or None
        settings: Application settings instance
        
    Returns:
        Resolved Path to AI root directory
        
    Raises:
        ValueError: If resolved path does not exist or missing required subdirectories
    """
    # Step 1: Explicit path takes highest precedence
    if explicit_path is not None:
        if isinstance(explicit_path, str):
            candidate_path = Path(explicit_path).resolve()
        else:
            candidate_path = explicit_path.resolve()
        print(f"Using explicit AI root: {candidate_path}")
    else:
        # Step 2: Environment variable
        env_path = os.getenv("HIVE_AI_ROOT")
        if env_path:
            candidate_path = Path(env_path).resolve()
            print(f"Using HIVE_AI_ROOT env: {candidate_path}")
        else:
            # Step 3: Settings default
            candidate_path = settings.project_root / settings.hive_ai_root
            print(f"Using default AI root: {candidate_path}")
    
    # Validate path exists
    if not candidate_path.exists():
        raise ValueError(
            f"AI root directory does not exist: {candidate_path}\n"
            f"Please ensure the path is correct or create the directory."
        )
    
    # Validate required subdirectories
    required_dirs = ["agents", "teams", "workflows"]
    missing_dirs = [d for d in required_dirs if not (candidate_path / d).exists()]
    
    if missing_dirs:
        raise ValueError(
            f"AI root {candidate_path} missing required directories: {', '.join(missing_dirs)}\n"
            f"Required: agents/, teams/, workflows/"
        )
    
    print(f"✅ AI root validated: {candidate_path}")
    return candidate_path