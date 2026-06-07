import json
from functools import wraps
from typing import Callable, Any
import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Global Redis Connection Pool
redis_pool = None

async def get_redis_client():
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_pool

def cache_response(expire: int = 300):
    """
    Decorator to cache FastAPI responses in Redis.
    Uses the request path and query parameters as the cache key.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # We must be careful how we build the key.
            # For simplicity in this implementation, we will hash the function name and kwargs.
            cache_key = f"cache:{func.__name__}:{str(kwargs)}"
            
            try:
                redis_client = await get_redis_client()
                cached_val = await redis_client.get(cache_key)
                
                if cached_val:
                    return json.loads(cached_val)
                    
                # Execute actual function if not in cache
                result = await func(*args, **kwargs)
                
                # Cache the result
                if isinstance(result, dict) or isinstance(result, list):
                    await redis_client.set(cache_key, json.dumps(result), ex=expire)
                    
                return result
            except Exception as e:
                # If Redis is down, just execute the function
                print(f"Redis cache error: {e}")
                return await func(*args, **kwargs)
        return wrapper
    return decorator
