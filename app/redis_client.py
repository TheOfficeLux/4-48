"""Redis client (lazy singleton)."""

from typing import Any

_redis: Any = None


def get_redis():
    """Return Redis client; None if not configured or connection failed."""
    global _redis
    if _redis is not None:
        return _redis
    try:
        from redis.asyncio import Redis
        from app.config import get_settings
        url = get_settings().redis_url
        _redis = Redis.from_url(url, decode_responses=False)
        return _redis
    except Exception:
        return None


async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
