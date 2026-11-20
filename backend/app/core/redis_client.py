import json
import logging
import time
from typing import Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory cache if Redis is temporarily unreachable
_memory_cache: dict[str, tuple[Any, float]] = {}

_redis_client = None
_redis_available = False
_last_redis_check = 0.0
_CHECK_INTERVAL = 60.0  # Check Redis reachability every 60 seconds if offline

def _init_redis():
    global _redis_client
    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.6,
            socket_timeout=0.6
        )
    except Exception as e:
        logger.warning(f"[Cache] Could not configure Redis: {e}")
        _redis_client = None

_init_redis()

async def _check_redis_health() -> bool:
    global _redis_available, _last_redis_check
    now = time.time()
    if _redis_client is None:
        _redis_available = False
        return False

    if _redis_available:
        return True

    # If currently offline, don't ping on every request; respect cooldown interval
    if now - _last_redis_check < _CHECK_INTERVAL:
        return False

    _last_redis_check = now
    try:
        await _redis_client.ping()
        _redis_available = True
        logger.info(f"[Cache] Connected to Redis at {settings.REDIS_URL}")
        return True
    except Exception:
        _redis_available = False
        return False

class CacheService:
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        if await _check_redis_health() and _redis_client:
            try:
                val = await _redis_client.get(key)
                if val:
                    return json.loads(val)
            except Exception as e:
                global _redis_available
                _redis_available = False
                logger.debug(f"[Cache] Redis GET fallback for {key}: {e}")

        # In-Memory Cache Lookup (<1ms)
        if key in _memory_cache:
            data, expiry = _memory_cache[key]
            if expiry == 0 or expiry > time.time():
                return data
            else:
                del _memory_cache[key]
        return None

    @staticmethod
    async def set(key: str, value: Any, ttl_seconds: int = 3600 * 12) -> bool:
        serialized = json.dumps(value, default=str)
        if await _check_redis_health() and _redis_client:
            try:
                await _redis_client.set(key, serialized, ex=ttl_seconds)
                return True
            except Exception as e:
                global _redis_available
                _redis_available = False
                logger.debug(f"[Cache] Redis SET fallback for {key}: {e}")

        # Store in in-memory cache with expiration timestamp
        expiry = (time.time() + ttl_seconds) if ttl_seconds > 0 else 0
        _memory_cache[key] = (value, expiry)
        return True

    @staticmethod
    async def delete(key: str) -> bool:
        if await _check_redis_health() and _redis_client:
            try:
                await _redis_client.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)
        return True

    @staticmethod
    def get_status() -> dict:
        return {
            "engine": "redis" if _redis_available else "in-memory (high-speed)",
            "redis_connected": _redis_available,
            "redis_url": settings.REDIS_URL,
            "cached_keys_count": len(_memory_cache)
        }

cache = CacheService()
