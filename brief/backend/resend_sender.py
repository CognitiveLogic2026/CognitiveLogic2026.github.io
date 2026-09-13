from __future__ import annotations

import os
from urllib.parse import urlencode

import requests

from .subscribers import update_delivery_status


RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_PUBLIC_BASE_URL = "https://cognitivelogic.it"


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is not configured")
    return value


def build_confirmation_url(token: str) -> str:
    token = (token or "").strip()
    if not token:
        raise ValueError("confirmation token is required")

    base_url = os.getenv(
        "BRIEF_PUBLIC_BASE_URL",
        DEFAULT_PUBLIC_BASE_URL,
    ).rstrip("/")

    query = urlencode({"token": token})
    return f"{base_url}/brief/confirm?{query}"


def send_confirmation_email(email: str, confirmation_token: str) -> None:
    api_key = _required_env("RESEND_API_KEY")
    from_email = _required_env("BRIEF_FROM_EMAIL")

    confirmation_url = build_confirmation_url(confirmation_token)

    payload = {
        "from": from_email,
        "to": [email],
        "subject": "Conferma l'iscrizione a Cognitive Logic Brief",
        "text": (
            "Hai richiesto l'iscrizione a Cognitive Logic Brief.\n\n"
            "Conferma l'iscrizione entro 24 ore:\n"
            f"{confirmation_url}\n\n"
            "Se non hai richiesto questa iscrizione, ignora questa email."
        ),
        "html": (
            "<p>Hai richiesto l'iscrizione a "
            "<strong>Cognitive Logic Brief</strong>.</p>"
            "<p>Conferma l'iscrizione entro 24 ore:</p>"
            f'<p><a href="{confirmation_url}">Conferma iscrizione</a></p>'
            "<p>Se non hai richiesto questa iscrizione, "
            "ignora questa email.</p>"
        ),
    }

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
    except requests.RequestException as exc:
        error = f"Resend request failed: {exc.__class__.__name__}"
        try:
            update_delivery_status(email, "failed", error=error)
        except Exception:
            pass
        raise RuntimeError(error) from exc

    if not 200 <= response.status_code < 300:
        error = f"Resend delivery failed with HTTP {response.status_code}"
        try:
            update_delivery_status(email, "failed", error=error)
        except Exception:
            pass
        raise RuntimeError(error)

    try:
        update_delivery_status(email, "sent")
    except Exception:
        pass
