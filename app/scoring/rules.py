"""Operator-owned thresholds (D-2026-10-15-19).

Defaults below are version 1 (the team spec, IN-07). Operators change them on /rules; every change is a
new append-only `rule_version` row, the scorer reads the latest, and each score snapshot records which
version produced it. The scorer never hard-codes a threshold.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

# (key, default, label, group, help)
SPEC = [
    # AML / context score
    ("income_fit_floor", 0.25, "Income fit: starts scoring at", "Context score", "30-day deposits as a share of estimated monthly income. Below this: 0 points."),
    ("income_fit_span", 0.75, "Income fit: full 25 points after a further", "Context score", "Points rise linearly over this span above the floor."),
    ("history_floor", 2.0, "Own history: starts scoring at (x usual)", "Context score", "30-day deposits divided by the previous 5-month average."),
    ("history_span", 8.0, "Own history: full 25 points after a further (x)", "Context score", ""),
    ("history_min_base", 50.0, "Own history: minimum monthly base ($)", "Context score", "Avoids dividing by a near-zero history."),
    ("peer_p95", 0.95, "Peers: 15 points above percentile", "Context score", "Share of comparable players (same age and income band) below this player."),
    ("peer_p99", 0.99, "Peers: 25 points above percentile", "Context score", ""),
    ("peer_min_group", 20, "Peers: minimum comparable players", "Context score", "Below this the peer check is not scored."),
    ("location_cities", 3, "Location: cities within the window", "Context score", ""),
    ("location_hours", 24, "Location: window (hours)", "Context score", ""),
    ("band_medium", 25, "Band Medium from score", "Context score", ""),
    ("band_high", 50, "Band High from score", "Context score", ""),
    # Labels
    ("structuring_low", 9000, "Structuring: deposit at or above ($)", "STR labels", "FINTRAC: multiple deposits just under the $10,000 reporting threshold."),
    ("structuring_high", 9999.99, "Structuring: deposit at or below ($)", "STR labels", ""),
    ("structuring_min", 2, "Structuring: minimum such deposits in 30 days", "STR labels", ""),
    ("minimal_play_ratio", 0.10, "Minimal play: wagered below this share of deposits", "STR labels", "Deposit, little play, withdraw."),
    ("v1_threshold", 10000, "Version 1.0: single deposit at or above ($)", "STR labels", "The old rule, used by the Version 1.0 console (/v1) and the Validation page."),
    # Safer Gambling score
    ("sg_escalation_min_rise", 0.10, "Escalation: a month counts as a rise at (+ share)", "Safer Gambling", "0.10 = at least 10% more than the month before. Smaller changes are normal variation (review 2026-10-15)."),
    ("sg_escalating_months", 4, "Escalation: 25 points at months rising in a row", "Safer Gambling", "Deposits higher than the month before, N months running. One month fewer: 15 points."),
    ("sg_night_share", 0.60, "Night play: 25 points at share of sessions 00:00-04:00", "Safer Gambling", "Two thirds of this share: 15 points."),
    ("sg_night_min_sessions", 3, "Night play: minimum sessions to score", "Safer Gambling", ""),
    ("sg_chase_minutes", 60, "Loss chasing: deposit within (minutes) after a losing session", "Safer Gambling", ""),
    ("sg_chase_count", 3, "Loss chasing: 25 points at this many in 30 days", "Safer Gambling", "One fewer: 15 points; one: 5 points."),
    ("sg_days_played", 20, "Intensity: 25 points at days played in 30", "Safer Gambling", "Fourteen or more: 15 points."),
    ("sg_band_medium", 30, "Safer Gambling band Medium from score", "Safer Gambling", "Default 30: one marker alone (max 25) does not raise an alert; two do."),
    ("sg_band_high", 50, "Safer Gambling band High from score", "Safer Gambling", ""),
]
DEFAULTS = {k: v for k, v, *_ in SPEC}


@dataclass
class Rules:
    version: int
    values: dict

    def __getattr__(self, k):
        try:
            return self.values[k]
        except KeyError:
            raise AttributeError(k)


def validate(form: dict) -> tuple[dict, list[str]]:
    out, errs = {}, []
    for k, default, label, *_ in SPEC:
        raw = str(form.get(k, "")).strip()
        try:
            v = int(raw) if isinstance(default, int) else float(raw)
        except ValueError:
            errs.append(f"{label}: '{raw}' is not a number")
            continue
        if v < 0:
            errs.append(f"{label}: must be zero or more")
        out[k] = v
    if not errs:
        if out["band_high"] <= out["band_medium"] or out["sg_band_high"] <= out["sg_band_medium"]:
            errs.append("Band High must be above Band Medium")
        if out["structuring_high"] < out["structuring_low"]:
            errs.append("Structuring: upper amount must be at or above the lower amount")
        if not 0 <= out["sg_escalation_min_rise"] <= 1:
            errs.append("Escalation: rise share must be between 0 and 1")
        if not 0 <= out["peer_p95"] <= out["peer_p99"] <= 1:
            errs.append("Peers: percentiles must be between 0 and 1 and p95 at or below p99")
    return out, errs


def current(conn) -> Rules:
    row = conn.execute("SELECT id, rules FROM rule_version ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return Rules(1, dict(DEFAULTS))
    vals = dict(DEFAULTS)
    vals.update(row["rules"])
    return Rules(row["id"], vals)


def history(conn, limit: int = 20) -> list[dict]:
    return conn.execute("SELECT id, created_at, actor, note, rules FROM rule_version ORDER BY id DESC LIMIT %s", (limit,)).fetchall()


def changed_keys(old: dict, new: dict) -> list[tuple[str, object, object]]:
    return [(k, old.get(k), new[k]) for k in new if old.get(k) != new[k]]


def save(conn, values: dict, actor: str, note: str, prev: Rules) -> int:
    from psycopg.types.json import Jsonb

    row = conn.execute("INSERT INTO rule_version (actor, note, rules) VALUES (%s, %s, %s) RETURNING id",
                       (actor, note, Jsonb(values))).fetchone()
    diff = changed_keys(prev.values, values)
    labels = {k: label for k, _, label, *_ in SPEC}
    summary = "; ".join(f"{labels[k]}: {a} -> {b}" for k, a, b in diff) or "no change"
    conn.execute("INSERT INTO audit_event (actor, action, note, score_snapshot) VALUES (%s, 'rule_change', %s, %s)",
                 (actor, f"Rules v{row['id']} ({note}): {summary}"[:1000], Jsonb({"rule_version": row["id"], "changes": [list(d) for d in diff]})))
    conn.commit()
    return row["id"]
