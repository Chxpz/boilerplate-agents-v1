from typing import Optional, Any
from core.redis_client import redis_client
from core.logger import logger
import json
import hashlib

class CacheManager:
    def __init__(self, prefix: str = "agent:cache"):
        self.prefix = prefix
        self.client = redis_client.get_async_client()
    
    def _make_key(self, key: str) -> str:
        return f"{self.prefix}:{key}"
    
    def _hash_key(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            value = await self.client.get(self._make_key(key))
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            await self.client.setex(
                self._make_key(key),
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, key: str):
        try:
            await self.client.delete(self._make_key(key))
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def get_or_set(self, key: str, factory, ttl: int = 3600) -> Any:
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        value = await factory() if callable(factory) else factory
        await self.set(key, value, ttl)
        return value

cache_manager = CacheManager()
