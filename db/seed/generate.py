"""Deterministic SYNTHETIC seed for UltraByte (team spec, K0 v0.7).

- 490 background players, Ontario only, 15 Apr - 14 Oct 2026
  (history = 15 Apr - 14 Sep, current window = 15 Sep - 14 Oct).
- 10 planted cases A-J (11 players; case F involves two players).
- Ground-truth labels go to `planted_case`, which the scorer never reads.

Only bands are stored (age band, income band, home city). The generator draws a hidden
"actual income" inside each band to drive spending, so peer groups have a realistic spread;
that hidden value is never written to the database.

Run:  DATABASE_URL=... python -m db.seed.generate
"""
from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

SEED = 20261014
N_BACKGROUND = 490
# Windows come from the scorer config so the data and the checks can never drift apart.
from app.scoring.config import EDT, HIST_START, MONTH_STARTS, WIN_END, WIN_START  # noqa: E402,F401

CITIES = ["Toronto", "Ottawa", "Hamilton", "London", "Kitchener", "Windsor", "Sudbury",
          "Sault Ste. Marie", "Thunder Bay", "Kingston", "Barrie", "Niagara Falls"]
CITY_W = [30, 14, 8, 7, 7, 5, 4, 4, 3, 4, 4, 3]
AGE_BANDS = ["19-29", "30-44", "45-64", "65+"]
INCOME_BANDS = ["<20k", "20-50k", "50-100k", "100-200k", "200k+"]
# Hidden actual-income range per band (annual CAD) - generator only, never stored.
INCOME_RANGE = {"<20k": (8_000, 20_000), "20-50k": (20_000, 50_000), "50-100k": (50_000, 100_000),
                "100-200k": (100_000, 200_000), "200k+": (200_000, 600_000)}
OCCUPATIONS = {
    "<20k": ["student", "part-time server", "retail associate", "unemployed"],
    "20-50k": ["cook", "warehouse worker", "admin assistant", "retired"],
    "50-100k": ["nurse", "teacher", "electrician", "analyst"],
    "100-200k": ["engineer", "sales manager", "pharmacist", "consultant"],
    "200k+": ["business owner", "physician", "executive", "lawyer"],
}
FIRST = ["Avery", "Jordan", "Riley", "Morgan", "Casey", "Quinn", "Rowan", "Sage", "Parker", "Reese",
         "Emerson", "Hayden", "Jamie", "Kai", "Logan", "Micah", "Noel", "Remy", "Skyler", "Tatum"]
LAST_INITIAL = "ABCDEFGHJKLMNPRSTVWZ"
METHODS = ["debit", "credit", "e_transfer", "wallet"]


def _fp(rng: random.Random, prefix: str) -> str:
    return prefix + hashlib.sha256(str(rng.random()).encode()).hexdigest()[:12]


@dataclass
class Player:
    id: str
    display_name: str
    occupation: str
    income_band: str
    age_band: str
    region: str
    created_at: datetime
    method: str
    card: str
    last4: str
    account: str
    device: str
    txns: list = field(default_factory=list)
    sessions: list = field(default_factory=list)

    @property
    def peer_segment(self) -> str:
        return f"{self.age_band}|{self.income_band}"

    # ---- event helpers -------------------------------------------------
    def deposit(self, ts, amount, *, card=None, last4=None, city=None, device=None, method=None):
        self.txns.append(dict(player_id=self.id, ts=ts, type="deposit", amount=round(amount, 2),
                              method=method or self.method, method_fingerprint=card or self.card,
                              method_last4=last4 or self.last4, location_region=city or self.region,
                              device_id=device or self.device, payout_account=None, payout_holder_match=None))

    def withdraw(self, ts, amount, *, account=None, holder_match=True, city=None, device=None):
        self.txns.append(dict(player_id=self.id, ts=ts, type="withdrawal", amount=round(amount, 2),
                              method="e_transfer", method_fingerprint=None, method_last4=None,
                              location_region=city or self.region, device_id=device or self.device,
                              payout_account=account or self.account, payout_holder_match=holder_match))

    def session(self, rng, start, hours, wagered, *, payback=None, city=None, device=None):
        """One session: a few wagers and possibly a win. Returns net result."""
        city, device = city or self.region, device or self.device
        end = start + timedelta(hours=hours)
        n = rng.randint(2, 4)
        for i in range(n):
            self.txns.append(dict(player_id=self.id, ts=start + timedelta(hours=hours * i / n), type="wager",
                                  amount=round(max(1.0, wagered / n), 2), method="wallet", method_fingerprint=None,
                                  method_last4=None, location_region=city, device_id=device,
                                  payout_account=None, payout_holder_match=None))
        payback = rng.uniform(0.75, 1.02) if payback is None else payback
        won = wagered * payback
        if won >= 1:
            self.txns.append(dict(player_id=self.id, ts=end, type="win", amount=round(won, 2), method="wallet",
                                  method_fingerprint=None, method_last4=None, location_region=city,
                                  device_id=device, payout_account=None, payout_holder_match=None))
        self.sessions.append(dict(player_id=self.id, start_ts=start, end_ts=end,
                                  net_result=round(won - wagered, 2), location_region=city, device_id=device))
        return won - wagered


