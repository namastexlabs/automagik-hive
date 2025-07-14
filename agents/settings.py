from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    """Agent settings para PagBank Multi-Agent System.

    Reference: https://pydantic-docs.helpmanual.io/usage/settings/
    """

    # OpenAI Models
    gpt_4: str = "gpt-4o"
    gpt_4o_mini: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    default_max_completion_tokens: int = 16000
    default_temperature: float = 0

    # Anthropic Models
    claude_3_7_sonnet: str = "claude-3-7-sonnet-latest"
    claude_4_sonnet: str = "claude-sonnet-4-20250514"

    # PagBank-specific settings
    default_language: str = "pt-BR"
    debug_mode: bool = False
    enable_memory: bool = True
    
    # Agent configuration
    max_context_tokens: int = 128000
    response_timeout: int = 30
    
    # Knowledge base settings
    knowledge_refresh_interval: int = 60  # seconds
    enable_csv_hot_reload: bool = True


# Create an AgentSettings object
agent_settings = AgentSettings()