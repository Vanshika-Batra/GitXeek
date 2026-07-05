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

    SECRET_KEY: str
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    GITHUB_CLIENT_ID: str = Field(default="")
    GITHUB_CLIENT_SECRET: str = Field(default="")
    GITHUB_REDIRECT_URI: str = Field(default="http://localhost:8000/api/v1/auth/github/callback")
    GITHUB_OAUTH_SCOPES: str = Field(default="repo read:user user:email")

    REPOS_CLONE_DIR: str = Field(default="/tmp/gitxeek/repos")
    FRONTEND_URL: str = Field(default="http://localhost:3000")

    COGNEE_SERVICE_URL: str
    COGNEE_API_KEY: str

    LLM_API_KEY: str
    LLM_PROVIDER: str
    LLM_MODEL: str


    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
