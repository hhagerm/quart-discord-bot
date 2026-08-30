import os
import pytest
from unittest.mock import patch
from core import storage

def test_valid_jpeg():
    valid_data = b"\xff\xd8\xff\x00"
    assert storage.is_valid_jpeg(valid_data) == True
    
def test_invalid_jpeg():
    invalid_data = b"\x00\x00\x00\x00"
    assert storage.is_valid_jpeg(invalid_data) == False

def test_write_file_success(tmp_path):
    file_path = tmp_path / "test_file.jpg"
    test_data = b"test_data"
    
    storage._write_file_sync(str(file_path), test_data)
    
    assert file_path.read_bytes() == test_data
    
def test_write_file_sync_raises_io_error(tmp_path):
    invalid_path = tmp_path / "nonexistent_dir" / "file.jpg"
    
    with pytest.raises(FileNotFoundError):
        storage._write_file_sync(str(invalid_path), b"data")
        
@pytest.mark.asyncio
@patch("core.storage._write_file_sync")
@patch("core.storage.UPLOAD_FOLDER", "/mock/upload/dir")
async def test_save_uploaded_image(mock_write):
    raw_data = b"fake_image_data"
    
    file_path = await storage.save_uploaded_image(raw_data)
    
    expected_prefix = os.path.join("/mock/upload/dir", "visitor_")
    
    assert file_path.startswith(expected_prefix)
    assert file_path.endswith(".jpg")
    mock_write.assert_called_once_with(file_path, raw_data)


@pytest.mark.asyncio
@patch("os.remove")
async def test_delete_image_success(mock_remove, caplog):
    test_path = "/mock/path.jpg"
    
    await storage.delete_image(test_path)
    
    mock_remove.assert_called_once_with(test_path)

@pytest.mark.asyncio
@patch("os.remove")
async def test_delete_image_handles_exception(mock_remove, caplog):
    test_path = "/mock/path.jpg"
    mock_remove.side_effect = OSError("Disk read error")
    
    await storage.delete_image(test_path)
    
    mock_remove.assert_called_once_with(test_path)
    assert "Failed to delete image" in caplog.text