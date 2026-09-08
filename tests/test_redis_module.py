import json

import pytest_asyncio
import pytest

import redis_module
from config import TEST_REDIS_HOST, TEST_REDIS_PORT

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_redis_client():
    redis_module.REDIS_HOST = TEST_REDIS_HOST
    redis_module.REDIS_PORT = TEST_REDIS_PORT
    await redis_module.init_redis_pool()

    yield
    
    await redis_module.close_redis_pool()
    
@pytest_asyncio.fixture(autouse=True)
async def isolate_test_state():
    client = redis_module.get_client()
    await client.flushdb(asynchronous=True)
    
    yield
    
class TestNotificationQueue:
    async def test_round_trip_preserves_data(self):
        await redis_module.publish_notification("test/path", [(1, 2), (3, 4)])
        
        file_path, subscriptions = await redis_module.receive_notification()
        
        assert file_path == "test/path"
        assert subscriptions == [[1, 2], [3, 4]]
    
    async def test_queue_is_fifo(self):
        await redis_module.publish_notification("test/path1", [(1, 1)])
        await redis_module.publish_notification("test/path2", [(2, 2)])
        
        file_path, subscriptions = await redis_module.receive_notification()
                
        assert file_path == "test/path1"
        assert subscriptions == [[1, 1]]
        
        file_path, subscriptions = await redis_module.receive_notification()
                
        assert file_path == "test/path2"
        assert subscriptions == [[2, 2]]

class TestReceiveNotification:
    async def test_receive_notification_returns_none_on_queue_empty(self, monkeypatch):
        monkeypatch.setattr(redis_module, "BLOCK_TIMEOUT", 0.1)
        
        assert await redis_module.receive_notification() is None
    
    
    async def test_receive_notification_raises_on_malformed_payload(self):
        client = redis_module.get_client()
        await client.rpush(redis_module.NOTIFICATION_QUEUE, "not json")

        with pytest.raises(json.JSONDecodeError):
            await redis_module.receive_notification()

class TestGetClient:          
    def test_get_client_raises_before_init(self, monkeypatch):
        monkeypatch.setattr(redis_module, "_client", None)
        
        with pytest.raises(RuntimeError):
            redis_module.get_client()