"""
Redis Caching Decorator for TRAMOS
Provides caching functionality for expensive analytics queries

Usage:
    from app.services.cache_decorator import cache_result

    @cache_result(expire_seconds=300, prefix="analytics")
    async def get_analytics(start_date, end_date):
        # Expensive query here
        return result
"""

import json
import hashlib
import functools
import logging
from typing import Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Global cache instance
_redis_client = None


def get_redis_client():
    """Get or create Redis client"""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        from app.config import settings

        if settings.REDIS_URL:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            _redis_client.ping()
            logger.info("Redis caching enabled")
            return _redis_client
        else:
            logger.debug("Redis not configured, caching disabled")
            return None
    except Exception as e:
        logger.debug(f"Redis connection failed: {e}")
        return None


def cache_result(
    expire_seconds: int = 300,
    prefix: str = "cache",
    skip_if_none: bool = True
):
    """
    Decorator for caching async function results in Redis.

    Args:
        expire_seconds: Cache TTL in seconds (default: 5 minutes)
        prefix: Cache key prefix for namespacing
        skip_if_none: If True, don't cache None results

    Usage:
        @cache_result(expire_seconds=300, prefix="analytics")
        async def get_dashboard_stats(start_date, end_date):
            # Expensive computation
            return result
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name, args, and kwargs
            key_parts = [
                prefix,
                func.__name__,
                str(args) if args else "",
                str(sorted(kwargs.items())) if kwargs else "",
            ]
            key_string = ":".join(key_parts)

            # Create hash if key is too long
            if len(key_string) > 200:
                key_hash = hashlib.md5(key_string.encode()).hexdigest()
                cache_key = f"{prefix}:{func.__name__}:{key_hash}"
            else:
                cache_key = key_string.replace(" ", "").replace("'", '"')

            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger.debug(f"Cache HIT: {cache_key}")
                        return json.loads(cached)
                    logger.debug(f"Cache MISS: {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")

            # Execute function
            try:
                result = await func(*args, **kwargs)

                # Cache the result
                if redis_client and result is not None:
                    try:
                        redis_client.setex(
                            cache_key,
                            expire_seconds,
                            json.dumps(result, default=str)
                        )
                        logger.debug(f"Cached result: {cache_key}")
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")

                return result

            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                raise

        return wrapper
    return decorator


def cache_sync(
    expire_seconds: int = 300,
    prefix: str = "cache"
):
    """
    Sync version of cache decorator for non-async functions.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            key_parts = [prefix, func.__name__, str(args), str(sorted(kwargs.items()))]
            key_string = ":".join(key_parts)

            if len(key_string) > 200:
                key_hash = hashlib.md5(key_string.encode()).hexdigest()
                cache_key = f"{prefix}:{func.__name__}:{key_hash}"
            else:
                cache_key = key_string.replace(" ", "").replace("'", '"')

            # Try cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger.debug(f"Cache HIT: {cache_key}")
                        return json.loads(cached)
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")

            # Execute
            try:
                result = func(*args, **kwargs)

                if redis_client and result is not None:
                    try:
                        redis_client.setex(
                            cache_key,
                            expire_seconds,
                            json.dumps(result, default=str)
                        )
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")

                return result

            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                raise

        return wrapper
    return decorator


def invalidate_cache(prefix: str = None, pattern: str = None):
    """
    Invalidate cache entries.

    Args:
        prefix: Invalidate all keys with this prefix
        pattern: Invalidate keys matching this pattern (Redis SCAN pattern)

    Usage:
        invalidate_cache(prefix="analytics")
        invalidate_cache(pattern="*user*")
    """
    redis_client = get_redis_client()
    if not redis_client:
        return

    try:
        if prefix:
            pattern = f"{prefix}:*"
        elif pattern is None:
            pattern = "*"

        deleted = 0
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                redis_client.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break

        logger.info(f"Invalidated {deleted} cache entries matching: {pattern}")
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")


class CacheManager:
    """Cache manager for explicit caching control"""

    def __init__(self):
        self.redis = get_redis_client()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None

        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def set(self, key: str, value: Any, expire_seconds: int = 300) -> bool:
        """Set value in cache"""
        if not self.redis:
            return False

        try:
            self.redis.setex(key, expire_seconds, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis:
            return False

        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.redis:
            return {"enabled": False}

        try:
            info = self.redis.info("stats")
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = max(1, hits + misses)
            return {
                "enabled": True,
                "hits": hits,
                "misses": misses,
                "hit_rate": round(hits / total * 100, 2),
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# Singleton instance
cache_manager = CacheManager()
