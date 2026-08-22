import asyncio
import logging
from quart import Blueprint, request, jsonify, abort

import bot.dc_bot as bot_module
from db import db_module
from api.storage import save_uploaded_image, is_valid_jpeg
from api.auth import validate_request
from config import BOT_SERVICES

logger = logging.getLogger(__name__)

doorbell_bp = Blueprint("doorbell", __name__)



doorbell_bp.route

@doorbell_bp.route("/doorbell", methods=["POST"])
@validate_request
async def doorbell_event(serial_number, event_id):

    raw_data: bytes = await request.get_data()
    if not raw_data:
        abort(400, "No image data found")
    
    if not is_valid_jpeg(raw_data):
        logger.warning("Rejected payload from serial %s: invalid JPEG signature", serial_number)
        abort(415, "Invalid image format")
    
    try:
        is_new_event = await db_module.add_event(serial_number, event_id)
    except Exception:
        logger.exception(
            "Database failure recording event %s for serial %s",
            event_id,
            serial_number,
        )
        abort(500, "Database operation failed")


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
        abort(500, "Database operation failed")

    if not subscriptions:
        logger.info("No active subscriptions for serial %s", serial_number)
        return jsonify({"status": "no subscriptions configured"}), 200


    try:
        file_path: str = await save_uploaded_image(raw_data)
    except Exception:
        logger.exception(
            "Failed to save image payload for event %s", event_id
        )
        abort(500, "Failed to process image payload")

    if BOT_SERVICES:
        notification_cog = bot_module.bot.get_cog("NotificationCog")
        if not notification_cog:
            logger.error(
                "NotificationCog unavailable; cannot dispatch alert for event %s",
                event_id,
            )
            abort(503, "Notification service unavailable")
        asyncio.create_task(
            notification_cog.send_discord_notification(file_path, subscriptions)
        )
    else:
        logger.info("Bot services are disabled via configuration.")

    return jsonify({"status": "success"}), 200