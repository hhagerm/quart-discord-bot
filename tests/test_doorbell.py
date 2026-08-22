import pytest
from unittest.mock import patch, AsyncMock
from config import API_KEY

HEADERS = {
    "Content-Length": "1",
    "X-API-KEY": API_KEY, 
    "Serial-Number": "123", 
    "Event-ID": "event1",
}

def headers_without(key_to_omit: str) -> dict:
    return {k: v for k, v in HEADERS.items() if k != key_to_omit}

# TEST MISSING HEADERS
@pytest.mark.parametrize(
    "headers, expected_status, expected_err",
    [
        pytest.param(
            headers_without("Content-Length"),
            411,
            "Length Required",
            id="missing_content_length"
        ),
        pytest.param(
            headers_without("X-API-KEY"),
            400,
            "Missing required headers",
            id="missing_api_key"
        ),
        pytest.param(
            headers_without("Serial-Number"),
            400,
            "Missing required headers",
            id="missing_serial_number"
        ),
        pytest.param(
            headers_without("Event-ID"),
            400,
            "Missing required headers",
            id="missing_event_id"
        ),
    ]
)
@pytest.mark.asyncio
async def test_missing_headers(test_client, headers, expected_status, expected_err):
    # Act
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    # Assert
    assert response.status_code == expected_status
    assert response_data["error"]["message"] == expected_err
    
@pytest.mark.asyncio
async def test_invalid_api_key(test_client):
    headers = HEADERS.copy()
    headers["X-API-KEY"] = "invalid"
    
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    assert response.status_code == 401
    assert response_data["error"]["message"] == "Unauthorized API Key"
    
    
@pytest.mark.asyncio
async def test_payload_too_large(test_client):
    headers = HEADERS.copy()
    headers["Content-Length"] = 5 * 1024 * 1024 + 1
    
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    assert response.status_code == 413
    assert response_data["error"]["message"] == "Payload too large"

    
@pytest.mark.asyncio
@patch("db.db_module.validate_serial_num", new_callable=AsyncMock)
async def test_payload_missing(mock_validate, test_client):
    mock_validate.return_value = True

    headers = HEADERS.copy()
    
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    assert response.status_code == 400
    assert response_data["error"]["message"] == "No image data found"