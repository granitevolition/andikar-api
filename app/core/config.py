from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Document Processing API"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # OpenAI Configuration
    OPENAI_API_KEYS: List[str] = []

    # Processing Configuration
    MAX_REQUESTS_PER_MINUTE: int = 900
    PROCESSING_BATCH_SIZE: int = 5
    SELECT_BEST_SENTENCE: bool = True

    # Model Configuration
    GPT_MODEL: str = "ft:gpt-3.5-turbo-0125:personal::9hpCfvVt"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()