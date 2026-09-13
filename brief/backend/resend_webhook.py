from __future__ import annotations

import json
import os

from svix.webhooks import Webhook, WebhookVerificationError

from .issue_deliveries import update_issue_delivery_by_resend_id
from .subscribers import update_delivery_status


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


def _update_known_subscriber(
    email: str,
    status: str,
    *,
    error: str | None = None,
) -> bool:
    try:
        update_delivery_status(
            email,
            status,
            error=error,
        )
    except ValueError:
        return False

    return True


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
    resend_email_id = str(data.get("email_id") or "").strip()

    to_value = data.get("to")

    if isinstance(to_value, list):
        email = to_value[0] if to_value else None
    else:
        email = to_value

    if not email:
        return "ignored"

    if event_type == "email.delivered":
        update_issue_delivery_by_resend_id(
            resend_email_id,
            "delivered",
        )
        if not _update_known_subscriber(email, "delivered"):
            return "ignored"
        return "delivered"

    if event_type == "email.failed":
        delivery_error = "Resend reported email.failed"
        update_issue_delivery_by_resend_id(
            resend_email_id,
            "failed",
            error=delivery_error,
        )
        if not _update_known_subscriber(
            email,
            "failed",
            error="Resend reported email.failed",
        ):
            return "ignored"
        return "failed"

    if event_type == "email.bounced":
        bounce = data.get("bounce") or {}
        bounce_type = (bounce.get("type") or "").strip()

        if bounce_type == "Permanent":
            bounce_error = "Resend bounce: Permanent"
            update_issue_delivery_by_resend_id(
                resend_email_id,
                "hard_bounce",
                error=bounce_error,
            )
            if not _update_known_subscriber(
                email,
                "hard_bounce",
                error="Resend bounce: Permanent",
            ):
                return "ignored"
            return "hard_bounce"

        if bounce_type == "Transient":
            bounce_error = "Resend bounce: Transient"
            update_issue_delivery_by_resend_id(
                resend_email_id,
                "soft_bounce",
                error=bounce_error,
            )
            if not _update_known_subscriber(
                email,
                "soft_bounce",
                error="Resend bounce: Transient",
            ):
                return "ignored"
            return "soft_bounce"

        bounce_error = (
            f"Resend bounce: {bounce_type or 'Undetermined'}"
        )
        update_issue_delivery_by_resend_id(
            resend_email_id,
            "failed",
            error=bounce_error,
        )
        if not _update_known_subscriber(
            email,
            "failed",
            error=bounce_error,
        ):
            return "ignored"
        return "failed"

    return "ignored"
