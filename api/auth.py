from functools import wraps
from quart import request, jsonify, Response, abort
from config import API_KEY
from db import db_module

MAX_PAYLOAD_SIZE = 5 * 1024 * 1024

async def validate_request(f) -> function:
    @wraps(f)
    async def wrapper(*args, **kwargs):
        content_length = request.content_length
        if content_length is None:
            abort(411, "Length Required")
        if content_length > MAX_PAYLOAD_SIZE:
            abort(413, "Payload too large")
        
        api_key = request.headers.get("X-API-KEY")
        serial_number = request.headers.get("Serial-Number")
        event_id = request.headers.get("Event-ID")
        
        if not api_key or not serial_number or not event_id:
            abort(400, "Missing required headers")
        
        if api_key != API_KEY:
            abort(401, "Unauthorized API Key")
        
        if not await db_module.validate_serial_num(serial_number):
            abort(403, "Device unauthorized")
        
        kwargs["serial_number"] = serial_number
        kwargs["event_id"] = event_id
        return await f(*args, **kwargs)
    
    return wrapper
            
        