def _new_player(rng, pid, *, income=None, age=None, occupation=None, city=None):
    income = income or rng.choices(INCOME_BANDS, weights=[15, 30, 30, 17, 8])[0]
    return Player(
        id=pid,
        display_name=f"{rng.choice(FIRST)} {rng.choice(LAST_INITIAL)}.",
        occupation=occupation or rng.choice(OCCUPATIONS[income]),
        income_band=income,
        age_band=age or rng.choices(AGE_BANDS, weights=[25, 30, 30, 15])[0],
        region=city or rng.choices(CITIES, weights=CITY_W)[0],
        created_at=HIST_START - timedelta(days=rng.randint(30, 900)),
        method=rng.choice(METHODS),
        card=_fp(rng, "card-"),
        last4=f"{rng.randint(0, 9999):04d}",
        account=_fp(rng, "acct-"),
        device=_fp(rng, "dev-"),
    )


def _at(day: datetime, hour: float) -> datetime:
    return day.replace(hour=0, minute=0) + timedelta(hours=hour)


def _month_days(k: int) -> tuple[datetime, int]:
    start = MONTH_STARTS[k]
    return start, (MONTH_STARTS[k + 1] - start).days


def _normal_month(rng, p: Player, k: int, total: float, *, evening=True, n=None):
    """Spread a monthly deposit total over 2-6 deposits, each followed by an evening session."""
    start, ndays = _month_days(k)
    n = n or rng.randint(2, 6)
    weights = [rng.uniform(0.7, 1.3) for _ in range(n)]
    for w in weights:
        amt = max(10.0, total * w / sum(weights))
        day = start + timedelta(days=rng.randrange(ndays))
        hour = rng.uniform(18, 23) if evening else rng.uniform(0, 4)
        city = p.region if rng.random() < 0.95 else rng.choice(CITIES)
        p.deposit(_at(day, hour), amt, city=city)
        p.session(rng, _at(day, hour + 0.1), rng.uniform(0.5, 3.0), amt * rng.uniform(1.0, 3.0), city=city)
        if rng.random() < 0.2:
            p.withdraw(_at(day + timedelta(days=1), rng.uniform(9, 17)), amt * rng.uniform(0.3, 0.8))


def _background(rng, p: Player):
    lo, hi = INCOME_RANGE[p.income_band]
    actual_monthly = rng.uniform(lo, hi) / 12
    high_roller = p.income_band in ("100-200k", "200k+") and rng.random() < 0.3
    rate = rng.uniform(0.15, 0.35) if high_roller else rng.uniform(0.01, 0.05)
    for k in range(6):
        _normal_month(rng, p, k, actual_monthly * rate * rng.uniform(0.7, 1.3))


def _plausible_occupations(players: list, keep: set) -> None:
    """No "retired, 30-44" or "student, 45-64" (review 2026-10-15 #10). Background players only; the replacement is
    the first other occupation in the same income band, so no random draw and no score changes (scores use the
    income band, not the occupation)."""
    odd = {"retired": ("19-29", "30-44"), "student": ("45-64", "65+")}
    for p in players:
        if p.id not in keep and p.age_band in odd.get(p.occupation, ()):
            p.occupation = next(o for o in OCCUPATIONS[p.income_band] if o not in odd)


