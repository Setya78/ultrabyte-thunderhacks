"""Append-only audit trail. Rows are only ever INSERTed; the database rejects UPDATE and DELETE."""
from psycopg.types.json import Jsonb

ACTIONS = {"escalate": "Escalate", "monitor": "Monitor", "dismiss": "Dismiss"}
LABELS = {**ACTIONS, "manual_entry": "Judge input", "ai_summary": "AI summary", "reset": "Reset", "note": "Note"}
ACTOR = "investigator (demo)"  # no authentication in the demo; disclosed in README


def record(conn, player_id: str, action: str, note: str, snapshot: dict) -> None:
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    conn.execute(
        "INSERT INTO audit_event (actor, player_id, action, note, score_snapshot) VALUES (%s, %s, %s, %s, %s)",
        (ACTOR, player_id, action, (note or "").strip()[:1000] or None, Jsonb(snapshot)),
    )
    conn.commit()


def for_player(conn, player_id: str) -> list[dict]:
    return conn.execute(
        "SELECT id, ts, actor, action, note, score_snapshot->>'score' AS score, score_snapshot->>'band' AS band"
        " FROM audit_event WHERE player_id = %s ORDER BY ts DESC, id DESC",
        (player_id,),
    ).fetchall()


def recent(conn, limit: int = 50) -> list[dict]:
    return conn.execute(
        "SELECT id, ts, actor, player_id, action, note, score_snapshot->>'score' AS score"
        " FROM audit_event ORDER BY ts DESC, id DESC LIMIT %s",
        (limit,),
    ).fetchall()
