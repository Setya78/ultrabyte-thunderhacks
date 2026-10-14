"""Deterministic SYNTHETIC seed for UltraByte.

~200 background players with 120 days of history, plus 10 planted scenarios.
Ground-truth labels go to `planted_case`, which the scorer never reads.

Run:  DATABASE_URL=... python -m db.seed.generate
"""
from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

SEED = 20261014
N_BACKGROUND = 190
HISTORY_DAYS = 120
# Fixed "now" so every reset produces identical data (12:00 EDT, 14 Oct 2026).
ANCHOR = datetime(2026, 10, 14, 16, 0, tzinfo=timezone.utc)

REGIONS = ["Toronto", "Ottawa", "Sault Ste. Marie", "Sudbury", "London", "Windsor", "Thunder Bay"]
AGE_BANDS = ["19-24", "25-34", "35-49", "50-64", "65+"]
INCOME_BANDS = ["<30k", "30-60k", "60-100k", "100-200k", ">200k"]
# Typical monthly deposit level per income band (synthetic assumption, CAD).
INCOME_SPEND = {"<30k": 120, "30-60k": 220, "60-100k": 400, "100-200k": 800, ">200k": 1800}
OCCUPATIONS = {
    "<30k": ["student", "retail associate", "server", "part-time tutor"],
    "30-60k": ["warehouse lead", "admin assistant", "bus driver", "technician"],
    "60-100k": ["nurse", "teacher", "electrician", "analyst"],
    "100-200k": ["engineer", "pharmacist", "manager", "consultant"],
    ">200k": ["business owner", "physician", "executive", "lawyer"],
}
FIRST = ["Avery", "Jordan", "Riley", "Morgan", "Casey", "Quinn", "Rowan", "Sage", "Parker", "Reese",
         "Emerson", "Hayden", "Jamie", "Kai", "Logan", "Micah", "Noel", "Remy", "Skyler", "Tatum"]
LAST_INITIAL = "ABCDEFGHJKLMNPRSTVWZ"
METHODS = ["debit", "credit", "e_transfer", "wallet"]


@dataclass
class Player:
    id: str
    display_name: str
    occupation: str
    income_band: str
    age_band: str
    region: str
    created_at: datetime
    device: str
    fingerprint: str
    method: str
    txns: list = field(default_factory=list)
    sessions: list = field(default_factory=list)

    @property
    def peer_segment(self) -> str:
        return f"{self.age_band}|{self.income_band}|{self.region}"


def _fp(rng: random.Random, prefix: str) -> str:
    return prefix + hashlib.sha256(str(rng.random()).encode()).hexdigest()[:12]


def _new_player(rng: random.Random, pid: str, *, income=None, age=None, region=None,
                occupation=None, created_days_ago=None) -> Player:
    income = income or rng.choices(INCOME_BANDS, weights=[2, 4, 4, 2, 1])[0]
    return Player(
        id=pid,
        display_name=f"{rng.choice(FIRST)} {rng.choice(LAST_INITIAL)}.",
        occupation=occupation or rng.choice(OCCUPATIONS[income]),
        income_band=income,
        age_band=age or rng.choice(AGE_BANDS),
        region=region or rng.choices(REGIONS, weights=[5, 3, 1, 1, 2, 1, 1])[0],
        created_at=ANCHOR - timedelta(days=created_days_ago or rng.randint(HISTORY_DAYS + 5, 900)),
        device=_fp(rng, "dev-"),
        fingerprint=_fp(rng, "fp-"),
        method=rng.choice(METHODS),
    )