def _unique_names(players: list, keep_first: set) -> None:
    """One display name per player (team feedback 2026-10-15: two "Logan V." with different IDs looked like one person).

    Planted-case players keep their names (pitch and personas use them). A later duplicate takes the next unused
    "First L." in a fixed order, then "First L.M." once those run out. No random draws, so scores and validation
    are unchanged; names are synthetic and display-only (the player ID is the identifier).
    """
    combos = [f"{f} {l}." for f in FIRST for l in LAST_INITIAL]
    combos += [f"{f} {a}.{b}." for f in FIRST for a in LAST_INITIAL for b in LAST_INITIAL]
    used = set()
    planted_first = {p.display_name.split()[0] for p in players if p.id in keep_first}
    for p in sorted(players, key=lambda p: (p.id not in keep_first, p.id)):
        if p.display_name in used:
            # a renamed planted player also avoids first names other planted cases use, so cases stay easy to tell apart
            avoid = planted_first if p.id in keep_first else set()
            p.display_name = next(n for n in combos if n not in used and n.split()[0] not in avoid)
        used.add(p.display_name)


def build(rng: random.Random | None = None):
    rng = rng or random.Random(SEED)
    planted_ids = {"P-1042", "P-2217", "P-3378", "P-4501", "P-5120", "P-6011", "P-6012",
                   "P-7730", "P-8104", "P-9021", "P-9988"}
    pool = [f"P-{n:04d}" for n in range(1000, 10000) if f"P-{n:04d}" not in planted_ids]
    bg_ids = rng.sample(pool, N_BACKGROUND)

    players: list[Player] = []
    for pid in bg_ids:
        p = _new_player(rng, pid)
        _background(rng, p)
        players.append(p)

    planted: list[tuple] = []
    SSM = "Sault Ste. Marie"

    def add(case, p, label, expected, category, source):
        planted.append((case, p.id, label, expected, category, source))
        if p not in players:
            players.append(p)

    def flat_history(p, monthly, n):
        for k in range(5):
            _normal_month(rng, p, k, monthly, n=n)

    # A - Student: $1,500/month steady, same in the last 30 days. Only profile + peers catch it.
    a = _new_player(rng, "P-1042", income="<20k", age="19-29", occupation="student", city=SSM)
    for k in range(6):
        _normal_month(rng, a, k, 1500, n=3)
    add("A", a, "Student depositing $1,500/month, steady for 6 months", "flag", "fraud_aml", "OLG brief: income fit + peers")

    # B - Retiree: $200/month, then $8,000 in 15 days.
    b = _new_player(rng, "P-2217", income="20-50k", age="65+", occupation="retired", city=SSM)
    flat_history(b, 200, 4)
    for i in range(8):
        day = datetime(2026, 9, 25, tzinfo=EDT) + timedelta(days=2 * i)
        b.deposit(_at(day, 19), 1000)
        b.session(rng, _at(day, 19.2), 2.0, 1100)
    add("B", b, "Retiree: ~$200/month then $8,000 in 15 days", "flag", "fraud_aml", "OLG brief: own history")

    # C - Night nurse: deposits rising five months in a row, mostly midnight-4am, losing every month.
    c = _new_player(rng, "P-3378", income="50-100k", age="30-44", occupation="nurse", city=SSM)
    for k, total in enumerate([600, 900, 1200, 1600, 2000, 2400]):
        start, ndays = _month_days(k)
        n = 12 if k == 5 else max(3, round(total / 200))
        amts = [rng.uniform(150, 250) for _ in range(n)]
        amts = [x * total / sum(amts) for x in amts]
        for j, amt in enumerate(amts):
            day = start + timedelta(days=rng.randrange(ndays))
            night = (k == 5 and j < 9) or (k < 5 and rng.random() < 0.6)  # 9/12 = 75% night in window
            hour = rng.uniform(0.2, 3.5) if night else rng.uniform(19, 22)
            c.deposit(_at(day, hour), amt)
            c.session(rng, _at(day, hour + 0.1), rng.uniform(2, 4), amt * 1.4, payback=rng.uniform(0.2, 0.5))
    add("C", c, "Night nurse: deposits rising 5 months, 75% of sessions 00:00-04:00, losses every month",
        "flag", "harm", "OLG brief: player protection")

    # D - Account takeover: three distant Ontario cities in under 5 hours, new card, new bank account.
    d = _new_player(rng, "P-4501", income="50-100k", age="30-44", occupation="electrician", city=SSM)
    flat_history(d, 500, 2)
    day = datetime(2026, 10, 8, tzinfo=EDT)
    new_dev = _fp(rng, "dev-")
    d.session(rng, _at(day, 9 + 10 / 60), 0.3, 40, city=SSM)
    d.session(rng, _at(day, 11.5), 0.3, 30, city="Toronto", device=new_dev)
    d.session(rng, _at(day, 13.75), 0.2, 20, city="Thunder Bay", device=new_dev)
    d.deposit(_at(day, 13.8), 500, card=_fp(rng, "card-"), last4="8820", city="Thunder Bay", device=new_dev)
    d.withdraw(_at(day, 14.2), 480, account=_fp(rng, "acct-"), city="Thunder Bay", device=new_dev)
    add("D", d, "Sessions from Sault Ste. Marie, Toronto, Thunder Bay within 5h; new card, new bank account",
        "flag", "fraud_aml", "FINTRAC online gambling indicators: unexpected locations")

    # E - Business owner, high roller: one $10,500 deposit is normal for this player. Control.
    e = _new_player(rng, "P-5120", income="200k+", age="45-64", occupation="business owner", city=SSM)
    for k in range(5):
        _normal_month(rng, e, k, rng.uniform(6000, 6500), n=3)
    day = datetime(2026, 10, 3, tzinfo=EDT)
    e.deposit(_at(day, 19), 10500)
    e.session(rng, _at(day, 19.2), 3.0, 18000)
    add("E", e, "Business owner: single $10,500 deposit, consistent with income, history, peers", "no_flag", None,
        "OLG workshop: same transaction, different meaning")

    # F - Two players sharing one card (ending 4417) and one payout bank account.
    f = _new_player(rng, "P-6012", income="<20k", age="30-44", occupation="unemployed", city=SSM)
    f2 = _new_player(rng, "P-6011", income="20-50k", age="19-29", occupation="cook", city=SSM)
    shared_card, shared_acct = _fp(rng, "card-"), _fp(rng, "acct-")
    f.card = f2.card = shared_card
    f.last4 = f2.last4 = "4417"
    f.account = f2.account = shared_acct
    for k in range(6):
        _normal_month(rng, f, k, 2000, n=4)
        _normal_month(rng, f2, k, 300, n=2)
    f.withdraw(datetime(2026, 10, 6, 12, tzinfo=EDT), 900)
    f2.withdraw(datetime(2026, 10, 9, 12, tzinfo=EDT), 400)
    add("F", f, "Shares card ending 4417 and payout account with P-6011", "flag", "fraud_aml", "FINTRAC: card used by several players")
    add("F", f2, "Shares card ending 4417 and payout account with P-6012", "flag", "fraud_aml", "FINTRAC: card used by several players")

    # G - Just under the line: ~$50/week, then $9,500 x3 in 7 days.
    g = _new_player(rng, "P-7730", income="<20k", age="19-29", occupation="student", city=SSM)
    for k in range(6):
        _normal_month(rng, g, k, 200, n=4)
    for dd in (1, 4, 7):
        day = datetime(2026, 10, dd, tzinfo=EDT)
        g.deposit(_at(day, 14), 9500)
        g.session(rng, _at(day, 20), 1.5, 2000)
    add("G", g, "Three deposits of $9,500 in 7 days; usually ~$50/week", "flag", "fraud_aml",
        "FINTRAC: multiple transactions just below a reporting threshold")

    # H - Deposit and run: $12,000 in, $350 wagered, $11,600 out the next day.
    h = _new_player(rng, "P-8104", income="100-200k", age="30-44", occupation="sales manager", city=SSM)
    flat_history(h, 800, 2)
    h.deposit(datetime(2026, 10, 5, 15, tzinfo=EDT), 12000, method="e_transfer")
    h.session(rng, datetime(2026, 10, 5, 16, tzinfo=EDT), 0.5, 350, payback=0.9)
    h.withdraw(datetime(2026, 10, 6, 10, tzinfo=EDT), 11600)
    add("H", h, "Deposited $12,000, wagered $350, withdrew $11,600 next day", "flag", "fraud_aml",
        "FINTRAC: minimal play before withdrawal")

    # I - Holiday: $300/month, plays from a different Ontario city each day for a week. Control.
    i_ = _new_player(rng, "P-9021", income="50-100k", age="45-64", occupation="teacher", city=SSM)
    flat_history(i_, 300, 2)
    trip = ["Barrie", "Toronto", "Kingston", "Ottawa", "Kingston", "Toronto", "Niagara Falls", "Hamilton"]
    for n_day, city in enumerate(trip):
        day = datetime(2026, 9, 20, tzinfo=EDT) + timedelta(days=n_day)
        if n_day in (0, 4):
            i_.deposit(_at(day, 19), 150, city=city)
        i_.session(rng, _at(day, 19.5), 1.0, 60, city=city)
    add("I", i_, "Holiday: one Ontario city per day for a week, spend unchanged", "no_flag", None,
        "Control: travel is not risk")

    # J - Payout to someone else's account.
    j = _new_player(rng, "P-9988", income="20-50k", age="19-29", occupation="warehouse worker", city=SSM)
    for k in range(6):
        _normal_month(rng, j, k, 400, n=2)
    day = datetime(2026, 10, 2, tzinfo=EDT)
    j.session(rng, _at(day, 20), 1.5, 300, payback=4000 / 300)
    j.withdraw(_at(day + timedelta(days=1), 10), 4000, account=_fp(rng, "acct-"), holder_match=False)
    add("J", j, "Wins $4,000; payout requested to a bank account in another person's name", "flag", "fraud_aml",
        "FINTRAC: winnings transferred to another person")

    _plausible_occupations(players, {pid for _, pid, *_ in planted})
    _unique_names(players, {pid for _, pid, *_ in planted})
    return players, planted


