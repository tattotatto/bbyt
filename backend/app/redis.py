import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

redis_client: aioredis.Redis | None = None


async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency: yields the Redis client."""
    if redis_client is None:
        await init_redis()
    return redis_client


async def close_redis():
    if redis_client:
        await redis_client.close()
