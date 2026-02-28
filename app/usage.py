"""Track and return API usage (LLM + embeddings) for UI limits display."""

from datetime import datetime, timezone

from app.config import get_settings
from app.redis_client import get_redis

USAGE_KEY_LLM = "usage:llm"
USAGE_KEY_EMBED = "usage:embed"
TTL_DAYS = 2


def _date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


async def record_llm_use() -> None:
    redis = get_redis()
    if not redis:
        return
    key = f"{USAGE_KEY_LLM}:{_date()}"
    try:
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, 86400 * TTL_DAYS)
    except Exception:
        pass


async def record_embed_use() -> None:
    redis = get_redis()
    if not redis:
        return
    key = f"{USAGE_KEY_EMBED}:{_date()}"
    try:
        n = await redis.incr(key)
        if n == 1:
            await redis.expire(key, 86400 * TTL_DAYS)
    except Exception:
        pass


async def get_usage() -> dict:
    """Return { date, llm_requests, llm_daily_limit, embed_requests, embed_daily_limit }."""
    settings = get_settings()
    today = _date()
    redis = get_redis()
    llm_requests = 0
    embed_requests = 0
    if redis:
        try:
            raw_llm = await redis.get(f"{USAGE_KEY_LLM}:{today}")
            llm_requests = int(raw_llm.decode()) if raw_llm else 0
        except Exception:
            pass
        try:
            raw_embed = await redis.get(f"{USAGE_KEY_EMBED}:{today}")
            embed_requests = int(raw_embed.decode()) if raw_embed else 0
        except Exception:
            pass
    return {
        "date": today,
        "llm_requests": llm_requests,
        "llm_daily_limit": settings.llm_daily_limit,
        "embed_requests": embed_requests,
        "embed_daily_limit": settings.embed_daily_limit,
    }
