# Redis client for caching, token blacklist, and message broker
import redis.asyncio as redis
from src.core.config import settings

# Async Redis client with decode_responses for string values
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def init_redis():
    """Initialize Redis connection on startup"""
    await redis_client.ping()

async def close_redis():
    """Close Redis connection on shutdown"""
    await redis_client.close()
