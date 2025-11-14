"""
Response caching utilities.
"""
from functools import wraps
from typing import Optional, Callable, Any
from fastapi import Request
import hashlib
import json
import structlog
import time

from app.services.redis_client import get_redis_client
from app.utils.metrics import (
    cache_hits_total,
    cache_misses_total,
    cache_operation_duration_seconds
)

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
                    cache_start_time = time.time()
                    cached_response = redis_client.get(full_cache_key)
                    cache_duration = time.time() - cache_start_time

                    if cached_response:
                        logger.debug("cache_hit", key=full_cache_key)
                        # Record cache hit metrics
                        cache_hits_total.labels(
                            cache_type="response",
                            cache_key_pattern=key_prefix
                        ).inc()
                        cache_operation_duration_seconds.labels(
                            operation="get",
                            cache_type="response"
                        ).observe(cache_duration)
                        return json.loads(cached_response)
                    else:
                        # Record cache miss metrics
                        cache_misses_total.labels(
                            cache_type="response",
                            cache_key_pattern=key_prefix
                        ).inc()
                        cache_operation_duration_seconds.labels(
                            operation="get",
                            cache_type="response"
                        ).observe(cache_duration)
                except Exception as e:
                    logger.warning("cache_read_error", error=str(e))
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            if redis_client:
                try:
                    set_start_time = time.time()
                    redis_client.setex(
                        full_cache_key,
                        ttl,
                        json.dumps(result, default=str)
                    )
                    set_duration = time.time() - set_start_time

                    logger.debug("cache_set", key=full_cache_key, ttl=ttl)
                    # Record cache set metrics
                    cache_operation_duration_seconds.labels(
                        operation="set",
                        cache_type="response"
                    ).observe(set_duration)
                except Exception as e:
                    logger.warning("cache_write_error", error=str(e))
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate cache entries matching a pattern.
    Uses SCAN for production-safe non-blocking operation.

    Args:
        pattern: Cache key pattern (e.g., "driver:*")
    """
    redis_client = get_redis_client()
    if not redis_client:
        return

    try:
        # Use SCAN instead of KEYS for production-safe operation
        # SCAN is non-blocking and won't freeze Redis
        cursor = 0
        deleted_count = 0
        match_pattern = f"response_cache:{pattern}"

        while True:
            # Scan returns (cursor, [keys])
            cursor, keys = redis_client.scan(
                cursor=cursor,
                match=match_pattern,
                count=100  # Process 100 keys at a time
            )

            if keys:
                redis_client.delete(*keys)
                deleted_count += len(keys)

            # cursor=0 means we've scanned all keys
            if cursor == 0:
                break

        if deleted_count > 0:
            logger.info("cache_invalidated", pattern=pattern, count=deleted_count)
    except Exception as e:
        logger.warning("cache_invalidation_error", error=str(e))

