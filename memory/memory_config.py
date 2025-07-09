"""
Memory Configuration for PagBank Multi-Agent System
Agent C: Memory System Foundation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class MemoryConfig:
    """Configuration for PagBank Memory System"""
    
    # Database configuration
    db_file: str = "data/pagbank.db"
    table_name: str = "pagbank_memories"
    
    # Memory settings
    enable_user_memories: bool = True
    enable_session_summaries: bool = True
    enable_agentic_memory: bool = True
    
    # LLM configuration for memory operations
    memory_model: str = "claude-sonnet-4-20250514"
    
    # Pattern detection settings
    pattern_detection_enabled: bool = True
    pattern_similarity_threshold: float = 0.8
    pattern_update_frequency: int = 10  # Updates every N interactions
    
    # Memory retention settings
    max_user_memories: int = 100
    max_session_memories: int = 50
    memory_cleanup_interval: int = 1000  # Clean up every N interactions
    
    # Session management
    session_timeout_minutes: int = 120
    auto_save_interval: int = 5  # Save every N interactions
    
    # Performance settings
    async_processing: bool = True
    batch_size: int = 10
    
    @classmethod
    def from_database_config(cls, db_config) -> 'MemoryConfig':
        """Create memory config from database config"""
        return cls(
            db_file=db_config.url.replace("postgresql+psycopg2://", "data/pagbank.db"),
            table_name="pagbank_memories"
        )
    
    def get_db_path(self) -> Path:
        """Get database file path, creating directory if needed"""
        db_path = Path(self.db_file)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            'db_file': self.db_file,
            'table_name': self.table_name,
            'enable_user_memories': self.enable_user_memories,
            'enable_session_summaries': self.enable_session_summaries,
            'enable_agentic_memory': self.enable_agentic_memory,
            'memory_model': self.memory_model,
            'pattern_detection_enabled': self.pattern_detection_enabled,
            'pattern_similarity_threshold': self.pattern_similarity_threshold,
            'pattern_update_frequency': self.pattern_update_frequency,
            'max_user_memories': self.max_user_memories,
            'max_session_memories': self.max_session_memories,
            'memory_cleanup_interval': self.memory_cleanup_interval,
            'session_timeout_minutes': self.session_timeout_minutes,
            'auto_save_interval': self.auto_save_interval,
            'async_processing': self.async_processing,
            'batch_size': self.batch_size
        }


# Default configuration instance
DEFAULT_MEMORY_CONFIG = MemoryConfig()


# Memory configuration for different environments
def get_memory_config(environment: str = "development") -> MemoryConfig:
    """Get memory configuration for specific environment"""
    
    configs = {
        "development": MemoryConfig(
            db_file="data/pagbank.db",
            table_name="pagbank_memories_dev",
            async_processing=False,  # Sync for easier debugging
            pattern_update_frequency=5,  # More frequent updates for testing
        ),
        
        "testing": MemoryConfig(
            db_file="data/pagbank.db",
            table_name="pagbank_memories_test",
            enable_user_memories=True,
            enable_session_summaries=False,  # Simplified for testing
            async_processing=False,
            max_user_memories=10,  # Smaller limits for testing
            max_session_memories=5,
        ),
        
        "production": MemoryConfig(
            db_file="data/pagbank.db",
            table_name="pagbank_memories",
            enable_user_memories=True,
            enable_session_summaries=True,
            enable_agentic_memory=True,
            async_processing=True,
            max_user_memories=1000,
            max_session_memories=500,
            memory_cleanup_interval=10000,
        )
    }
    
    return configs.get(environment, DEFAULT_MEMORY_CONFIG)


def validate_memory_config(config: MemoryConfig) -> Dict[str, Any]:
    """Validate memory configuration"""
    validation_results = {
        'valid': True,
        'issues': [],
        'warnings': []
    }
    
    # Check database file path
    try:
        db_path = config.get_db_path()
        if not db_path.parent.exists():
            validation_results['warnings'].append(f"Database directory will be created: {db_path.parent}")
    except Exception as e:
        validation_results['valid'] = False
        validation_results['issues'].append(f"Invalid database path: {e}")
    
    # Check memory limits
    if config.max_user_memories < 1:
        validation_results['valid'] = False
        validation_results['issues'].append("max_user_memories must be at least 1")
    
    if config.max_session_memories < 1:
        validation_results['valid'] = False
        validation_results['issues'].append("max_session_memories must be at least 1")
    
    # Check thresholds
    if not (0.0 <= config.pattern_similarity_threshold <= 1.0):
        validation_results['valid'] = False
        validation_results['issues'].append("pattern_similarity_threshold must be between 0.0 and 1.0")
    
    # Check intervals
    if config.pattern_update_frequency < 1:
        validation_results['valid'] = False
        validation_results['issues'].append("pattern_update_frequency must be at least 1")
    
    if config.auto_save_interval < 1:
        validation_results['valid'] = False
        validation_results['issues'].append("auto_save_interval must be at least 1")
    
    # Check session timeout
    if config.session_timeout_minutes < 1:
        validation_results['valid'] = False
        validation_results['issues'].append("session_timeout_minutes must be at least 1")
    
    return validation_results