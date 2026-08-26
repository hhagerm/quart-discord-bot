import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from services.doorbell_service import process_doorbell_event, EventProcessed, DuplicateEventIgnored, NoSubscriptionsFound
from core import exceptions

@pytest.fixture
def mock_db():
    with patch("services.doorbell_service.db_module") as mock:
        mock.validate_serial_num = AsyncMock(return_value = True)
        mock.add_event = AsyncMock(return_value = True)
        mock.get_device_subscriptions = AsyncMock(return_value=["sub"])
        yield mock

@pytest.fixture
def mock_storage():
    with patch("services.doorbell_service.storage") as mock:
        mock.is_valid_jpeg.return_value = True
        mock.save_uploaded_image = AsyncMock(return_value = "test_image.jpg")
        yield mock

@pytest.fixture
def mock_bot():
    with patch("services.doorbell_service.bot_module") as mock:
        mock_cog = MagicMock()
        mock_cog.send_discord_notification = AsyncMock()
        mock.bot.get_cog.return_value = mock_cog
        yield mock
        
@pytest.mark.asyncio
async def test_process_event_success(mock_db, mock_storage, mock_bot):
    mock_cog = mock_bot.bot.get_cog.return_value
    
    result = await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert isinstance(result, EventProcessed)
    mock_db.validate_serial_num.assert_called_once_with("123")
    mock_bot.bot.get_cog.assert_called_once_with("NotificationCog")
    mock_cog.send_discord_notification.assert_called_once_with("test_image.jpg", ["sub"])
    

@pytest.mark.asyncio
async def test_invalid_img_format(mock_storage):
    mock_storage.is_valid_jpeg.return_value = False
    
    with pytest.raises(exceptions.InvalidImageFormatError) as exc_info:
        await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert str(exc_info.value) == "Invalid image format"
    
@pytest.mark.asyncio
async def test_unauthorized_serial_num(mock_storage, mock_db):
    mock_db.validate_serial_num.return_value = False
    
    with pytest.raises(exceptions.DeviceUnauthorizedError) as exc_info:
        await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert str(exc_info.value) == "Serial number 123 unauthorized"

@pytest.mark.asyncio
async def test_add_event_db_fail(mock_storage, mock_db):
    mock_db.add_event.side_effect = Exception()
    
    with pytest.raises(exceptions.DatabaseError) as exc_info:
        await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert str(exc_info.value) == "add_event failed"
    
@pytest.mark.asyncio
async def test_duplicate_event(mock_storage, mock_db):
    mock_db.add_event.return_value = False
    
    result = await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert isinstance(result, DuplicateEventIgnored)

@pytest.mark.asyncio
async def test_get_device_subscriptions_db_fail(mock_storage, mock_db):
    mock_db.get_device_subscriptions.side_effect = Exception()
    
    with pytest.raises(exceptions.DatabaseError) as exc_info:
        await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert str(exc_info.value) == "get_device_subscriptions failed"
    
@pytest.mark.asyncio
async def test_no_subscriptions(mock_storage, mock_db):
    mock_db.get_device_subscriptions.return_value = []
    
    result = await process_doorbell_event("123", "evt_1", b"fake_data")
        
    assert isinstance(result, NoSubscriptionsFound)
    
@pytest.mark.asyncio
async def test_image_processing_err(mock_storage, mock_db):
    mock_storage.save_uploaded_image.side_effect = Exception()
    
    with pytest.raises(exceptions.ImageProcessingError):
        await process_doorbell_event("123", "evt_1", b"fake_data")
        
@pytest.mark.asyncio
async def test_notification_service_err(mock_storage, mock_db, mock_bot):
    mock_bot.bot.get_cog.return_value = None
    
    with pytest.raises(exceptions.NotificationServiceError):
        await process_doorbell_event("123", "evt_1", b"fake_data")

@patch("services.doorbell_service.BOT_SERVICES", False)
@pytest.mark.asyncio
async def test_bot_services_disabled(mock_storage, mock_db, mock_bot):
    result = await process_doorbell_event("123", "evt_1", b"fake_data")
    
    assert isinstance(result, EventProcessed)
    mock_bot.bot.get_cog.assert_not_called()