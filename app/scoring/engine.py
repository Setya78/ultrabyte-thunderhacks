"""Explainable context score (V2) and the Version 1.0 threshold rule.

Score = four checks x 25 points (income fit, own history, peers, location). Every point carries a
plain-English reason and a source. Labels (STR candidate, URGENT, Safer Gambling) add no points;
they pin a player near the top and say why. This module never reads `planted_case`.
"""
from __future__ import annotations

from bisect import bisect_left
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import timedelta

from app.scoring import config as C


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _round(x: float) -> int:
    return int(x + 0.5)  # half-up, not banker's rounding


@dataclass
class Check:
    key: str
    name: str
    points: int
    reason: str
    source: str
    max: int = 25


@dataclass
class Label:
    key: str
    text: str
    reason: str
    source: str


@dataclass
class PlayerScore:
    player_id: str
    display_name: str
    occupation: str
    age_band: str
    income_band: str
    region: str
    score: int
    band: str
    checks: list[Check]
    labels: list[Label]
    caught: bool
    top_reason: str
    v1_flagged: bool
    v1_reason: str
    metrics: dict = field(default_factory=dict)
    evidence_txn_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def priority(self) -> tuple:
        keys = {l.key for l in self.labels}
        return ("urgent" not in keys, "str" not in keys, -self.score)


def _month_index(ts) -> int | None:
    for k in range(len(C.MONTH_STARTS) - 1):
        if C.MONTH_STARTS[k] <= ts < C.MONTH_STARTS[k + 1]:
            return k
    return None


def load(conn) -> dict:
    """Pull everything the scorer needs in a few queries."""
    q = lambda sql, *a: conn.execute(sql, a).fetchall()
    return {
        "players": q("SELECT id, display_name, occupation, age_band, income_band, region, peer_segment FROM player"),
        "money": q("SELECT id, player_id, ts, type, amount, method_fingerprint, method_last4, payout_account,"
                   " payout_holder_match FROM txn WHERE type IN ('deposit','withdrawal') ORDER BY ts"),
        "wagers": q("SELECT player_id, ts, amount FROM txn WHERE type = 'wager' AND ts >= %s ORDER BY ts",
                    C.WIN_START - timedelta(days=7)),
        "sessions": q("SELECT player_id, start_ts, location_region FROM session WHERE start_ts >= %s AND start_ts < %s"
                      " ORDER BY start_ts", C.WIN_START, C.WIN_END),
    }


def score_all(data: dict) -> list[PlayerScore]:
    players = {p["id"]: p for p in data["players"]}
    monthly = defaultdict(lambda: [0.0] * (len(C.MONTH_STARTS) - 1))
    win_deposits, win_withdrawals, all_money = defaultdict(list), defaultdict(list), defaultdict(list)
    card_users, acct_users = defaultdict(set), defaultdict(set)
    first_seen_card, first_seen_acct = {}, {}

    for t in data["money"]:
        pid, amt = t["player_id"], float(t["amount"])
        all_money[pid].append(t)
        if t["type"] == "deposit":
            k = _month_index(t["ts"])
            if k is not None:
                monthly[pid][k] += amt
            if t["method_fingerprint"]:
                card_users[t["method_fingerprint"]].add(pid)
                first_seen_card.setdefault((pid, t["method_fingerprint"]), t["ts"])
            if C.WIN_START <= t["ts"] < C.WIN_END:
                win_deposits[pid].append(t)
        else:
            if t["payout_account"]:
                acct_users[t["payout_account"]].add(pid)
                first_seen_acct.setdefault((pid, t["payout_account"]), t["ts"])
            if C.WIN_START <= t["ts"] < C.WIN_END:
                win_withdrawals[pid].append(t)

    wagers = defaultdict(list)
    for w in data["wagers"]:
        wagers[w["player_id"]].append((w["ts"], float(w["amount"])))
    sessions = defaultdict(list)
    for s in data["sessions"]:
        sessions[s["player_id"]].append((s["start_ts"], s["location_region"]))

    dep30 = {pid: monthly[pid][C.HIST_MONTHS] for pid in players}
    peers = defaultdict(list)
    for pid, p in players.items():
        peers[p["peer_segment"]].append(dep30[pid])
    for seg in peers:
        peers[seg].sort()

    results = []
    for pid, p in players.items():
        results.append(_score_one(p, monthly[pid], dep30[pid], peers[p["peer_segment"]], win_deposits[pid],
                                  win_withdrawals[pid], all_money[pid], wagers[pid], sessions[pid],
                                  card_users, acct_users, first_seen_card, first_seen_acct))
    results.sort(key=lambda r: r.priority)
    return results


