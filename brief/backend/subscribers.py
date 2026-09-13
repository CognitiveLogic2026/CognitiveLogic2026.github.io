from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .init_db import DEFAULT_DB_PATH, connect_db


CONFIRMATION_TTL_HOURS = 24
CONSENT_VERSION = "brief-p0-v1"
DEFAULT_SOURCE = "brief-web"


@dataclass(frozen=True)
class PendingSubscription:
    email: str
    confirmation_token: str
    confirmation_expires_at: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_email(email: str) -> str:
    normalized = (email or "").strip().lower()

    if not normalized:
        raise ValueError("email is required")

    if len(normalized) > 254:
        raise ValueError("email is too long")

    if normalized.count("@") != 1:
        raise ValueError("invalid email")

    local, domain = normalized.split("@", 1)

    if not local or not domain or "." not in domain:
        raise ValueError("invalid email")

    if any(ch.isspace() for ch in normalized):
        raise ValueError("invalid email")

    return normalized


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def resolve_db_path(db_path: Path | None = None) -> Path:
    if db_path is not None:
        return Path(db_path)

    override = os.getenv("BRIEF_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def create_pending_subscription(
    email: str,
    *,
    db_path: Path | None = None,
    source: str = DEFAULT_SOURCE,
    consent_version: str = CONSENT_VERSION,
) -> PendingSubscription:
    normalized = normalize_email(email)

    now = utc_now()
    now_s = iso_utc(now)
    expires_s = iso_utc(now + timedelta(hours=CONFIRMATION_TTL_HOURS))

    token = generate_token()
    token_hash = hash_token(token)

    conn = connect_db(resolve_db_path(db_path))

    try:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            """
            SELECT id, status
            FROM subscribers
            WHERE email = ?
            """,
            (normalized,),
        ).fetchone()

        if row is None:
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
                    confirmation_token_hash,
                    confirmation_expires_at
                )
                VALUES (?, 'pending', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized,
                    now_s,
                    now_s,
                    now_s,
                    consent_version,
                    source,
                    token_hash,
                    expires_s,
                ),
            )

        elif row[1] == "pending":
            conn.execute(
                """
                UPDATE subscribers
                SET
                    updated_at = ?,
                    consent_at = ?,
                    consent_version = ?,
                    source = ?,
                    confirmation_token_hash = ?,
                    confirmation_expires_at = ?
                WHERE id = ?
                """,
                (
                    now_s,
                    now_s,
                    consent_version,
                    source,
                    token_hash,
                    expires_s,
                    row[0],
                ),
            )

        elif row[1] == "active":
            conn.rollback()
            raise ValueError("email already subscribed")

        elif row[1] == "unsubscribed":
            conn.execute(
                """
                UPDATE subscribers
                SET
                    status = 'pending',
                    updated_at = ?,
                    consent_at = ?,
                    consent_version = ?,
                    source = ?,
                    confirmation_token_hash = ?,
                    confirmation_expires_at = ?,
                    confirmed_at = NULL,
                    unsubscribe_token_hash = NULL,
                    unsubscribed_at = NULL
                WHERE id = ?
                """,
                (
                    now_s,
                    now_s,
                    consent_version,
                    source,
                    token_hash,
                    expires_s,
                    row[0],
                ),
            )

        else:
            conn.rollback()
            raise RuntimeError(f"unsupported subscriber status: {row[1]}")

        conn.commit()

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()

    return PendingSubscription(
        email=normalized,
        confirmation_token=token,
        confirmation_expires_at=expires_s,
    )


@dataclass(frozen=True)
class ConfirmedSubscription:
    email: str
    unsubscribe_token: str
    confirmed_at: str


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def confirm_subscription(
    confirmation_token: str,
    *,
    db_path: Path | None = None,
) -> ConfirmedSubscription:
    token = (confirmation_token or "").strip()

    if not token:
        raise ValueError("confirmation token is required")

    token_hash = hash_token(token)
    now = utc_now()
    now_s = iso_utc(now)

    unsubscribe_token = generate_token()
    unsubscribe_token_hash = hash_token(unsubscribe_token)

    conn = connect_db(resolve_db_path(db_path))

    try:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            """
            SELECT
                id,
                email,
                status,
                confirmation_expires_at
            FROM subscribers
            WHERE confirmation_token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if row is None:
            conn.rollback()
            raise ValueError("invalid confirmation token")

        subscriber_id, email, status, expires_at = row

        if status != "pending":
            conn.rollback()
            raise ValueError("subscription is not pending")

        if not expires_at:
            conn.rollback()
            raise ValueError("confirmation token has no expiry")

        if parse_utc(expires_at) <= now:
            conn.rollback()
            raise ValueError("confirmation token expired")

        conn.execute(
            """
            UPDATE subscribers
            SET
                status = 'active',
                updated_at = ?,
                confirmed_at = ?,
                confirmation_token_hash = NULL,
                confirmation_expires_at = NULL,
                unsubscribe_token_hash = ?,
                unsubscribed_at = NULL
            WHERE id = ?
            """,
            (
                now_s,
                now_s,
                unsubscribe_token_hash,
                subscriber_id,
            ),
        )

        conn.commit()

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()

    return ConfirmedSubscription(
        email=email,
        unsubscribe_token=unsubscribe_token,
        confirmed_at=now_s,
    )


@dataclass(frozen=True)
class UnsubscribedSubscription:
    email: str
    unsubscribed_at: str


def unsubscribe_subscription(
    unsubscribe_token: str,
    *,
    db_path: Path | None = None,
) -> UnsubscribedSubscription:
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
                id,
                email,
                status
            FROM subscribers
            WHERE unsubscribe_token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if row is None:
            conn.rollback()
            raise ValueError("invalid unsubscribe token")

        subscriber_id, email, status = row

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
            (
                now_s,
                now_s,
                subscriber_id,
            ),
        )

        conn.commit()

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()

    return UnsubscribedSubscription(
        email=email,
        unsubscribed_at=now_s,
    )


DELIVERY_STATUSES = frozenset({
    "sent",
    "delivered",
    "soft_bounce",
    "hard_bounce",
    "failed",
})


def update_delivery_status(
    email: str,
    status: str,
    *,
    error: str | None = None,
    db_path: Path | None = None,
) -> None:
    normalized = normalize_email(email)
    delivery_status = (status or "").strip()

    if delivery_status not in DELIVERY_STATUSES:
        raise ValueError("unsupported delivery status")

    now_s = iso_utc(utc_now())

    safe_error = (error or "").strip() or None
    if safe_error is not None:
        safe_error = safe_error[:500]

    sent_at = now_s if delivery_status == "sent" else None
    bounce_at = (
        now_s
        if delivery_status in {"soft_bounce", "hard_bounce"}
        else None
    )

    conn = connect_db(resolve_db_path(db_path))

    try:
        conn.execute("BEGIN IMMEDIATE")

        row = conn.execute(
            """
            SELECT id
            FROM subscribers
            WHERE email = ?
            """,
            (normalized,),
        ).fetchone()

        if row is None:
            conn.rollback()
            raise ValueError("subscriber not found")

        conn.execute(
            """
            UPDATE subscribers
            SET
                updated_at = ?,
                last_email_sent_at = COALESCE(?, last_email_sent_at),
                last_delivery_status = ?,
                last_delivery_error = ?,
                last_bounce_at = COALESCE(?, last_bounce_at)
            WHERE id = ?
            """,
            (
                now_s,
                sent_at,
                delivery_status,
                safe_error,
                bounce_at,
                row[0],
            ),
        )

        conn.commit()

    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()
