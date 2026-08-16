import asyncio
import logging
from quart import Blueprint, request, jsonify

import bot.dc_bot as bot_module
from db import db_module
from api.storage import save_uploaded_image
from api.auth import validate_request

logger = logging.getLogger(__name__)

doorbell_bp = Blueprint("doorbell", __name__)

MAX_PAYLOAD_SIZE = 5 * 1024 * 1024


@doorbell_bp.route("/doorbell", methods=["POST"])
async def doorbell_event():
    content_length = request.content_length
    if content_length is None:
        return jsonify({"error": "Length Required"}), 411

    if content_length > MAX_PAYLOAD_SIZE:
        return jsonify({"error": "Payload too large"}), 413

    serial_number, response, code = await validate_request()
    if not serial_number:
        return response, code

    event_id = request.headers.get("Event-ID")

    try:
        is_new_event = await db_module.add_event(serial_number, event_id)
    except Exception:
        logger.exception(
            "Database failure recording event %s for serial %s",
            event_id,
            serial_number,
        )
        return jsonify({"error": "Database operation failed"}), 500

    if not is_new_event:
        logger.info(
            "Ignored duplicate event %s for serial %s", event_id, serial_number
        )
        return jsonify({"status": "success"}), 200

    try:
        subscriptions = await db_module.get_device_subscriptions(serial_number)
    except Exception:
        logger.exception(
            "Database failure retrieving subscriptions for serial %s",
            serial_number,
        )
        return jsonify({"error": "Database operation failed"}), 500

    if not subscriptions:
        logger.info("No active subscriptions for serial %s", serial_number)
        return jsonify({"status": "no subscriptions configured"}), 200

    raw_data: bytes = await request.get_data()
    if not raw_data:
        return jsonify({"error": "No image data found"}), 400

    try:
        file_path: str = await save_uploaded_image(raw_data)
    except Exception:
        logger.exception(
            "Failed to save image payload for event %s", event_id
        )
        return jsonify({"error": "Failed to process image payload"}), 500

    notification_cog = bot_module.bot.get_cog("NotificationCog")
    if not notification_cog:
        logger.error(
            "NotificationCog unavailable; cannot dispatch alert for event %s",
            event_id,
        )
        return jsonify({"error": "Notification service unavailable"}), 503

    asyncio.create_task(
        notification_cog.send_discord_notification(file_path, subscriptions)
    )

    return jsonify({"status": "success"}), 200