TXN_COLS = ("player_id", "ts", "type", "amount", "method", "method_fingerprint", "method_last4",
            "location_region", "device_id", "payout_account", "payout_holder_match")
SES_COLS = ("player_id", "start_ts", "end_ts", "net_result", "location_region", "device_id")


def load(conn) -> dict:
    """TRUNCATE and reload everything. Used by first load and by /reset."""
    players, planted = build()
    txns = sorted((t for p in players for t in p.txns), key=lambda t: (t["ts"], t["player_id"]))
    sessions = sorted((s for p in players for s in p.sessions), key=lambda s: (s["start_ts"], s["player_id"]))
    with conn.cursor() as cur:
        cur.execute("TRUNCATE audit_event, planted_case, txn, session, player RESTART IDENTITY")
        with cur.copy("COPY player (id, display_name, occupation, income_band, age_band, region, peer_segment, created_at) FROM STDIN") as cp:
            for p in players:
                cp.write_row((p.id, p.display_name, p.occupation, p.income_band, p.age_band, p.region, p.peer_segment, p.created_at))
        with cur.copy(f"COPY txn ({', '.join(TXN_COLS)}) FROM STDIN") as cp:
            for t in txns:
                cp.write_row(tuple(t[c] for c in TXN_COLS))
        with cur.copy(f"COPY session ({', '.join(SES_COLS)}) FROM STDIN") as cp:
            for s in sessions:
                cp.write_row(tuple(s[c] for c in SES_COLS))
        with cur.copy("COPY planted_case (case_id, player_id, label, expected, expected_category, source_ref) FROM STDIN") as cp:
            for row in planted:
                cp.write_row(row)
    conn.commit()
    return {"players": len(players), "txns": len(txns), "sessions": len(sessions), "planted_rows": len(planted)}


if __name__ == "__main__":
    import psycopg

    with psycopg.connect(os.environ["DATABASE_URL"]) as c:
        print(load(c))
