import pytest
from unittest.mock import patch, AsyncMock
from config import API_KEY, MAX_PAYLOAD_SIZE
import core.exceptions as exceptions
from services.doorbell_service import EventProcessed, NoSubscriptionsFound, DuplicateEventIgnored

VALID_JPEG_PAYLOAD = b"\xff\xd8\xff\x00\x00"

def get_valid_request() -> tuple[dict, bytes]:
    headers = {
        "Content-Length": "1",
        "Content-Type": "image/jpeg",
        "X-API-KEY": API_KEY, 
        "Serial-Number": "123", 
        "Event-ID": "event1",
    }
    return headers, VALID_JPEG_PAYLOAD 

# TEST MISSING HEADERS
@pytest.mark.parametrize(
    "key_to_omit, expected_status, expected_err",
    [
        pytest.param(
            "Content-Length",
            411,
            "Length Required",
            id="missing_content_length"
        ),
        pytest.param(
            "Content-Type",
            400,
            "Content Type required",
            id="missing_content_type"
        ),
        pytest.param(
            "X-API-KEY",
            400,
            "Missing required headers",
            id="missing_api_key"
        ),
        pytest.param(
            "Serial-Number",
            400,
            "Missing required headers",
            id="missing_serial_number"
        ),
        pytest.param(
            "Event-ID",
            400,
            "Missing required headers",
            id="missing_event_id"
        ),
    ]
)
@pytest.mark.asyncio
async def test_missing_headers(test_client, key_to_omit, expected_status, expected_err):
    headers, _ = get_valid_request()
    headers.pop(key_to_omit, None)
    
    
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    assert response.status_code == expected_status
    assert response_data["error"]["message"] == expected_err


# TEST INVALID HEADERS
@pytest.mark.parametrize(
    "header_override, expected_status, expected_err",
    [
        pytest.param(
            {"X-API-KEY": "invalid_api_key"},
            401,
            "Unauthorized API Key",
            id="invalid_api_key"
        ),
        pytest.param(
            {"Content-Type": "invalid_content_type"},
            415,
            "Unsupported content type",
            id="invalid_content_type"
        ),
        pytest.param(
            {"Content-Length": str(MAX_PAYLOAD_SIZE + 1)},
            413,
            "Payload too large",
            id="payload_too_large"
        ),
    ]
)
@pytest.mark.asyncio
async def test_invalid_header_values(test_client, header_override, expected_status, expected_err):
    headers, _ = get_valid_request()
    new_headers = {**headers, **header_override}
    response = await test_client.post("/doorbell", headers=new_headers)
    response_data = await response.get_json()
    
    assert response.status_code == expected_status
    assert response_data["error"]["message"] == expected_err

# TEST MISSING PAYLOAD
@pytest.mark.asyncio
async def test_payload_missing(test_client):

    headers, _ = get_valid_request()
    
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    assert response.status_code == 400
    assert response_data["error"]["message"] == "No image data found"

# TEST RESULT SUCCESS    
@pytest.mark.parametrize(
    "result_class, expected_status, expected_message",
    [
        pytest.param(
            DuplicateEventIgnored,
            200,
            "Duplicate Event Ignored",
            id="duplicate_event"
        ),
        pytest.param(
            NoSubscriptionsFound,
            200,
            "No Active Subscriptions Configured",
            id="no_subscriptions"
        ),
        pytest.param(
            EventProcessed,
            200,
            "Event Processed Successfully",
            id="event_processed"
        ),
    ]
)
@patch("api.blueprints.doorbell.service.process_doorbell_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_results_success(mock_result, test_client, result_class, expected_status, expected_message):
    mock_result.return_value = result_class()
    
    headers, data = get_valid_request()
    response = await test_client.post("/doorbell", headers=headers, data=data)
    response_data = await response.get_json()
    
    assert response.status_code == expected_status
    assert response_data["status"] == "success"
    assert response_data["message"] == expected_message

# TEST UNHANDLED RESULT TYPE
@patch("api.blueprints.doorbell.service.process_doorbell_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_unhandled_result_type(mock_process_event, test_client):
    mock_process_event.return_value = object()
    
    headers, data = get_valid_request()
    response = await test_client.post("/doorbell", headers=headers, data=data)
    response_data = await response.get_json()
    
    assert response.status_code == 500
    assert response_data["error"]["message"] == "Internal Server Error"

# TEST RESULT EXCEPTIONS
@pytest.mark.parametrize(
    "exception_class, expected_status, expected_err",
    [
        pytest.param(
            exceptions.DeviceUnauthorizedError,
            403,
            "Device Unauthorized",
            id="device_unauthorized_error"
        ),
        pytest.param(
            exceptions.InvalidImageFormatError,
            415,
            "Invalid Image Format",
            id="invalid_image_format_error"
        ),
        pytest.param(
            exceptions.NotificationServiceError,
            503,
            "Service Unavailable",
            id="service_unavailable_error"
        ),
        pytest.param(
            exceptions.DatabaseError,
            500,
            "Internal Server Error",
            id="database_error"
        ),
        pytest.param(
            exceptions.ImageProcessingError,
            500,
            "Internal Server Error",
            id="image_processing_error"
        ),
        pytest.param(
            Exception,
            500,
            "Internal Server Error",
            id="unhandled_exception"
        ),
    ]
)
@patch("api.blueprints.doorbell.service.process_doorbell_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_results_exceptions(mock_result, test_client, exception_class, expected_status, expected_err):
    mock_result.side_effect = exception_class()
    
    headers, data = get_valid_request()
    response = await test_client.post("/doorbell", headers=headers, data=data)
    response_data = await response.get_json()
    
    assert response.status_code == expected_status
    assert response_data["error"]["message"] == expected_err