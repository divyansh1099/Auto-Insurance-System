"""
Response caching utilities.
"""
from functools import wraps
from typing import Optional, Callable, Any
from fastapi import Request
import hashlib
import json
import structlog

from app.services.redis_client import get_redis_client

logger = structlog.get_logger()


def cache_response(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache API responses in Redis.
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key_parts = [key_prefix, func.__name__]
            
            # Add request path if available
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                cache_key_parts.append(request.url.path)
                # Include query parameters
                if request.query_params:
                    cache_key_parts.append(str(sorted(request.query_params.items())))
            
            # Add kwargs (excluding db session)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'db'}
            if filtered_kwargs:
                cache_key_parts.append(json.dumps(filtered_kwargs, sort_keys=True, default=str))
            
            cache_key = ":".join(cache_key_parts)
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
            full_cache_key = f"response_cache:{cache_key_hash}"
            
            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_response = redis_client.get(full_cache_key)
                    if cached_response:
                        logger.debug("cache_hit", key=full_cache_key)
                        return json.loads(cached_response)
                except Exception as e:
                    logger.warning("cache_read_error", error=str(e))
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if redis_client:
                try:
                    redis_client.setex(
                        full_cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    logger.debug("cache_set", key=full_cache_key, ttl=ttl)
                except Exception as e:
                    logger.warning("cache_write_error", error=str(e))
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate cache entries matching a pattern.
    
    Args:
        pattern: Cache key pattern (e.g., "response_cache:driver:*")
    """
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        # Note: Redis SCAN is needed for pattern matching in production
        # For now, we'll use a simple approach
        keys = redis_client.keys(f"response_cache:{pattern}")
        if keys:
            redis_client.delete(*keys)
            logger.info("cache_invalidated", pattern=pattern, count=len(keys))
    except Exception as e:
        logger.warning("cache_invalidation_error", error=str(e))

