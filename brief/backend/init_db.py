from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("/var/lib/cognitivelogic/brief/subscribers.sqlite3")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        db_path,
        timeout=5.0,
        isolation_level=None,
    )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = connect_db(db_path)
    try:
        conn.executescript(schema)

        result = conn.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise RuntimeError(f"SQLite integrity check failed: {result}")

        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        busy = conn.execute("PRAGMA busy_timeout").fetchone()[0]

        if fk != 1:
            raise RuntimeError("foreign_keys is not enabled")
        if str(journal).lower() != "wal":
            raise RuntimeError(f"journal_mode is not WAL: {journal}")
        if busy < 5000:
            raise RuntimeError(f"busy_timeout too low: {busy}")

    finally:
        conn.close()

    os.chmod(db_path, 0o600)


if __name__ == "__main__":
    override = os.getenv("BRIEF_DB_PATH")
    target = Path(override) if override else DEFAULT_DB_PATH

    initialize_database(target)

    stat = target.stat()
    print(f"database={target}")
    print(f"mode={oct(stat.st_mode & 0o777)}")
    print("status=OK")
