from __future__ import annotations

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from init_db import DEFAULT_DB_PATH, connect_db


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


def create_pending_subscription(
    email: str,
    *,
    db_path: Path = DEFAULT_DB_PATH,
    source: str = DEFAULT_SOURCE,
    consent_version: str = CONSENT_VERSION,
) -> PendingSubscription:
    normalized = normalize_email(email)

    now = utc_now()
    now_s = iso_utc(now)
    expires_s = iso_utc(now + timedelta(hours=CONFIRMATION_TTL_HOURS))

    token = generate_token()
    token_hash = hash_token(token)

    conn = connect_db(Path(db_path))

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
