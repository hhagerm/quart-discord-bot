from functools import wraps
from quart import request, abort
from config import API_KEY, MAX_PAYLOAD_SIZE

def validate_headers(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        content_length = request.content_length
        if content_length is None:
            abort(411, "Length Required")
        if content_length > MAX_PAYLOAD_SIZE:
            abort(413, "Payload too large")
        
        
        content_type = request.content_type
        if content_type is None:
            abort(400, "Content Type required")
        if content_type != "image/jpeg":
            abort(415, "Unsupported content type")
        
        api_key = request.headers.get("X-API-KEY")
        serial_number = request.headers.get("Serial-Number")
        event_id = request.headers.get("Event-ID")
        
        if not api_key or not serial_number or not event_id:
            abort(400, "Missing required headers")
        
        if api_key != API_KEY:
            abort(401, "Unauthorized API Key")
        
        kwargs["serial_number"] = serial_number
        kwargs["event_id"] = event_id
        return await f(*args, **kwargs)
    
    return wrapper
            
        