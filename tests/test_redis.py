import pytest
import pytest_asyncio
from core.redis_client import redis_client
from core.cache import cache_manager
from core.events import event_bus

@pytest_asyncio.fixture
async def redis_conn():
    client = redis_client.get_async_client()
    yield client
    await redis_client.close()

@pytest.mark.asyncio
async def test_redis_connection(redis_conn):
    """Test Redis connection."""
    result = await redis_conn.ping()
    assert result is True

@pytest.mark.asyncio
async def test_cache_operations(redis_conn):
    """Test cache set and get operations."""
    test_key = "test:key"
    test_value = {"data": "test"}
    
    await cache_manager.set(test_key, test_value, ttl=60)
    cached = await cache_manager.get(test_key)
    
    assert cached == test_value
    
    await cache_manager.delete(test_key)
    cached = await cache_manager.get(test_key)
    assert cached is None

@pytest.mark.asyncio
async def test_event_publish(redis_conn):
    """Test event publishing."""
    event_id = await event_bus.publish("test.event", {"message": "test"})
    assert event_id is not None
    assert len(event_id) > 0

@pytest.mark.asyncio
async def test_event_request_timeout(redis_conn):
    """Test event request with timeout."""
    result = await event_bus.request("nonexistent.event", {"data": "test"}, timeout=2)
    assert result is None
