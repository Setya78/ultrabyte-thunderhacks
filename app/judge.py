"""Manual entry (D-2026-10-14-16): type one deposit or withdrawal, see the score change.

Rows are marked entry_source='manual', stay synthetic, and /reset removes them. A new player's display name may be
typed (owner 2026-10-15 17:05; labelled fictional, letters only) or left empty for a generated 'Player M-###'.
Every entry writes an audit event.
"""
from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import datetime, timedelta

from psycopg.types.json import Jsonb

from app.importer import AGE_BANDS, INCOME_BANDS

# Same lists as db/seed/generate.py OCCUPATIONS (keep in sync): a manual player picks from the dataset's own occupations.
OCCUPATIONS = {
    "<20k": ["student", "part-time server", "retail associate", "unemployed"],
    "20-50k": ["cook", "warehouse worker", "admin assistant", "retired"],
    "50-100k": ["nurse", "teacher", "electrician", "analyst"],
    "100-200k": ["engineer", "sales manager", "pharmacist", "consultant"],
    "200k+": ["business owner", "physician", "executive", "lawyer"],
}
from app.scoring import config as C

CITIES = ["Toronto", "Ottawa", "Hamilton", "London", "Kitchener", "Windsor", "Sudbury",
          "Sault Ste. Marie", "Thunder Bay", "Kingston", "Barrie", "Niagara Falls"]
METHODS = {"deposit": ["debit", "credit", "e_transfer", "cash_cage", "prepaid"],
           "withdrawal": ["e_transfer", "cash_cage"]}
ACTOR = "manual entry (demo)"
MAX_AMOUNT = 250_000


@dataclass
class Entry:
    player_id: str          # existing id, or "" for a new player
    ptype: str              # deposit | withdrawal
    amount: float
    when: datetime
    method: str
    city: str
    card_last4: str | None
    wagered: float
    third_party: bool
    new_age: str = ""
    new_income: str = ""
    new_city: str = ""
    new_occupation: str = ""
    new_name: str = ""


def parse(form: dict) -> tuple[Entry | None, list[str]]:
    errs: list[str] = []
    g = lambda k: (form.get(k) or "").strip()
    ptype = g("type")
    if ptype not in METHODS:
        errs.append("Type must be deposit or withdrawal.")
    try:
        amount = round(float(g("amount").replace(",", "").replace("$", "")), 2)
        if not 0 < amount <= MAX_AMOUNT:
            errs.append(f"Amount must be between $1 and ${MAX_AMOUNT:,}.")
    except ValueError:
        amount = 0.0
        errs.append("Amount is not a number.")
    try:
        when = datetime.strptime(f"{g('date')} {g('time') or '12:00'}", "%Y-%m-%d %H:%M").replace(tzinfo=C.EDT)
        if not C.WIN_START <= when < C.WIN_END:
            errs.append("Date must be in the scored window, 2026-09-15 to 2026-10-14.")
    except ValueError:
        when = C.WIN_END - timedelta(hours=12)
        errs.append("Date or time is not valid (YYYY-MM-DD, HH:MM).")
    method = g("method")
    if ptype in METHODS and method not in METHODS[ptype]:
        errs.append(f"Method for a {ptype} must be one of: {', '.join(METHODS[ptype])}.")
    city = g("city")
    if city not in CITIES:
        errs.append("Choose a city from the list (Ontario).")
    last4 = g("card_last4") or None
    if last4 and not (len(last4) == 4 and last4.isdigit()):
        errs.append("Card: last 4 digits only.")
    try:
        wagered = round(float(g("wagered") or 0), 2)
        if wagered < 0 or wagered > MAX_AMOUNT:
            errs.append("Amount played must be between $0 and the limit.")
    except ValueError:
        wagered = 0.0
        errs.append("Amount played is not a number.")
    mode = g("mode") or ("existing" if g("player_id") else "new")
    if mode == "existing" and not g("player_id"):
        errs.append("Existing player: enter the player's ID (e.g. P-5120), or switch to New player.")
    e = Entry(player_id=g("player_id") if mode == "existing" else "", ptype=ptype, amount=amount, when=when, method=method, city=city,
              card_last4=last4 if ptype == "deposit" else None, wagered=wagered if ptype == "deposit" else 0.0,
              third_party=ptype == "withdrawal" and g("third_party") == "yes")
    if not e.player_id:
        e.new_age, e.new_income, e.new_city = g("new_age"), g("new_income"), g("new_city")
        e.new_occupation = g("new_occupation")
        if e.new_income in OCCUPATIONS and e.new_occupation not in OCCUPATIONS[e.new_income]:
            errs.append(f"New player: choose an occupation from the {e.new_income} list.")
        first, last = " ".join(g("new_first").split())[:30], " ".join(g("new_last").split())[:30]
        name_re = r"[A-Za-z][A-Za-z'\-]*( [A-Za-z][A-Za-z'\-]*)*"
        if (first or last) and not (first and last):
            errs.append("New player: enter both a first name and a last name, or leave both empty.")
        elif first and not (re.fullmatch(name_re, first) and re.fullmatch(name_re, last)):
            errs.append("New player: names may only use letters, hyphens and apostrophes (use a fictional name).")
        # Stored as "First L." like every other player in the dataset (data minimisation, P7).
        e.new_name = f"{first} {last[0].upper()}." if first and last else ""
        if e.new_age not in AGE_BANDS:
            errs.append("New player: choose an age band.")
        if e.new_income not in INCOME_BANDS:
            errs.append("New player: choose an income band.")
        if e.new_city not in CITIES:
            errs.append("New player: choose a home city.")
    return (None if errs else e), errs


