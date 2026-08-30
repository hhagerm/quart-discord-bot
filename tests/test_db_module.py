import pytest_asyncio
import pytest
from unittest.mock import patch
from asyncpg.exceptions import ForeignKeyViolationError
from db import db_module
from config import TEST_DATABASE_URL

EXISTING_DATA = {
    "serial_number": "SN-001",
    "pairing_code": "1234"
}

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db_pool():
    db_module.DATABASE_URL = TEST_DATABASE_URL
    await db_module.init_db_pool()
    
    yield
    
    await db_module.close_db_pool()

@pytest_asyncio.fixture(autouse=True)
async def isolate_test_state():
    pool = db_module.get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "TRUNCATE TABLE devices, subscriptions, processed_events RESTART IDENTITY CASCADE;"
        )
        
    yield

@pytest_asyncio.fixture
async def existing_device():
    pool = db_module.get_pool()
    await pool.execute(
        "INSERT INTO devices (serial_number, pairing_code) VALUES ($1, $2)",
        EXISTING_DATA["serial_number"], EXISTING_DATA["pairing_code"]
    )

@pytest_asyncio.fixture
async def existing_event():
    pool = db_module.get_pool()
    await pool.execute(
        "INSERT INTO processed_events (serial_number, event_id) VALUES ($1, $2)",
        EXISTING_DATA["serial_number"], "1"
    )

@pytest_asyncio.fixture
async def existing_subs():
    pool = db_module.get_pool()
    await pool.execute(
        "INSERT INTO subscriptions (serial_number, channel_id, guild_id) VALUES ($1, $2, $3)",
        EXISTING_DATA["serial_number"], 1, 1
    )
    await pool.execute(
        "INSERT INTO subscriptions (serial_number, channel_id, guild_id) VALUES ($1, $2, $3)",
        EXISTING_DATA["serial_number"], 2, 2
    )

class TestVerifyPairCode:
    async def test_verify_pair_code_returns_true_when_match(self, existing_device):
        result = await db_module.verify_pair_code(EXISTING_DATA["serial_number"], EXISTING_DATA["pairing_code"])
        assert result is True
        
    async def test_verify_pair_code_returns_false_when_serial_missing(self):
        result = await db_module.verify_pair_code("GHOST-SN", EXISTING_DATA["pairing_code"])
        assert result is False
        
    async def test_verify_pair_code_returns_false_when_pair_not_matching(self, existing_device):
        result = await db_module.verify_pair_code(EXISTING_DATA["serial_number"], "14")
        assert result is False

class TestValidateSerialNum:
    async def test_validate_serial_num_returns_true_when_exists(self, existing_device):
        result = await db_module.validate_serial_num(EXISTING_DATA["serial_number"])
        assert result is True

    async def test_validate_serial_num_returns_false_when_missing(self):
        result = await db_module.validate_serial_num("GHOST-SN")
        assert result is False

class TestAddEvent:
    async def test_add_event_returns_false_on_exists(self, existing_device, existing_event):
        result = await db_module.add_event(EXISTING_DATA["serial_number"], "1")
        assert result is False
        
    async def test_add_event_returns_true_on_new(self, existing_device):
        result = await db_module.add_event(EXISTING_DATA["serial_number"], "1")
        assert result is True
    
    async def test_add_event_raises_on_foreign_key_violation(self):
        with pytest.raises(ForeignKeyViolationError):
            await db_module.add_event("GHOST-SN", "some-event-id")

class TestGetDeviceSubscriptions:
    async def test_get_device_subscriptions_empty_result(self, existing_device):
        result = await db_module.get_device_subscriptions(EXISTING_DATA["serial_number"]);
        
        assert len(result) == 0
        
    async def test_get_device_subscriptions_returns_subs_on_match(self, existing_device, existing_subs):
        result = await db_module.get_device_subscriptions(EXISTING_DATA["serial_number"]);
        
        assert len(result) == 2
        assert len(result[0]) == 2
        
class TestRemoveSubscriptions:
    async def test_remove_subscription_removes_subscription(self, existing_device, existing_subs):
        result = await db_module.remove_subscription(EXISTING_DATA["serial_number"], 1);
        
        assert result is True
        
        pool = db_module.get_pool()
        row = await pool.fetchrow(
            "SELECT 1 FROM subscriptions WHERE serial_number = $1 AND guild_id = $2",
            EXISTING_DATA["serial_number"], 1
        )
        assert row is None
        
    async def test_remove_subscription_returns_false_on_no_match(self, existing_device):
        result = await db_module.remove_subscription(EXISTING_DATA["serial_number"], 1);
        
        assert result is False
        
class TestAddSubscription:
    async def test_add_subscription_creates_new_row(self, existing_device):
        result = await db_module.add_subscription(EXISTING_DATA["serial_number"], guild_id=1, channel_id=100)
        assert result is True

        pool = db_module.get_pool()
        row = await pool.fetchrow(
            "SELECT channel_id FROM subscriptions WHERE serial_number = $1 AND guild_id = $2",
            EXISTING_DATA["serial_number"], 1
        )
        assert row["channel_id"] == 100

    async def test_add_subscription_updates_channel_on_conflict(self, existing_device, existing_subs):
        result = await db_module.add_subscription(EXISTING_DATA["serial_number"], guild_id=1, channel_id=999)
        assert result is True

        pool = db_module.get_pool()
        row = await pool.fetchrow(
            "SELECT channel_id FROM subscriptions WHERE serial_number = $1 AND guild_id = $2",
           EXISTING_DATA["serial_number"], 1
        )
        assert row["channel_id"] == 999
    
    async def test_add_subscription_returns_false_when_device_does_not_exist(self):
        result = await db_module.add_subscription("GHOST-SN", guild_id=1, channel_id=100)
        assert result is False