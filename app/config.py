"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/adaptive_learning"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google AI Studio (embeddings + chat) — set GOOGLE_API_KEY in .env
    google_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    llm_model: str = "gemini-2.0-flash"

    # JWT
    jwt_secret: str = "change-me-in-production-minimum-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 480
    jwt_refresh_expire_days: int = 30

    # RAG
    rag_retrieve_top_k: int = 20
    rag_rerank_top_n: int = 5
    llm_max_tokens: int = 700
    llm_temperature: float = 0.35

    # Usage limits (shown in UI; approximate free-tier limits)
    llm_daily_limit: int = 60
    embed_daily_limit: int = 500


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