def save(conn, e: Entry) -> str:
    """Insert the entry (and a new player if asked). Returns the player id."""
    with conn.cursor() as cur:
        if e.player_id:
            if not cur.execute("SELECT 1 FROM player WHERE id = %s", (e.player_id,)).fetchone():
                raise ValueError(f"No player with ID {e.player_id}. Check the Review queue, or switch to New player (the ID is assigned automatically).")
            pid = e.player_id
        else:
            row = cur.execute("SELECT count(*) AS n FROM player WHERE id LIKE %s", ("M-%",)).fetchone()
            n = (row["n"] if isinstance(row, dict) else row[0]) + 1
            pid = f"M-{n:03d}"
            cur.execute(
                "INSERT INTO player (id, display_name, occupation, income_band, age_band, region, peer_segment,"
                " created_at, entry_source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'manual')",
                (pid, e.new_name or f"Player M-{n:03d}", e.new_occupation, e.new_income, e.new_age, e.new_city,
                 f"{e.new_age}|{e.new_income}", C.HIST_START - timedelta(days=60)))
        card = f"manual-card-{e.card_last4}" if e.card_last4 else None
        acct = (f"manual-acct-other-{pid}" if e.third_party else f"manual-acct-{pid}") if e.ptype == "withdrawal" else None
        cur.execute(
            "INSERT INTO txn (player_id, ts, type, amount, method, method_fingerprint, method_last4, location_region,"
            " device_id, payout_account, payout_holder_match, entry_source)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'manual-device', %s, %s, 'manual')",
            (pid, e.when, e.ptype, e.amount, e.method, card, e.card_last4, e.city, acct,
             (not e.third_party) if e.ptype == "withdrawal" else None))
        if e.wagered:
            cur.execute(
                "INSERT INTO txn (player_id, ts, type, amount, method, location_region, device_id, entry_source)"
                " VALUES (%s, %s, 'wager', %s, 'wallet', %s, 'manual-device', 'manual')",
                (pid, e.when + timedelta(minutes=10), e.wagered, e.city))
        # A short play session at the same place and time, so the location check sees where it happened.
        cur.execute(
            "INSERT INTO session (player_id, start_ts, end_ts, net_result, location_region, device_id, entry_source)"
            " VALUES (%s, %s, %s, %s, %s, 'manual-device', 'manual')",
            (pid, e.when, e.when + timedelta(minutes=30), -e.wagered, e.city))
    conn.commit()
    return pid


def record(conn, pid: str, e: Entry, before: dict | None, after: dict, actor: str = ACTOR) -> None:
    what = f"{e.ptype} ${e.amount:,.2f} in {e.city} on {e.when:%Y-%m-%d %H:%M}"
    if e.wagered:
        what += f", played ${e.wagered:,.2f}"
    if e.third_party:
        what += ", payout to another person's account"
    if e.card_last4:
        what += f", card ending {e.card_last4}"
    score = f"score {before['score'] if before else 'new'} -> {after['score']}"
    conn.execute(
        "INSERT INTO audit_event (actor, player_id, action, note, score_snapshot) VALUES (%s, %s, 'manual_entry', %s, %s)",
        (actor, pid, f"Manual entry: {what} ({score})", Jsonb(after)))
    conn.commit()


def diff(before: dict | None, after: dict) -> dict:
    """Per-check before/after and which labels appeared or went away."""
    b_checks = {c["key"]: c for c in (before or {}).get("checks", [])}
    rows = []
    for c in after["checks"]:
        old = b_checks.get(c["key"])
        rows.append({"name": c["name"], "key": c["key"], "before": old["points"] if old else None, "after": c["points"],
                     "reason": c["reason"], "changed": (old is None) or old["points"] != c["points"] or old["reason"] != c["reason"]})
    lab = lambda d: {(l["text"], l["reason"]) for l in (d or {}).get("labels", [])}
    return {"checks": rows, "new_labels": sorted(lab(after) - lab(before)), "gone_labels": sorted(lab(before) - lab(after)),
            "score_before": before["score"] if before else None, "band_before": before["band"] if before else None}
