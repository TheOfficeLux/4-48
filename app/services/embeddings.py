"""EmbeddingService: OpenAI text-embedding-3-small (1536 dims) with Redis cache."""

import asyncio
import hashlib

from app.config import get_settings
from app.constants import CACHE_EMBEDDING_TTL
from app.exceptions import LearningServiceUnavailableError
from app.redis_client import get_redis


class EmbeddingService:
    """OpenAI embeddings with Redis cache keyed by sha256(text)[:16]."""

    def __init__(self):
        self.settings = get_settings()
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self._client

    async def embed(self, text: str) -> list[float]:
        """Return 1536-dim embedding; use cache if present. Retries on 429, raises LearningServiceUnavailableError on quota/errors."""
        key_hex = hashlib.sha256(text.encode()).hexdigest()[:16]
        redis = get_redis()
        if redis:
            try:
                raw = await redis.get(f"embedding:{key_hex}")
                if raw:
                    import msgpack
                    return msgpack.unpackb(raw)
            except Exception:
                pass
        from openai import APIError, RateLimitError

        for attempt in range(3):
            try:
                response = await self.client.embeddings.create(
                    model=self.settings.embedding_model,
                    input=text,
                )
                vec = response.data[0].embedding
                if redis:
                    try:
                        import msgpack
                        await redis.set(f"embedding:{key_hex}", msgpack.packb(vec), ex=CACHE_EMBEDDING_TTL)
                    except Exception:
                        pass
                return vec
            except RateLimitError as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LearningServiceUnavailableError(
                    "Embedding service is temporarily unavailable (rate limit or quota). Please try again later.",
                    cause=e,
                ) from e
            except (APIError, Exception) as e:
                raise LearningServiceUnavailableError(
                    "Embedding service is temporarily unavailable. Please try again later.",
                    cause=e,
                ) from e
