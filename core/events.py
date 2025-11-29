from typing import Dict, Any, Optional, Callable, Awaitable
from core.redis_client import redis_client
from core.logger import logger
import json
import asyncio
import uuid
from datetime import datetime, timezone

class EventBus:
    def __init__(self, stream_prefix: str = "agent:stream"):
        self.stream_prefix = stream_prefix
        self.client = redis_client.get_async_client()
        self.handlers: Dict[str, Callable] = {}
        self.running = False
    
    def _make_stream(self, event_type: str) -> str:
        return f"{self.stream_prefix}:{event_type}"
    
    async def publish(self, event_type: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        try:
            event_id = correlation_id or str(uuid.uuid4())
            stream_name = self._make_stream(event_type)
            
            payload = {
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": json.dumps(data)
            }
            
            message_id = await self.client.xadd(stream_name, payload)
            logger.info(f"Published event {event_type} with ID {event_id}")
            return event_id
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise
    
    async def request(self, event_type: str, data: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        correlation_id = str(uuid.uuid4())
        response_stream = f"{self.stream_prefix}:response:{correlation_id}"
        
        try:
            await self.publish(event_type, {**data, "response_stream": response_stream}, correlation_id)
            
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                messages = await self.client.xread({response_stream: "0"}, count=1, block=1000)
                
                if messages:
                    for stream, msg_list in messages:
                        for msg_id, msg_data in msg_list:
                            await self.client.delete(response_stream)
                            return json.loads(msg_data.get("data", "{}"))
                
                await asyncio.sleep(0.1)
            
            logger.warning(f"Request timeout for {event_type}")
            return None
        except Exception as e:
            logger.error(f"Request failed for {event_type}: {e}")
            return None
        finally:
            await self.client.delete(response_stream)
    
    def subscribe(self, event_type: str):
        def decorator(handler: Callable[[Dict[str, Any]], Awaitable[None]]):
            self.handlers[event_type] = handler
            return handler
        return decorator
    
    async def start_consumer(self, consumer_group: str = "agent-group", consumer_name: str = "agent-1"):
        self.running = True
        
        for event_type in self.handlers.keys():
            stream_name = self._make_stream(event_type)
            try:
                await self.client.xgroup_create(stream_name, consumer_group, id="0", mkstream=True)
            except Exception:
                pass
        
        logger.info(f"Event consumer started for {len(self.handlers)} event types")
        
        while self.running:
            try:
                streams = {self._make_stream(et): ">" for et in self.handlers.keys()}
                messages = await self.client.xreadgroup(
                    consumer_group,
                    consumer_name,
                    streams,
                    count=10,
                    block=1000
                )
                
                for stream, msg_list in messages:
                    event_type = stream.decode() if isinstance(stream, bytes) else stream
                    event_type = event_type.split(":")[-1]
                    
                    handler = self.handlers.get(event_type)
                    if not handler:
                        continue
                    
                    for msg_id, msg_data in msg_list:
                        try:
                            data = json.loads(msg_data.get("data", "{}"))
                            await handler(data)
                            await self.client.xack(stream, consumer_group, msg_id)
                        except Exception as e:
                            logger.error(f"Handler error for {event_type}: {e}")
            except Exception as e:
                if self.running:
                    logger.error(f"Consumer error: {e}")
                    await asyncio.sleep(1)
    
    async def stop_consumer(self):
        self.running = False

event_bus = EventBus()
