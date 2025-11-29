from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from typing import Optional, Dict, Any
from config import settings
from core.logger import logger
import json

class RedisClient:
    _sync_instance: Optional[Redis] = None
    _async_instance: Optional[AsyncRedis] = None
    
    @classmethod
    def get_sync_client(cls) -> Redis:
        if cls._sync_instance is None:
            cls._sync_instance = Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            logger.info("Redis sync client initialized")
        return cls._sync_instance
    
    @classmethod
    def get_async_client(cls) -> AsyncRedis:
        if cls._async_instance is None:
            cls._async_instance = AsyncRedis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            logger.info("Redis async client initialized")
        return cls._async_instance
    
    @classmethod
    async def close(cls):
        if cls._async_instance:
            await cls._async_instance.aclose()
        if cls._sync_instance:
            cls._sync_instance.close()

redis_client = RedisClient()
