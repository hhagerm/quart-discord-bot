from quart import request, jsonify, Response
from config import API_KEY
from db import db_module

async def validate_request() -> tuple[str | None, Response | None, int | None]:
        if request.headers.get("X-API-Key") != API_KEY:
            return None, jsonify({"error": "Unauthorized"}), 401
        
        serial_number: str = request.headers.get("Serial-Number")
        if not serial_number or not await db_module.validate_serial_num(serial_number):
            return None, jsonify({"error": "Device unauthorized"}), 403
        
        return serial_number, None, None