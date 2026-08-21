from quart import Blueprint, jsonify
from werkzeug.exceptions import HTTPException

errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(HTTPException)
def handle_http_exception(error: HTTPException):
    response = jsonify({
        "status": "error",
        "error": {
            "type": error.name,
            "message": error.description
        }
    })
    response.status_code = error.code
    return response
    