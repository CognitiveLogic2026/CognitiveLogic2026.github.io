from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .init_db import connect_db
from .subscribers import (
    generate_token,
    hash_token,
    iso_utc,
    normalize_email,
    resolve_db_path,
    utc_now,
)


ISSUE_SLUG_PATTERN = re.compile(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
)

DELIVERY_STATUSES = frozenset({
    "pending",
    "sent",
    "delivered",
    "soft_bounce",
    "hard_bounce",
    "failed",
})


@dataclass(frozen=True)
class IssueDelivery:
    id: int
    email: str
    issue_slug: str
    unsubscribe_token: str
    created_at: str


def normalize_issue_slug(issue_slug: str) -> str:
    normalized = (issue_slug or "").strip().lower()

    if not ISSUE_SLUG_PATTERN.fullmatch(normalized):
        raise ValueError("invalid issue slug")

    return normalized


def create_issue_delivery(
    email: str,
    issue_slug: str,
    *,
    db_path: Path | None = None,
) -> IssueDelivery:
    normalized_email = normalize_email(email)
    normalized_issue = normalize_issue_slug(issue_slug)

    token = generate_token()
    token_hash = hash_token(token)
    now_s = iso_utc(utc_now())

    conn = connect_db(resolve_db_path(db_path))

    try:
        conn.execute("BEGIN IMMEDIATE")

        subscriber = conn.execute(
            """
            SELECT id
            FROM subscribers
            WHERE email = ?
              AND status = 'active'
            """,
            (normalized_email,),
        ).fetchone()

        if subscriber is None:
            conn.rollback()
            raise ValueError("active subscriber not found")

        try:
            cursor = conn.execute(
                """
                INSERT INTO brief_issue_deliveries (
                    subscriber_id,
                    issue_slug,
                    created_at,
                    updated_at,
                    unsubscribe_token_hash,
                    delivery_status
                )
                VALUES (?, ?, ?, ?, ?, 'pending')
                """,
                (
                    subscriber[0],
                    normalized_issue,
                    now_s,
                    now_s,
                    token_hash,
                ),
            )
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise ValueError(
                "delivery already exists for subscriber and issue"
            ) from exc

        delivery_id = int(cursor.lastrowid)
        conn.commit()

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()

    return IssueDelivery(
        id=delivery_id,
        email=normalized_email,
        issue_slug=normalized_issue,
        unsubscribe_token=token,
        created_at=now_s,
    )


def update_issue_delivery(
    delivery_id: int,
    status: str,
    *,
    resend_email_id: str | None = None,
    error: str | None = None,
    db_path: Path | None = None,
) -> None:
    delivery_status = (status or "").strip()

    if delivery_status not in DELIVERY_STATUSES:
        raise ValueError("unsupported delivery status")

    now_s = iso_utc(utc_now())
    safe_error = (error or "").strip()[:500] or None
    safe_resend_id = (resend_email_id or "").strip() or None

    sent_at = now_s if delivery_status == "sent" else None
    delivered_at = (
        now_s if delivery_status == "delivered" else None
    )
    bounced_at = (
        now_s
        if delivery_status in {"soft_bounce", "hard_bounce"}
        else None
    )

    conn = connect_db(resolve_db_path(db_path))

    try:
        conn.execute("BEGIN IMMEDIATE")

        cursor = conn.execute(
            """
            UPDATE brief_issue_deliveries
            SET
                updated_at = ?,
                resend_email_id =
                    COALESCE(?, resend_email_id),
                delivery_status = ?,
                last_delivery_error = ?,
                sent_at = COALESCE(?, sent_at),
                delivered_at = COALESCE(?, delivered_at),
                bounced_at = COALESCE(?, bounced_at)
            WHERE id = ?
            """,
            (
                now_s,
                safe_resend_id,
                delivery_status,
                safe_error,
                sent_at,
                delivered_at,
                bounced_at,
                delivery_id,
            ),
        )

        if cursor.rowcount != 1:
            conn.rollback()
            raise ValueError("issue delivery not found")

        conn.commit()

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()


def update_issue_delivery_by_resend_id(
    resend_email_id: str,
    status: str,
    *,
    error: str | None = None,
    db_path: Path | None = None,
) -> bool:
    email_id = (resend_email_id or "").strip()

    if not email_id:
        return False

    conn = connect_db(resolve_db_path(db_path))

    try:
        row = conn.execute(
            """
            SELECT id
            FROM brief_issue_deliveries
            WHERE resend_email_id = ?
            """,
            (email_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return False

    update_issue_delivery(
        int(row[0]),
        status,
        error=error,
        db_path=db_path,
    )

    return True


def unsubscribe_issue_delivery(
    unsubscribe_token: str,
    *,
    db_path: Path | None = None,
) -> str:
    token = (unsubscribe_token or "").strip()

    if not token:
        raise ValueError("unsubscribe token is required")

    token_hash = hash_token(token)
    now_s = iso_utc(utc_now())

    conn = connect_db(resolve_db_path(db_path))

    try:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            """
            SELECT
                d.id,
                d.subscriber_id,
                s.email,
                s.status
            FROM brief_issue_deliveries AS d
            JOIN subscribers AS s
              ON s.id = d.subscriber_id
            WHERE d.unsubscribe_token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if row is None:
            conn.rollback()
            raise ValueError("invalid unsubscribe token")

        delivery_id, subscriber_id, email, status = row

        if status != "active":
            conn.rollback()
            raise ValueError("subscription is not active")

        conn.execute(
            """
            UPDATE subscribers
            SET
                status = 'unsubscribed',
                updated_at = ?,
                unsubscribed_at = ?
            WHERE id = ?
            """,
            (now_s, now_s, subscriber_id),
        )

        conn.execute(
            """
            UPDATE brief_issue_deliveries
            SET updated_at = ?
            WHERE id = ?
            """,
            (now_s, delivery_id),
        )

        conn.commit()
        return str(email)

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()
