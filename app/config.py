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

    # OpenAI (embeddings)
    openai_api_key: str = ""

    # LLM for /ask: "openai" or "mistral"
    llm_provider: str = "mistral"
    llm_model: str = "mistral-small-latest"
    mistral_api_key: str = ""

    # OpenAI (only used for embeddings and when llm_provider=openai)
    embedding_model: str = "text-embedding-3-small"

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

    # State encoder
    state_encoder_model: str = "all-MiniLM-L6-v2"

    # Logging
    log_level: str = "INFO"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
