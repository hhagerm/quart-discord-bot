import pytest

HEADERS = {
    "Content-Length": "1",
    "X-API-KEY": "secret", 
    "Serial-Number": "123", 
    "Event-ID": "event1",
}

def headers_without(key_to_omit: str) -> dict:
    return {k: v for k, v in HEADERS.items() if k != key_to_omit}

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
async def test_doorbell_missing_headers(test_client, headers, expected_status, expected_err):
    # Act
    response = await test_client.post("/doorbell", headers=headers)
    response_data = await response.get_json()
    
    # Assert
    assert response.status_code == expected_status
    assert response_data["error"]["message"] == expected_err