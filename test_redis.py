#!/usr/bin/env python3
"""Redis connection test script for debugging."""

import asyncio
import sys
import os
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import settings
from src.core.redis import init_redis, get_redis, redis_set, redis_get, close_redis

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_redis_connection():
    """Test Redis connection and basic operations."""
    print("=== Redis Connection Test ===")
    print(f"Redis Host: {settings.REDIS_HOST}")
    print(f"Redis Port: {settings.REDIS_PORT}")
    print(f"Redis DB: {settings.REDIS_DB}")
    print(f"Redis Password: {'<set>' if settings.REDIS_PASSWORD else '<empty>'}")
    print()
    
    try:
        # Initialize Redis
        print("1. Initializing Redis connection...")
        await init_redis()
        
        # Get Redis client
        print("2. Getting Redis client...")
        redis_client = await get_redis()
        
        if redis_client is None:
            print("❌ Failed to get Redis client")
            return False
        
        print("✅ Redis client obtained successfully")
        
        # Test basic operations
        print("3. Testing basic Redis operations...")
        
        # Test SET
        test_key = "test:connection"
        test_value = {"message": "Hello Redis!", "timestamp": "2025-09-17"}
        
        print(f"   Setting key '{test_key}'...")
        set_result = await redis_set(test_key, test_value, expire=60)
        
        if not set_result:
            print("❌ Failed to set test key")
            return False
        
        print("✅ SET operation successful")
        
        # Test GET
        print(f"   Getting key '{test_key}'...")
        get_result = await redis_get(test_key)
        
        if get_result != test_value:
            print(f"❌ GET operation failed. Expected: {test_value}, Got: {get_result}")
            return False
        
        print("✅ GET operation successful")
        
        # Test direct Redis operations
        print("4. Testing direct Redis operations...")
        direct_result = await redis_client.ping()
        print(f"✅ Direct PING successful: {direct_result}")
        
        # Test Redis info
        info = await redis_client.info('server')
        print(f"✅ Redis server version: {info.get('redis_version', 'unknown')}")
        
        print("\n🎉 All Redis tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Redis test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("5. Closing Redis connection...")
        await close_redis()
        print("✅ Redis connection closed")


async def test_redis_availability():
    """Quick test to check if Redis is available."""
    import redis.asyncio as redis
    
    try:
        # Test direct connection
        redis_password = settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None
        
        client = redis.Redis(
            host=settings.REDIS_HOST or 'localhost',
            port=settings.REDIS_PORT or 6379,
            password=redis_password,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        result = await client.ping()
        await client.close()
        
        print(f"✅ Direct Redis connection successful: {result}")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis connection error: {e}")
        return False
    except redis.AuthenticationError as e:
        print(f"❌ Redis authentication error: {e}")
        return False
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False


def main():
    """Main test function."""
    print("Starting Redis diagnostics...\n")
    
    # Test 1: Check settings
    print("=== Configuration Check ===")
    if not settings.REDIS_HOST:
        print("❌ REDIS_HOST is not set")
        sys.exit(1)
    
    print("✅ Redis configuration looks valid")
    
    # Test 2: Direct connection test
    print("\n=== Direct Connection Test ===")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        direct_success = loop.run_until_complete(test_redis_availability())
        
        if not direct_success:
            print("❌ Direct Redis connection failed")
            sys.exit(1)
        
        # Test 3: Full application test
        print("\n=== Application Redis Test ===")
        app_success = loop.run_until_complete(test_redis_connection())
        
        if not app_success:
            print("❌ Application Redis test failed")
            sys.exit(1)
        
        print("\n🎉 All Redis diagnostics passed!")
        
    finally:
        loop.close()


if __name__ == "__main__":
    main()