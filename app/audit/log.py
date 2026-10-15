"""Append-only audit trail. Rows are only ever INSERTed; the database rejects UPDATE and DELETE."""
from psycopg.types.json import Jsonb

ACTIONS = {"escalate": "Escalate", "monitor": "Monitor", "dismiss": "Dismiss"}
# Case hand-off (owner 2026-10-15): compliance picks an escalated case up, then closes it. Same append-only table.
STATUS_ACTIONS = {"handling": "Mark as handling", "resolve": "Mark resolved"}
LABELS = {**ACTIONS, "handling": "In progress", "resolve": "Resolved", "manual_entry": "Manual entry", "ai_summary": "AI summary", "reset": "Reset", "note": "Note", "rule_change": "Rule change", "login": "Signed in", "logout": "Signed out"}
# What the latest decision-or-status row means for the case. Order = how the queue groups decided cases.
STATES = {
    "escalate": ("escalated", "Escalated, waiting for compliance"),
    "handling": ("handling", "In progress, compliance"),
    "monitor": ("monitor", "Monitor"),
    "dismiss": ("dismiss", "Dismissed"),
    "resolve": ("resolved", "Resolved"),
}
STATE_ORDER = ["escalated", "handling", "monitor", "dismiss", "resolved"]
ACTOR = "investigator (demo)"  # no authentication in the demo; disclosed in README


def record(conn, player_id: str, action: str, note: str, snapshot: dict, actor: str = ACTOR) -> None:
    if action not in ACTIONS and action not in STATUS_ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    conn.execute(
        "INSERT INTO audit_event (actor, player_id, action, note, score_snapshot) VALUES (%s, %s, %s, %s, %s)",
        (actor, player_id, action, (note or "").strip()[:1000] or None, Jsonb(snapshot)),
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


def case_status(conn) -> dict:
    """Latest decision-or-status row per player -> {player_id: {state, label, action, actor, ts}}. Read-only."""
    out = {}
    for d in conn.execute(
        "SELECT DISTINCT ON (player_id) player_id, action, actor, ts FROM audit_event"
        " WHERE action IN ('escalate','monitor','dismiss','handling','resolve') AND player_id IS NOT NULL"
        " ORDER BY player_id, ts DESC, id DESC").fetchall():
        state, label = STATES[d["action"]]
        out[d["player_id"]] = {"state": state, "label": label, "action": d["action"], "actor": d["actor"], "ts": d["ts"]}
    return out


def latest_notes(conn) -> dict:
    """Latest non-empty comment per player on a case decision or hand-off -> {player_id: {note, actor, ts}}. Read-only.
    Owner 2026-10-15 19:09: cases with an investigator comment are pinned on top of the queue."""
    out = {}
    for d in conn.execute(
        "SELECT DISTINCT ON (player_id) player_id, note, actor, ts FROM audit_event"
        " WHERE action IN ('escalate','monitor','dismiss','handling','resolve') AND player_id IS NOT NULL"
        " AND note IS NOT NULL AND btrim(note) <> ''"
        " ORDER BY player_id, ts DESC, id DESC").fetchall():
        out[d["player_id"]] = {"note": d["note"], "actor": d["actor"], "ts": d["ts"]}
    return out


def case_timeline(conn) -> dict:
    """Every case step per player, oldest first -> {player_id: [{action, actor, ts, note}]}. Read-only.
    Feeds the Report page (owner 2026-10-15 19:28, D-2026-10-15-29)."""
    out: dict = {}
    for d in conn.execute(
        "SELECT player_id, action, actor, ts, note FROM audit_event"
        " WHERE action IN ('escalate','monitor','dismiss','handling','resolve') AND player_id IS NOT NULL"
        " ORDER BY player_id, ts, id").fetchall():
        out.setdefault(d["player_id"], []).append(dict(d))
    return out
