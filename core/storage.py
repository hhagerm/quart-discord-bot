import logging
from uuid import uuid4
import asyncio
import os

from config import UPLOAD_FOLDER

logger = logging.getLogger(__name__)

JPEG_MAGIC_BYTES = b"\xff\xd8\xff"

def is_valid_jpeg(data: bytes) -> bool:
    return data.startswith(JPEG_MAGIC_BYTES)

def _write_file_sync(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)
        
async def save_uploaded_image(raw_data: bytes) -> str:
    file_name: str = f"visitor_{uuid4().hex}.jpg"
    file_path: str = os.path.join(
        UPLOAD_FOLDER, 
        file_name
    )
    
    await asyncio.to_thread(_write_file_sync, file_path, raw_data)
    return file_path

async def delete_image(path: str):
    try:
        await asyncio.to_thread(os.remove, path)
    except Exception:
       logger.exception("Failed to delete image: %s", path)
        