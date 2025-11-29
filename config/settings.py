from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )
    # LLM Configuration
    openai_api_key: str
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    
    # Vector Store
    vector_store_path: str = "./data/vectorstore"
    embeddings_model: str = "text-embedding-3-small"
    
    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # MCP Configuration
    mcp_server_url: Optional[str] = None
    mcp_timeout: int = 30
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_enabled: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60


settings = Settings()
