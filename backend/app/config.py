import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Amulate AI Car Consultant API"
    environment: str = "development"
    debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    
    # Agent & LLM
    agent_mode: str = "mock" # "mock" or "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Storage
    storage_backend: str = "auto" # "auto", "mongodb", "json"
    mongodb_uri: str = "mongodb://localhost:27017/car_consultant"
    
    # Observability
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
