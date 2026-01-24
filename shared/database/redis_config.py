"""Redis configuration and connection management."""

from typing import Optional

import redis

from shared.config.settings import settings
from shared.logging.config import get_logger

logger = get_logger(__name__)

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None


def get_redis_pool() -> redis.ConnectionPool:
    """Get or create Redis connection pool."""
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis.url,
            decode_responses=settings.redis.decode_responses,
            socket_connect_timeout=settings.redis.socket_connect_timeout,
            socket_timeout=settings.redis.socket_timeout,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info("Redis connection pool created", url=settings.redis.url)

    return _redis_pool


def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    return redis.Redis(connection_pool=get_redis_pool())


def test_redis_connection() -> bool:
    """Test Redis connection."""
    try:
        client = get_redis()
        client.ping()
        logger.info("Redis connection test successful")
        return True
    except Exception as e:
        logger.error("Redis connection test failed", error=str(e))
        return False


class RedisCache:
    """Redis cache utility class."""

    def __init__(self):
        self.client = get_redis()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error("Redis get failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            return self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error("Redis set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error("Redis delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error("Redis exists failed", key=key, error=str(e))
            return False


# Global cache instance
cache = RedisCache()
