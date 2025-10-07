from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional, Union
import json


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )
    
    PROJECT_NAME: str = "Fuschia API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_CONNECTION_URL: Optional[str] = None
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    @property
    def neo4j_uri(self) -> str:
        # Prioritize NEO4J_URI (used in Railway), fallback to NEO4J_CONNECTION_URL
        return self.NEO4J_URI or self.NEO4J_CONNECTION_URL or "bolt://localhost:7687"

    @property
    def neo4j_username(self) -> str:
        return self.NEO4J_USER or self.NEO4J_USERNAME
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fall back to comma-separated
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    # Logging
    LOG_LEVEL: str = "INFO"

    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None

    # PostgreSQL (can use either DATABASE_URL or individual params)
    DATABASE_URL: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_PRISMA_URL: Optional[str] = None

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None


settings = Settings()