def _ts(day_ago: float, hour: float) -> datetime:
    base = (ANCHOR - timedelta(days=day_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(hours=hour)


def _add_txn(p: Player, ts, ttype, amount, *, method=None, region=None, device=None, fp=None):
    p.txns.append((p.id, ts, ttype, round(float(amount), 2), method or p.method,
                   fp or p.fingerprint, region or p.region, device or p.device))


def _play_session(rng: random.Random, p: Player, start: datetime, hours: float, stake: float,
                  rtp: float = 0.93, region=None, device=None):
    """One session: a few wagers, maybe a win. Net result recorded on the session."""
    end = start + timedelta(hours=hours)
    n = max(1, int(hours * 3))
    wagered = won = 0.0
    for i in range(n):
        w = max(1.0, rng.gauss(stake / n, stake / n * 0.3))
        t = start + timedelta(hours=hours * i / n)
        _add_txn(p, t, "wager", w, region=region, device=device)
        wagered += w
    if rng.random() < 0.45:
        won = wagered * rng.uniform(0.5, 2.2) * rtp
        _add_txn(p, end, "win", won, region=region, device=device)
    p.sessions.append((p.id, start, end, round(won - wagered, 2)))
    return won - wagered


def _background_history(rng: random.Random, p: Player, days=HISTORY_DAYS, scale=1.0, start_day=None):
    """Normal behaviour: deposits ~weekly at the income-band level, evening sessions."""
    monthly = INCOME_SPEND[p.income_band] * scale * rng.uniform(0.6, 1.4)
    first = min(days, start_day if start_day is not None else days)
    d = first
    while d > 0:
        gap = rng.uniform(4, 10)
        d -= gap
        if d <= 0:
            break
        dep = max(10.0, rng.gauss(monthly / 4, monthly / 12))
        _add_txn(p, _ts(d, rng.uniform(17, 22)), "deposit", dep)
        _play_session(rng, p, _ts(d, rng.uniform(18, 22)), rng.uniform(0.5, 2.0), dep * rng.uniform(0.6, 1.0))
        if rng.random() < 0.15:
            _add_txn(p, _ts(d - 1, rng.uniform(9, 17)), "withdrawal", dep * rng.uniform(0.3, 0.9))


def build(rng: random.Random | None = None):
    rng = rng or random.Random(SEED)
    players: list[Player] = []
    planted: list[tuple] = []
    ids = [f"P{n:04d}" for n in range(1, N_BACKGROUND + 12)]  # 190 background + 11 planted
    rng.shuffle(ids)  # planted players get scattered ids, not a giveaway range
    pid = iter(ids)

    # ---- background population ----
    for _ in range(N_BACKGROUND):
        p = _new_player(rng, next(pid))
        _background_history(rng, p)
        players.append(p)

    def case(no, label, p, expected, category, source):
        planted.append((no, p.id, label, expected, category, source))
        players.append(p)

    # 1. "$10k x2": A routinely deposits ~$10k (not a risk); B normally ~$200/month then $10k.
    a = _new_player(rng, next(pid), income=">200k", occupation="business owner", age="50-64", region="Toronto")
    d = HISTORY_DAYS
    while d > 3:
        d -= rng.uniform(12, 16)
        if d <= 0:
            break
        amt = rng.uniform(9800, 10400)
        _add_txn(a, _ts(d, 19), "deposit", amt)
        _play_session(rng, a, _ts(d, 19.5), 2.5, amt * 0.8)
        _add_txn(a, _ts(d - 1, 11), "withdrawal", amt * rng.uniform(0.4, 0.8))
    case(1, "$10k x2 - A: routine $10k depositor (control)", a, "no_flag", None, "OLG brief: context vs threshold")
    b = _new_player(rng, next(pid), income="30-60k", occupation="admin assistant", age="25-34", region="London")
    _background_history(rng, b, scale=0.9)
    _add_txn(b, _ts(4, 20), "deposit", 10000.00)
    _play_session(rng, b, _ts(4, 20.5), 1.5, 2500)
    case(1, "$10k x2 - B: ~$200/month player deposits $10k", b, "flag", "fraud_aml", "OLG brief 3d; FINTRAC LCTR $10k")

    # 2. Structuring: $9,500 x3 within 7 days, cash at the cage.
    p = _new_player(rng, next(pid), income="60-100k")
    _background_history(rng, p)
    for day in (9, 6, 3):
        _add_txn(p, _ts(day, rng.uniform(13, 18)), "deposit", 9500.00, method="cash_cage")
        _play_session(rng, p, _ts(day, 19), 1.0, 900)
    case(2, "Structuring: $9,500 x3 in 7 days (cash)", p, "flag", "fraud_aml", "FINTRAC-OG #16")

    # 3. Cash-through: large deposit, minimal play, large withdrawal.
    p = _new_player(rng, next(pid), income="100-200k")
    _background_history(rng, p)
    _add_txn(p, _ts(5, 14), "deposit", 15000.00, method="e_transfer")
    _play_session(rng, p, _ts(5, 15), 0.4, 600)
    _add_txn(p, _ts(4, 10), "withdrawal", 14200.00, method="e_transfer")
    case(3, "Cash-through: deposit $15k, wager $600, withdraw $14.2k", p, "flag", "fraud_aml", "FINTRAC-OG #5")

    # 4. Spend inconsistent with income band (student, high spend).
    p = _new_player(rng, next(pid), income="<30k", occupation="student", age="19-24", region="Sault Ste. Marie")
    _background_history(rng, p, days=HISTORY_DAYS, start_day=HISTORY_DAYS)
    for day in range(28, 0, -4):
        amt = rng.uniform(2500, 3500)
        _add_txn(p, _ts(day, 21), "deposit", amt)
        _play_session(rng, p, _ts(day, 21.5), 2.0, amt * 0.9)
    case(4, "Spend vs income: student depositing ~$3k every 4 days", p, "flag", "fraud_aml", "FINTRAC-OG #1; OLG brief 3a")

    # 5. Spike vs peer segment: new account, so peers are the only reference.
    p = _new_player(rng, next(pid), income="30-60k", age="35-49", region="Toronto", created_days_ago=16)
    for day in range(14, 0, -2):
        amt = rng.uniform(800, 1100)
        _add_txn(p, _ts(day, 20), "deposit", amt)
        _play_session(rng, p, _ts(day, 20.5), 1.5, amt)
    case(5, "Peer spike: new account, ~10x peer-segment deposits", p, "flag", "fraud_aml", "FINTRAC-OG #13; OLG brief 3b")

    # 6. Unexpected location + new device.
    p = _new_player(rng, next(pid), region="Sudbury")
    _background_history(rng, p)
    new_dev = _fp(rng, "dev-")
    for day in (6, 4, 2):
        amt = rng.uniform(1500, 2500)
        _add_txn(p, _ts(day, 2), "deposit", amt, region="Windsor", device=new_dev)
        _play_session(rng, p, _ts(day, 2.3), 1.0, amt, region="Windsor", device=new_dev)
    case(6, "Geo anomaly: Sudbury player, 3 deposits from Windsor on a new device", p, "flag", "fraud_aml", "FINTRAC-OG #7; OLG brief 3c")

    # 7. Gradual behaviour change over 60 days.
    p = _new_player(rng, next(pid), income="60-100k")
    _background_history(rng, p, days=HISTORY_DAYS, start_day=HISTORY_DAYS)
    p.txns = [t for t in p.txns if t[1] < ANCHOR - timedelta(days=60)]
    p.sessions = [s for s in p.sessions if s[1] < ANCHOR - timedelta(days=60)]
    for i, day in enumerate(range(60, 0, -5)):
        amt = 100 + i * 200
        _add_txn(p, _ts(day, 20), "deposit", amt)
        _play_session(rng, p, _ts(day, 20.5), 1.5, amt * 0.9)
    case(7, "Gradual drift: weekly deposits ramp $100 -> $2,300 over 60 days", p, "flag", "fraud_aml", "FINTRAC-OG #14; OLG brief 3d")

    # 8. Harm: long late-night sessions and chasing losses.
    p = _new_player(rng, next(pid), income="30-60k")
    _background_history(rng, p)
    stake = 200
    for day in (10, 8, 6, 4, 2):
        _add_txn(p, _ts(day, 0.5), "deposit", stake)
        net = _play_session(rng, p, _ts(day, 0.7), rng.uniform(5, 7), stake * 1.3, rtp=0.6)
        if net < 0:
            stake *= 1.6
    case(8, "Harm: 5-7h sessions after midnight, deposits rising after losses", p, "flag", "harm", "OLG brief (safer play); AML workshop")

    # 9. Harm: repeated withdrawal reversals.
    p = _new_player(rng, next(pid), income="60-100k")
    _background_history(rng, p)
    for day in (12, 9, 7, 4, 2):
        amt = rng.uniform(400, 900)
        _add_txn(p, _ts(day, 11), "withdrawal", amt)
        _add_txn(p, _ts(day, 13), "withdrawal_reversal", amt)
        _play_session(rng, p, _ts(day, 14), 2.5, amt)
    case(9, "Harm: 5 withdrawals reversed back into play in 12 days", p, "flag", "harm", "OLG brief (safer play)")

    # 10. Combination: three weak signals, each below its own threshold.
    p = _new_player(rng, next(pid), income="30-60k", age="25-34")
    _background_history(rng, p)
    for day in (12, 8, 4):
        amt = INCOME_SPEND["30-60k"] * 0.9  # moderate rise; M1 thresholds are tuned so this alone stays below
        _add_txn(p, _ts(day, 23.2), "deposit", amt)  # late but not deep night
        _play_session(rng, p, _ts(day, 23.4), 2.8, amt * 1.1)
    case(10, "Combination: mild deviation + late play + mild income stretch", p, "flag", "fraud_aml", "OLG brief: combine weak signals")

    return players, planted


def load(conn) -> dict:
    """TRUNCATE and reload everything. Used by first load and by /reset."""
    players, planted = build()
    with conn.cursor() as cur:
        cur.execute("TRUNCATE audit_event, planted_case, txn, session, player RESTART IDENTITY")
        with cur.copy("COPY player (id, display_name, occupation, income_band, age_band, region, peer_segment, created_at) FROM STDIN") as cp:
            for p in players:
                cp.write_row((p.id, p.display_name, p.occupation, p.income_band, p.age_band, p.region, p.peer_segment, p.created_at))
        with cur.copy("COPY txn (player_id, ts, type, amount, method, method_fingerprint, location_region, device_id) FROM STDIN") as cp:
            for p in players:
                for t in p.txns:
                    cp.write_row(t)
        with cur.copy("COPY session (player_id, start_ts, end_ts, net_result) FROM STDIN") as cp:
            for p in players:
                for s in p.sessions:
                    cp.write_row(s)
        with cur.copy("COPY planted_case (case_no, player_id, label, expected, expected_category, source_ref) FROM STDIN") as cp:
            for row in planted:
                cp.write_row(row)
    conn.commit()
    return {
        "players": len(players),
        "txns": sum(len(p.txns) for p in players),
        "sessions": sum(len(p.sessions) for p in players),
        "planted_rows": len(planted),
    }


if __name__ == "__main__":
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as c:
        print(load(c))
