"""Redis connection utility â€” shared across API, realtime, and Celery modules."""

import os

import redis.asyncio as aioredis


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)


_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get a Redis connection from the pool."""

    global _redis_pool

    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            REDIS_URL,
            decode_responses=True,
        )

    return _redis_pool


async def close_redis() -> None:
    """Close Redis pool gracefully."""

    global _redis_pool

    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None