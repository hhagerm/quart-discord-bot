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
    await client.xgroup_create(
        redis_module.STREAM_NAME, redis_module.GROUP_NAME, id="$", mkstream=True
    )
    
    yield
    
class TestNotificationQueue:
    async def test_round_trip_preserves_data(self):
        await redis_module.publish_notification("test/path", [(1, 2), (3, 4)])

        result = await redis_module.receive_notification()

        assert [r[1:] for r in result] == [("test/path", 1, 2), ("test/path", 3, 4)]

    async def test_queue_is_fifo(self):
        await redis_module.publish_notification("test/path1", [(1, 1)])
        await redis_module.publish_notification("test/path2", [(2, 2)])

        result = await redis_module.receive_notification()

        assert [r[1:] for r in result] == [("test/path1", 1, 1), ("test/path2", 2, 2)]



class TestReceiveNotification:
    async def test_returns_empty_list_when_stream_empty(self, monkeypatch):
        monkeypatch.setattr(redis_module, "BLOCK_TIMEOUT_MS", 100)

        assert await redis_module.receive_notification() == []

    async def test_raises_on_malformed_payload(self):
        await redis_module.get_client().xadd(
            redis_module.STREAM_NAME,
            {"file_path": "x", "guild_id": "not-an-int", "channel_id": "1"},
        )

        with pytest.raises(ValueError):
            await redis_module.receive_notification()

    async def test_acked_message_not_pending(self):
        await redis_module.publish_notification("p", [(1, 1)])
        [(msg_id, *_)] = await redis_module.receive_notification()

        await redis_module.ack_notification(msg_id)

        assert await redis_module.receive_pending_notifications() == []
        
class TestGetClient:          
    def test_get_client_raises_before_init(self, monkeypatch):
        monkeypatch.setattr(redis_module, "_client", None)
        
        with pytest.raises(RuntimeError):
            redis_module.get_client()