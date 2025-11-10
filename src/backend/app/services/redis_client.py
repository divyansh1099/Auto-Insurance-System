"""
Redis client for caching and feature store.
"""
import json
import redis
from typing import Optional, Dict, Any
from datetime import timedelta, datetime
import structlog

from app.config import get_settings
from app.utils.metrics import (
    redis_operations_total,
    redis_operation_duration_seconds
)
import time

logger = structlog.get_logger()
settings = get_settings()

# Global Redis connection
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client with connection pooling."""
    global _redis_client
    
    if _redis_client is None:
        try:
            # Use connection pool for better performance
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=True,
                retry_on_timeout=True
            )
            _redis_client = redis.Redis(connection_pool=pool)
            # Test connection
            _redis_client.ping()
            logger.info("redis_connected", host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        except Exception as e:
            logger.warning("redis_connection_failed", error=str(e))
            # Return None if connection fails
            _redis_client = None
    
    return _redis_client


def cache_risk_score(driver_id: str, risk_score: float, ttl: int = 3600):
    """Cache risk score for a driver."""
    client = get_redis_client()
    if not client:
        return
    
    start_time = time.time()
    try:
        key = f"risk_score:{driver_id}"
        client.setex(key, ttl, json.dumps({
            'risk_score': risk_score,
            'cached_at': str(datetime.utcnow())
        }))
        redis_operations_total.labels(operation='set', status='success').inc()
        duration = time.time() - start_time
        redis_operation_duration_seconds.labels(operation='set').observe(duration)
        logger.debug("risk_score_cached", driver_id=driver_id, risk_score=risk_score)
    except Exception as e:
        redis_operations_total.labels(operation='set', status='failed').inc()
        logger.warning("cache_risk_score_failed", error=str(e))


def get_cached_risk_score(driver_id: str) -> Optional[float]:
    """Get cached risk score for a driver."""
    client = get_redis_client()
    if not client:
        return None
    
    start_time = time.time()
    try:
        key = f"risk_score:{driver_id}"
        data = client.get(key)
        if data:
            parsed = json.loads(data)
            redis_operations_total.labels(operation='get', status='success').inc()
            duration = time.time() - start_time
            redis_operation_duration_seconds.labels(operation='get').observe(duration)
            return parsed.get('risk_score')
        redis_operations_total.labels(operation='get', status='miss').inc()
    except Exception as e:
        redis_operations_total.labels(operation='get', status='failed').inc()
        logger.warning("get_cached_risk_score_failed", error=str(e))
    
    return None


def cache_driver_statistics(cache_key: str, stats: Dict[str, Any], ttl: int = 1800):
    """Cache driver statistics. Accepts cache_key (e.g., 'DRV-0001:30') or driver_id."""
    client = get_redis_client()
    if not client:
        return
    
    try:
        # Use cache_key directly (supports both 'driver_id' and 'driver_id:period_days' formats)
        key = f"driver_stats:{cache_key}"
        client.setex(key, ttl, json.dumps(stats, default=str))
        logger.debug("driver_stats_cached", cache_key=cache_key)
    except Exception as e:
        logger.warning("cache_driver_stats_failed", error=str(e))


def get_cached_driver_statistics(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached driver statistics. Accepts cache_key (e.g., 'DRV-0001:30') or driver_id."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        # Use cache_key directly (supports both 'driver_id' and 'driver_id:period_days' formats)
        key = f"driver_stats:{cache_key}"
        data = client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning("get_cached_driver_stats_failed", error=str(e))
    
    return None


def update_feature_store(driver_id: str, features: Dict[str, Any], ttl: int = 3600):
    """Update feature store in Redis."""
    client = get_redis_client()
    if not client:
        return
    
    try:
        key = f"features:{driver_id}"
        client.setex(key, ttl, json.dumps(features, default=str))
        logger.debug("features_updated", driver_id=driver_id)
    except Exception as e:
        logger.warning("update_feature_store_failed", error=str(e))


def get_feature_store(driver_id: str) -> Optional[Dict[str, Any]]:
    """Get features from feature store."""
    client = get_redis_client()
    if not client:
        return None
    
    try:
        key = f"features:{driver_id}"
        data = client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning("get_feature_store_failed", error=str(e))
    
    return None


def invalidate_cache(driver_id: str):
    """Invalidate all cache for a driver."""
    client = get_redis_client()
    if not client:
        return
    
    try:
        patterns = [
            f"risk_score:{driver_id}",
            f"driver_stats:{driver_id}",
            f"features:{driver_id}"
        ]
        for pattern in patterns:
            client.delete(pattern)
        logger.debug("cache_invalidated", driver_id=driver_id)
    except Exception as e:
        logger.warning("invalidate_cache_failed", error=str(e))

