from __future__ import annotations

from collections.abc import Callable

from flask import Blueprint, current_app, jsonify, redirect, request

from .issue_deliveries import unsubscribe_issue_delivery
from .resend_webhook import verify_and_process_resend_webhook

from .subscribers import (
    confirm_subscription,
    create_pending_subscription,
    unsubscribe_subscription,
)


CONFIRMATION_SENDER_CONFIG = "BRIEF_CONFIRMATION_SENDER"
SUBSCRIBE_RATE_LIMIT = "5 per minute;20 per hour"


def _json_error(message: str, status: int):
    return jsonify({
        "status": "error",
        "message": message,
    }), status


def _confirmation_sender() -> Callable[[str, str], None] | None:
    sender = current_app.config.get(CONFIRMATION_SENDER_CONFIG)
    return sender if callable(sender) else None


def create_brief_blueprint(limiter=None) -> Blueprint:
    brief_bp = Blueprint("brief", __name__)
    _lim = limiter.limit if limiter else lambda _rule: (lambda f: f)

    @brief_bp.post("/brief/subscribe")
    @_lim(SUBSCRIBE_RATE_LIMIT)
    def brief_subscribe():
        sender = _confirmation_sender()

        if sender is None:
            return _json_error(
                "Subscription service is temporarily unavailable.",
                503,
            )

        payload = request.get_json(silent=True) or {}
        email = payload.get("email", "")
        consent = payload.get("consent") is True

        if not consent:
            return _json_error(
                "Consent is required.",
                400,
            )

        try:
            pending = create_pending_subscription(
                email,
                source="brief-web",
            )
        except ValueError:
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

        return redirect("/brief/confirmed/", code=302)

    @brief_bp.route(
        "/brief/unsubscribe",
        methods=["GET", "POST"],
    )
    def brief_unsubscribe():
        token = request.args.get("token", "")

        try:
            unsubscribe_subscription(token)
        except ValueError:
            try:
                unsubscribe_issue_delivery(token)
            except ValueError:
                return _json_error(
                    "Invalid unsubscribe link.",
                    400,
                )

        if request.method == "POST":
            return jsonify({
                "status": "ok",
                "message": "Subscription removed.",
            }), 200

        return redirect("/brief/unsubscribed/", code=302)


    @brief_bp.post("/brief/webhook/resend")
    def resend_webhook():
        raw_body = request.get_data(cache=False)

        headers = {
            "svix-id": request.headers.get("svix-id", ""),
            "svix-timestamp": request.headers.get("svix-timestamp", ""),
            "svix-signature": request.headers.get("svix-signature", ""),
        }

        try:
            result = verify_and_process_resend_webhook(
                raw_body,
                headers,
            )
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid webhook.",
            }), 400
        except RuntimeError:
            return jsonify({
                "status": "error",
                "message": "Webhook unavailable.",
            }), 503

        return jsonify({
            "status": "ok",
            "result": result,
        }), 200

    return brief_bp
