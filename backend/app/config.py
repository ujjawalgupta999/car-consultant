import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices

class Settings(BaseSettings):
    app_name: str = "Amulate AI Car Consultant API"
    environment: str = "development"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    
    # Agent & LLM
    agent_mode: str = "openai" # "mock" or "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Storage
    storage_backend: str = "auto" # "auto", "mongodb", "json"
    mongodb_uri: str = "mongodb://localhost:27017/car_consultant"
    mongodb_db_name: str = "car_consultant"
    
    # Observability (Langfuse)
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = Field(
        default="https://us.cloud.langfuse.com",
        validation_alias=AliasChoices("langfuse_host", "langfuse_base_url", "LANGFUSE_HOST", "LANGFUSE_BASE_URL")
    )
    langfuse_base_url: Optional[str] = None

    model_config = SettingsConfigDict(env_file=(".env", "../.env", "backend/.env"), extra="allow")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_openai_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))

    @property
    def is_langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def effective_langfuse_host(self) -> str:
        return self.langfuse_base_url or self.langfuse_host or "https://us.cloud.langfuse.com"

settings = Settings()

