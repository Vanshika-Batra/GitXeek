from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = Field(default="GitXeek Backend")
    DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = Field(default="/api/v1")

    DATABASE_URL: str 

    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
