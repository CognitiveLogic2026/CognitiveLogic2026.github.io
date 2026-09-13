from __future__ import annotations

import json
import os

from svix.webhooks import Webhook, WebhookVerificationError

from .subscribers import update_delivery_status


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


def verify_and_process_resend_webhook(
    raw_body: bytes,
    headers: dict[str, str],
) -> str:
    secret = _required_env("RESEND_WEBHOOK_SECRET")

    webhook = Webhook(secret)

    try:
        webhook.verify(raw_body, headers)
    except WebhookVerificationError as exc:
        raise ValueError("invalid webhook signature") from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid webhook payload") from exc

    event_type = payload.get("type")
    data = payload.get("data") or {}

    to_value = data.get("to")

    if isinstance(to_value, list):
        email = to_value[0] if to_value else None
    else:
        email = to_value

    if not email:
        return "ignored"

    if event_type == "email.delivered":
        update_delivery_status(email, "delivered")
        return "delivered"

    if event_type == "email.failed":
        update_delivery_status(
            email,
            "failed",
            error="Resend reported email.failed",
        )
        return "failed"

    if event_type == "email.bounced":
        bounce = data.get("bounce") or {}
        bounce_type = (bounce.get("type") or "").strip()

        if bounce_type == "Permanent":
            update_delivery_status(
                email,
                "hard_bounce",
                error="Resend bounce: Permanent",
            )
            return "hard_bounce"

        if bounce_type == "Transient":
            update_delivery_status(
                email,
                "soft_bounce",
                error="Resend bounce: Transient",
            )
            return "soft_bounce"

        update_delivery_status(
            email,
            "failed",
            error=f"Resend bounce: {bounce_type or 'Undetermined'}",
        )
        return "failed"

    return "ignored"
