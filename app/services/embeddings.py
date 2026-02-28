"""EmbeddingService: Google AI Studio gemini-embedding-001 (768 dims) with Redis cache."""

import asyncio
import hashlib

from app.config import get_settings
from app.constants import CACHE_EMBEDDING_TTL
from app.exceptions import LearningServiceUnavailableError
from app.redis_client import get_redis
from app.usage import record_embed_use


class EmbeddingService:
    """Google AI Studio embeddings with Redis cache keyed by sha256(text)[:16]."""

    def __init__(self):
        self.settings = get_settings()

    async def embed(self, text: str) -> list[float]:
        """Return 768-dim embedding (Google); use cache if present. Retries on 429, raises LearningServiceUnavailableError on quota/errors."""
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

        from google import genai
        from google.genai.types import EmbedContentConfig

        config = EmbedContentConfig(output_dimensionality=768)
        for attempt in range(3):
            # New client per attempt: exiting "async with client.aio" closes the aio client, so reuse would raise "client has been closed"
            client = genai.Client(api_key=self.settings.google_api_key)
            try:
                async with client.aio as aio_client:
                    result = await aio_client.models.embed_content(
                        model=self.settings.embedding_model,
                        contents=text,
                        config=config,
                    )
                if not result.embeddings:
                    raise LearningServiceUnavailableError("Embedding returned empty.", cause=None) from None
                emb = result.embeddings[0]
                vec = list(getattr(emb, "values", emb))
                if not vec:
                    raise LearningServiceUnavailableError(
                        "Embedding service returned empty result.",
                        cause=None,
                    ) from None
                if redis:
                    try:
                        import msgpack

                        await redis.set(
                            f"embedding:{key_hex}",
                            msgpack.packb(vec),
                            ex=CACHE_EMBEDDING_TTL,
                        )
                    except Exception:
                        pass
                await record_embed_use()
                return vec
            except LearningServiceUnavailableError:
                raise
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate" in err_str or "quota" in err_str:
                    if attempt < 2:
                        await asyncio.sleep(2**attempt)
                        continue
                raise LearningServiceUnavailableError(
                    "Embedding service is temporarily unavailable. Please try again later.",
                    cause=e,
                ) from e
