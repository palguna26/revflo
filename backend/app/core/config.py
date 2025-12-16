from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Mongo / persistence
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    mongodb_db: str = Field("revflo", alias="MONGODB_DB")

    # API
    api_prefix: str = "/api"

    # GitHub OAuth
    github_client_id: str = Field(..., alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(..., alias="GITHUB_CLIENT_SECRET")
    github_redirect_uri: str = Field(..., alias="GITHUB_REDIRECT_URI")

    # Frontend + cookies
    frontend_url: str = Field(..., alias="FRONTEND_URL")

    # Groq LLM
    groq_api_key: str = Field(..., alias="GROQ_API_KEY")

    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    environment: str = Field("production", alias="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
