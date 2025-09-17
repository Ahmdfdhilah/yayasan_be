"""Redis connection and utilities with better error handling and configuration."""

import redis.asyncio as redis
from typing import Optional, Any
import json
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
redis_pool: Optional[redis.ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global redis_pool, redis_client
    
    if not settings.REDIS_HOST:
        logger.warning("Redis not configured, skipping Redis initialization")
        return
    
    try:
        # Handle empty string passwords properly
        redis_password = settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None
        
        redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT or 6379,
            password=redis_password,  
            db=settings.REDIS_DB,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Test connection with more detailed error handling
        await redis_client.ping()
        logger.info(f"✅ Redis connected successfully to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
    except redis.ConnectionError as e:
        logger.error(f"❌ Redis connection failed - Connection Error: {e}")
        logger.error(f"Redis config: host={settings.REDIS_HOST}, port={settings.REDIS_PORT}, db={settings.REDIS_DB}")
        redis_pool = None
        redis_client = None
    except redis.AuthenticationError as e:
        logger.error(f"❌ Redis authentication failed: {e}")
        logger.error("Check REDIS_PASSWORD configuration")
        redis_pool = None
        redis_client = None
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        logger.error(f"Redis config: host={settings.REDIS_HOST}, port={settings.REDIS_PORT}, db={settings.REDIS_DB}")
        redis_pool = None
        redis_client = None


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_pool, redis_client
    
    if redis_client:
        try:
            await redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
    
    if redis_pool:
        try:
            await redis_pool.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting Redis pool: {e}")
    
    redis_pool = None
    redis_client = None
    logger.info("Redis connection closed")


async def get_redis() -> Optional[redis.Redis]:
    """Get Redis client instance (async style)."""
    if redis_client is None:
        logger.warning("Redis client is not initialized")
        return None
    
    try:
        # Quick health check
        await redis_client.ping()
        return redis_client
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return None


async def redis_set(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """Set a value in Redis with optional expiration."""
    client = await get_redis()
    if not client:
        logger.warning("Redis not available for SET operation")
        return False
    
    try:
        # Serialize value to JSON if it's not a string
        if not isinstance(value, str):
            value = json.dumps(value)
        
        expire_time = expire or settings.REDIS_TTL
        await client.setex(key, expire_time, value)
        logger.debug(f"Redis SET successful for key: {key}")
        return True
        
    except Exception as e:
        logger.error(f"Redis SET error for key {key}: {e}")
        return False


async def redis_get(key: str) -> Optional[Any]:
    """Get a value from Redis."""
    client = await get_redis()
    if not client:
        logger.warning("Redis not available for GET operation")
        return None
    
    try:
        value = await client.get(key)
        if value is None:
            return None
        
        # Try to deserialize JSON, fallback to string
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
            
    except Exception as e:
        logger.error(f"Redis GET error for key {key}: {e}")
        return None


async def redis_delete(key: str) -> bool:
    """Delete a key from Redis."""
    client = await get_redis()
    if not client:
        logger.warning("Redis not available for DELETE operation")
        return False
    
    try:
        result = await client.delete(key)
        return result > 0
        
    except Exception as e:
        logger.error(f"Redis DELETE error for key {key}: {e}")
        return False


async def redis_exists(key: str) -> bool:
    """Check if a key exists in Redis."""
    client = await get_redis()
    if not client:
        return False
    
    try:
        result = await client.exists(key)
        return result > 0
        
    except Exception as e:
        logger.error(f"Redis EXISTS error for key {key}: {e}")
        return False


async def redis_increment(key: str, amount: int = 1, expire: Optional[int] = None) -> Optional[int]:
    """Increment a counter in Redis."""
    client = await get_redis()
    if not client:
        logger.warning("Redis not available for INCREMENT operation")
        return None
    
    try:
        # Use pipeline for atomic operation
        async with client.pipeline() as pipe:
            await pipe.incrby(key, amount)
            if expire:
                await pipe.expire(key, expire)
            results = await pipe.execute()
            return results[0]
            
    except Exception as e:
        logger.error(f"Redis INCREMENT error for key {key}: {e}")
        return None


async def redis_get_pattern(pattern: str) -> list:
    """Get all keys matching a pattern."""
    client = await get_redis()
    if not client:
        return []
    
    try:
        keys = await client.keys(pattern)
        return keys
        
    except Exception as e:
        logger.error(f"Redis KEYS error for pattern {pattern}: {e}")
        return []


async def redis_flush_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern."""
    client = await get_redis()
    if not client:
        return 0
    
    try:
        keys = await redis_get_pattern(pattern)
        if not keys:
            return 0
        
        result = await client.delete(*keys)
        return result
        
    except Exception as e:
        logger.error(f"Redis FLUSH error for pattern {pattern}: {e}")
        return 0