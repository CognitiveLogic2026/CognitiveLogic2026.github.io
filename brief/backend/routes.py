from __future__ import annotations

from collections.abc import Callable

from flask import Blueprint, current_app, jsonify, request

from .subscribers import (
    confirm_subscription,
    create_pending_subscription,
    unsubscribe_subscription,
)


brief_bp = Blueprint("brief", __name__)

CONFIRMATION_SENDER_CONFIG = "BRIEF_CONFIRMATION_SENDER"


def _json_error(message: str, status: int):
    return jsonify({
        "status": "error",
        "message": message,
    }), status


def _confirmation_sender() -> Callable[[str, str], None] | None:
    sender = current_app.config.get(CONFIRMATION_SENDER_CONFIG)
    return sender if callable(sender) else None


@brief_bp.post("/brief/subscribe")
def brief_subscribe():
    sender = _confirmation_sender()

    if sender is None:
        return _json_error(
            "Subscription service is temporarily unavailable.",
            503,
        )

    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")

    try:
        pending = create_pending_subscription(email)
    except ValueError:
        # Generic response: do not disclose whether an address is already active.
        return jsonify({
            "status": "ok",
            "message": (
                "If the address can be subscribed, "
                "confirmation instructions will be sent."
            ),
        }), 200

    try:
        sender(
            pending.email,
            pending.confirmation_token,
        )
    except Exception:
        current_app.logger.exception(
            "Brief confirmation delivery failed"
        )
        return _json_error(
            "Subscription service is temporarily unavailable.",
            503,
        )

    return jsonify({
        "status": "ok",
        "message": (
            "If the address can be subscribed, "
            "confirmation instructions will be sent."
        ),
    }), 200


@brief_bp.get("/brief/confirm")
def brief_confirm():
    token = request.args.get("token", "")

    try:
        confirm_subscription(token)
    except ValueError:
        return _json_error(
            "Invalid or expired confirmation link.",
            400,
        )

    return jsonify({
        "status": "active",
        "message": "Subscription confirmed.",
    }), 200


@brief_bp.get("/brief/unsubscribe")
def brief_unsubscribe():
    token = request.args.get("token", "")

    try:
        unsubscribe_subscription(token)
    except ValueError:
        return _json_error(
            "Invalid unsubscribe link.",
            400,
        )

    return jsonify({
        "status": "unsubscribed",
        "message": "Subscription cancelled.",
    }), 200
