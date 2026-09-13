import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from flask import Flask

from brief.backend.init_db import initialize_database
from brief.backend.issue_deliveries import (
    create_issue_delivery,
    unsubscribe_issue_delivery,
    update_issue_delivery,
)
from brief.backend.resend_webhook import (
    verify_and_process_resend_webhook,
)
from brief.backend.routes import create_brief_blueprint
from brief.backend.send_issue import (
    render_number_zero,
    send_number_zero,
)


def add_active_subscriber(db: Path) -> None:
    conn = sqlite3.connect(db)
    conn.execute(
        """
        INSERT INTO subscribers (
            email,
            status,
            created_at,
            updated_at,
            consent_at,
            consent_version,
            source,
            confirmed_at,
            unsubscribe_token_hash
        )
        VALUES (?, 'active', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test@example.com",
            "2026-09-13T00:00:00Z",
            "2026-09-13T00:00:00Z",
            "2026-09-13T00:00:00Z",
            "brief-p0-v1",
            "test",
            "2026-09-13T00:00:00Z",
            "existing-hash",
        ),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def brief_db(tmp_path, monkeypatch):
    db = tmp_path / "brief.sqlite3"
    initialize_database(db)
    add_active_subscriber(db)
    monkeypatch.setenv("BRIEF_DB_PATH", str(db))
    return db


def test_issue_delivery_and_unsubscribe(brief_db):
    delivery = create_issue_delivery(
        "test@example.com",
        "numero-zero-test",
        db_path=brief_db,
    )

    update_issue_delivery(
        delivery.id,
        "sent",
        resend_email_id="resend-test-id",
        db_path=brief_db,
    )

    email = unsubscribe_issue_delivery(
        delivery.unsubscribe_token,
        db_path=brief_db,
    )

    conn = sqlite3.connect(brief_db)
    subscriber_status = conn.execute(
        "SELECT status FROM subscribers WHERE email = ?",
        ("test@example.com",),
    ).fetchone()[0]
    delivery_status = conn.execute(
        """
        SELECT delivery_status
        FROM brief_issue_deliveries
        WHERE resend_email_id = ?
        """,
        ("resend-test-id",),
    ).fetchone()[0]
    conn.close()

    assert email == "test@example.com"
    assert subscriber_status == "unsubscribed"
    assert delivery_status == "sent"


def test_one_click_unsubscribe_route(brief_db):
    delivery = create_issue_delivery(
        "test@example.com",
        "numero-zero-test",
        db_path=brief_db,
    )

    app = Flask(__name__)
    app.register_blueprint(create_brief_blueprint())
    client = app.test_client()

    response = client.post(
        "/brief/unsubscribe",
        query_string={
            "token": delivery.unsubscribe_token,
        },
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_number_zero_rendering():
    subject, text, html = render_number_zero(
        "https://example.com/unsubscribe?token=test",
        test=True,
    )

    assert subject.startswith("[TEST]")
    assert "Non tutto ciò che cambia" in subject
    assert "Disiscriviti:" in text
    assert "List-Unsubscribe" not in html
    assert "Numero Zero" in html
    assert "fuorimenu.substack.com" in html


def test_mock_send_records_resend_id(
    brief_db,
    monkeypatch,
):
    monkeypatch.setenv("RESEND_API_KEY", "test-key")
    monkeypatch.setenv(
        "BRIEF_FROM_EMAIL",
        "Cognitive Logic Brief <brief@example.com>",
    )

    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "id": "mock-resend-email-id",
    }

    with patch(
        "brief.backend.send_issue.requests.post",
        return_value=response,
    ) as post:
        email_id = send_number_zero(
            "test@example.com",
            test=True,
            db_path=brief_db,
        )

    payload = post.call_args.kwargs["json"]
    request_headers = post.call_args.kwargs["headers"]

    assert email_id == "mock-resend-email-id"
    assert payload["to"] == ["test@example.com"]
    assert payload["subject"].startswith("[TEST]")
    assert (
        payload["headers"]["List-Unsubscribe-Post"]
        == "List-Unsubscribe=One-Click"
    )
    assert request_headers["Idempotency-Key"].startswith(
        "brief-numero-zero-test-"
    )

    conn = sqlite3.connect(brief_db)
    row = conn.execute(
        """
        SELECT
            issue_slug,
            resend_email_id,
            delivery_status
        FROM brief_issue_deliveries
        """
    ).fetchone()
    conn.close()

    assert row == (
        "numero-zero-test",
        "mock-resend-email-id",
        "sent",
    )


def test_webhook_updates_exact_delivery(
    brief_db,
    monkeypatch,
):
    monkeypatch.setenv(
        "RESEND_WEBHOOK_SECRET",
        "whsec_test",
    )

    delivery = create_issue_delivery(
        "test@example.com",
        "numero-zero-test",
        db_path=brief_db,
    )

    update_issue_delivery(
        delivery.id,
        "sent",
        resend_email_id="webhook-email-id",
        db_path=brief_db,
    )

    payload = {
        "type": "email.delivered",
        "data": {
            "email_id": "webhook-email-id",
            "to": ["test@example.com"],
        },
    }

    with patch(
        "brief.backend.resend_webhook.Webhook"
    ) as webhook:
        webhook.return_value.verify.return_value = payload

        result = verify_and_process_resend_webhook(
            json.dumps(payload).encode("utf-8"),
            {
                "svix-id": "test-id",
                "svix-timestamp": "1",
                "svix-signature": "test-signature",
            },
        )

    conn = sqlite3.connect(brief_db)
    status = conn.execute(
        """
        SELECT delivery_status
        FROM brief_issue_deliveries
        WHERE resend_email_id = ?
        """,
        ("webhook-email-id",),
    ).fetchone()[0]
    conn.close()

    assert result == "delivered"
    assert status == "delivered"
