-- Cognitive Logic Brief
-- Proprietary subscriber database schema — P0
-- The runtime database lives outside the repository:
-- /var/lib/cognitivelogic/brief/subscribers.sqlite3

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    email TEXT NOT NULL COLLATE NOCASE UNIQUE,

    status TEXT NOT NULL
        CHECK (status IN ('pending', 'active', 'unsubscribed')),

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    consent_at TEXT NOT NULL,
    consent_version TEXT NOT NULL,
    source TEXT NOT NULL,

    confirmation_token_hash TEXT,
    confirmation_expires_at TEXT,
    confirmed_at TEXT,

    unsubscribe_token_hash TEXT,
    unsubscribed_at TEXT,

    last_email_sent_at TEXT,
    last_delivery_status TEXT
        CHECK (
            last_delivery_status IS NULL OR
            last_delivery_status IN (
                'sent',
                'delivered',
                'soft_bounce',
                'hard_bounce',
                'failed'
            )
        ),
    last_delivery_error TEXT,
    last_bounce_at TEXT,

    CHECK (
        status != 'active'
        OR confirmed_at IS NOT NULL
    ),

    CHECK (
        status != 'unsubscribed'
        OR unsubscribed_at IS NOT NULL
    ),

    CHECK (
        status != 'pending'
        OR (
            confirmation_token_hash IS NOT NULL
            AND confirmation_expires_at IS NOT NULL
        )
    ),

    CHECK (
        status != 'active'
        OR unsubscribe_token_hash IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_subscribers_status
    ON subscribers(status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_confirmation_token
    ON subscribers(confirmation_token_hash)
    WHERE confirmation_token_hash IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_unsubscribe_token
    ON subscribers(unsubscribe_token_hash)
    WHERE unsubscribe_token_hash IS NOT NULL;