def _score_one(p, months, d30, peer_vals, wdeps, wwds, money, wagers, sessions,
               card_users, acct_users, first_card, first_acct) -> PlayerScore:
    pid = p["id"]
    hist_avg = sum(months[: C.HIST_MONTHS]) / C.HIST_MONTHS
    est_monthly = C.INCOME_MIDPOINT[p["income_band"]] / 12
    checks, labels, evidence = [], [], []

    # (a) Income fit
    r = d30 / est_monthly
    pts = 0 if r < C.INCOME_FIT_FLOOR else min(25, _round(25 * (r - C.INCOME_FIT_FLOOR) / C.INCOME_FIT_SPAN))
    reason = (f"Deposits of {_money(d30)} in 30 days are {r:.0%} of estimated monthly income "
              f"for the {p['income_band']} band ({p['occupation']}).")
    checks.append(Check("income", "Income fit", pts, reason, C.SOURCES["income"]))

    # (b) Own history
    base = max(C.HISTORY_MIN_BASE, hist_avg)
    r = d30 / base
    pts = 0 if r < C.HISTORY_FLOOR else min(25, _round(25 * (r - C.HISTORY_FLOOR) / C.HISTORY_SPAN))
    if pts:
        reason = f"Deposits rose from about {_money(hist_avg)} a month to {_money(d30)} in the last 30 days, {r:.0f} times usual."
    else:
        reason = f"Consistent with own history: about {_money(hist_avg)} a month over the previous 5 months."
    checks.append(Check("history", "Own history", pts, reason, C.SOURCES["history"]))

    # (c) Peers: share of other players in the same age band x income band below this player.
    others = list(peer_vals)
    others.remove(d30)
    pct = bisect_left(others, d30) / len(others) if others else 0.0
    pts = 25 if pct > C.PEER_P99 else 15 if pct >= C.PEER_P95 else 0
    reason = (f"Higher than {pct:.0%} of {len(others)} players aged {p['age_band']} "
              f"earning {p['income_band']}.")
    if C.PEER_MIN_GROUP and len(others) < C.PEER_MIN_GROUP:
        pts = 0
        reason = (f"Not scored: only {len(others)} comparable players (aged {p['age_band']}, earning "
                  f"{p['income_band']}); at least {C.PEER_MIN_GROUP} are needed for a fair comparison.")
    checks.append(Check("peer", "Peers", pts, reason, C.SOURCES["peer"]))

    # (d) Location: sessions from 3+ different cities within 24 hours.
    pts, reason = 0, "No unusual locations in the last 30 days."
    for i, (t0, _) in enumerate(sessions):
        cities = {c for t, c in sessions[i:] if t - t0 <= timedelta(hours=C.LOCATION_HOURS)}
        if len(cities) >= C.LOCATION_CITIES:
            span = [t for t, c in sessions[i:] if t - t0 <= timedelta(hours=C.LOCATION_HOURS)]
            hours = (max(span) - t0).total_seconds() / 3600
            pts = 25
            reason = f"Sessions from {', '.join(sorted(cities))} within {hours:.1f} hours."
            break
    checks.append(Check("location", "Location", pts, reason, C.SOURCES["location"]))

    # ---- labels (no points) ----
    str_reasons = []
    near = [t for t in wdeps if C.STRUCTURING_LOW <= float(t["amount"]) <= C.STRUCTURING_HIGH]
    if len(near) >= C.STRUCTURING_MIN:
        evidence += [t["id"] for t in near]
        str_reasons.append((f"{len(near)} deposits of {_money(C.STRUCTURING_LOW)}-{_money(10_000 - 1)} in 30 days, "
                            f"each just under $10,000 ({_money(sum(float(t['amount']) for t in near))} total).",
                            C.SOURCES["structuring"]))
    for wd in wwds:
        prior = [t for t in money if t["type"] == "withdrawal" and t["ts"] < wd["ts"]]
        since = max((t["ts"] for t in prior), default=wd["ts"] - timedelta(days=7))
        since = max(since, wd["ts"] - timedelta(days=7))
        deps = [t for t in money if t["type"] == "deposit" and since <= t["ts"] < wd["ts"]]
        dep_sum = sum(float(t["amount"]) for t in deps)
        wag_sum = sum(a for ts, a in wagers if since <= ts < wd["ts"])
        if dep_sum >= 100 and float(wd["amount"]) >= 0.5 * dep_sum and wag_sum < C.MINIMAL_PLAY_RATIO * dep_sum:
            evidence += [t["id"] for t in deps] + [wd["id"]]
            str_reasons.append((f"Deposited {_money(dep_sum)}, wagered {_money(wag_sum)} ({wag_sum / dep_sum:.0%}), "
                                f"withdrew {_money(float(wd['amount']))}.", C.SOURCES["minimal_play"]))
            break
    shared = set()
    for t in money:
        if t["type"] == "deposit" and t["method_fingerprint"] and len(card_users[t["method_fingerprint"]]) > 1:
            shared.add(("card", t["method_last4"], tuple(sorted(card_users[t["method_fingerprint"]] - {pid}))))
        if t["type"] == "withdrawal" and t["payout_account"] and len(acct_users[t["payout_account"]]) > 1:
            shared.add(("payout bank account", None, tuple(sorted(acct_users[t["payout_account"]] - {pid}))))
    for kind, last4, other in sorted(shared, key=str):
        what = f"Card ending {last4}" if kind == "card" else "Payout bank account"
        str_reasons.append((f"{what} is also used by {', '.join(other)}.", C.SOURCES["shared"]))
    third = [t for t in wwds if t["payout_holder_match"] is False]
    if third:
        evidence += [t["id"] for t in third]
        str_reasons.append((f"Payout of {_money(float(third[0]['amount']))} requested to a bank account "
                            f"in another person's name.", C.SOURCES["third_party"]))
    for text, src in str_reasons:
        labels.append(Label("str", "STR candidate", text, src))

    # URGENT: unusual location plus a new card or new payout account in the window.
    if checks[3].points:
        new_card = any(t["method_fingerprint"] and first_card[(pid, t["method_fingerprint"])] >= C.WIN_START
                       for t in wdeps)
        new_acct = any(t["payout_account"] and first_acct[(pid, t["payout_account"])] >= C.WIN_START
                       for t in wwds)
        if new_card or new_acct:
            parts = [x for x, ok in (("a new card", new_card), ("a new bank account", new_acct)) if ok]
            evidence += [t["id"] for t in wdeps + wwds]
            labels.append(Label("urgent", "URGENT", f"Unusual locations together with {' and '.join(parts)}: "
                                f"possible account takeover.", C.SOURCES["location"]))

    # Safer Gambling: rising deposits for 4+ months in a row, or mostly night play.
    run = best = 0
    for a, b in zip(months, months[1:]):
        run = run + 1 if b > a and a > 0 else 0
        best = max(best, run)
    if best >= C.ESCALATING_MONTHS:
        labels.append(Label("safer", "Safer Gambling", f"Deposits have risen {best} months in a row.", C.SOURCES["safer"]))
    if len(sessions) >= C.NIGHT_MIN_SESSIONS:
        night = sum(1 for t, _ in sessions if C.NIGHT_START_H <= t.astimezone(C.EDT).hour < C.NIGHT_END_H)
        share = night / len(sessions)
        if share >= C.NIGHT_SHARE:
            labels.append(Label("safer", "Safer Gambling",
                                f"{share:.0%} of recent sessions were between midnight and 4 a.m.", C.SOURCES["safer"]))

    score = sum(c.points for c in checks)
    band = "High" if score >= C.BAND_HIGH else "Medium" if score >= C.BAND_MEDIUM else "Low"
    keys = {l.key for l in labels}
    caught = band != "Low" or bool(keys & {"str", "urgent"})
    scored = sorted((c for c in checks if c.points), key=lambda c: -c.points)
    pinned = [l for l in labels if l.key in ("urgent", "str")] or [l for l in labels if l.key == "safer"]
    top = pinned[0].reason if pinned else scored[0].reason if scored else "No unusual activity."

    big = [t for t in wdeps if float(t["amount"]) >= C.V1_THRESHOLD]
    return PlayerScore(
        player_id=pid, display_name=p["display_name"], occupation=p["occupation"], age_band=p["age_band"],
        income_band=p["income_band"], region=p["region"], score=score, band=band, checks=checks, labels=labels,
        caught=caught, top_reason=top, v1_flagged=bool(big), v1_reason="Deposit over limit" if big else "",
        metrics={"dep30": round(d30, 2), "hist_monthly_avg": round(hist_avg, 2), "est_monthly_income": round(est_monthly, 2),
                 "peer_percentile": round(pct, 4), "peer_count": len(others), "monthly_deposits": [round(m, 2) for m in months]},
        evidence_txn_ids=sorted(set(evidence + [t["id"] for t in big])),
    )
