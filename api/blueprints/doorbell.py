import logging
from quart import Blueprint, request, jsonify, abort


import api.validation as validation
import services.doorbell_service as service
from services.doorbell_service import EventProcessed, NoSubscriptionsFound, DuplicateEventIgnored
import core.exceptions as exceptions


logger = logging.getLogger(__name__)

doorbell_bp = Blueprint("doorbell", __name__)


@doorbell_bp.route("/doorbell", methods=["POST"])
@validation.validate_headers
async def doorbell_event(serial_number, event_id):
    raw_data: bytes = await request.get_data()
    if not raw_data:
        abort(400, "No image data found")
    
    try:
        result = await service.process_doorbell_event(serial_number, event_id, raw_data)
        match result:
            case DuplicateEventIgnored():
                return jsonify({"status": "success", "message": "Duplicate Event Ignored"}), 200
            case NoSubscriptionsFound():
                return jsonify({"status": "success", "message": "No Active Subscriptions Configured"}), 200
            case EventProcessed():
                return jsonify({"status": "success", "message": "Event Processed Successfully"}), 200
            case _:
                logger.error("Received unhandled process result type: %s", type(result))
                abort(500, "Internal Server Error")
    except exceptions.DeviceUnauthorizedError:
        abort(403, "Device Unauthorized")
    except exceptions.InvalidImageFormatError:
        abort(415, "Invalid Image Format")
    except exceptions.NotificationServiceError:
        abort(503, "Service Unavailable")
    except (exceptions.DatabaseError, exceptions.ImageProcessingError):
        abort(500, "Internal Server Error")
    except Exception:
        logger.exception("Unhandled unexpected exception during doorbell processing")
        abort(500, "Internal Server Error")