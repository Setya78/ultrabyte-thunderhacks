"""Database access. Connection string comes only from the DATABASE_URL env var (HS2)."""
import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL") or None


@contextmanager
def connect():
    url = database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    with psycopg.connect(url, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def status() -> dict:
    """Health detail: whether the DB is reachable and how much seed data is loaded."""
    if not database_url():
        return {"db": "not_configured"}
    try:
        with connect() as conn:
            row = conn.execute(
                "SELECT (SELECT count(*) FROM player) AS players,"
                " (SELECT count(*) FROM txn) AS txns,"
                " (SELECT count(*) FROM audit_event) AS audit_events"
            ).fetchone()
        return {"db": "ok", **row}
    except Exception as exc:  # report, do not crash the health endpoint
        return {"db": "error", "detail": type(exc).__name__}
