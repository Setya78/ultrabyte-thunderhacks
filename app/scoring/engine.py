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
    suggestion: str = ""
    suggestion_rule: str = ""
    harm_score: int = 0
    harm_band: str = "Low"
    harm_checks: list = field(default_factory=list)
    rule_version: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def priority(self) -> tuple:
        keys = {l.key for l in self.labels}
        return ("urgent" not in keys, "str" not in keys, -max(self.score, self.harm_score if self.harm_band == "High" else 0), -self.score)


def suggest(band: str, labels: list[Label], checks: list[Check] | None = None, harm_band: str = "Low") -> tuple[str, str]:
    """Suggested next step (S2). Advice only: the investigator decides and records the decision."""
    keys = {l.key for l in labels}
    safer = " + Safer Gambling check-in" if harm_band != "Low" else ""
    if "urgent" in keys:
        return ("Escalate - Fraud: lock account, verify identity" + safer,
                "URGENT label: unusual locations with a new card or bank account")
    if "str" in keys:
        first = next(l for l in labels if l.key == "str")
        return ("Escalate - STR candidate: review for a suspicious transaction report" + safer,
                f"STR label: {first.reason}")
    if band == "High":
        return ("Escalate - AML: request source of funds" + safer, "Band High (score >= 50)")
    income = next((c for c in (checks or []) if c.key == "income"), None)
    if band == "Medium" and income and income.points == income.max:
        return ("Escalate - AML: request source of funds" + safer,
                "Band Medium and 30-day deposits at or above estimated monthly income")
    if harm_band == "High":
        return ("Escalate - Safer Gambling: proactive outreach, consider limits",
                "Safer Gambling band High (score >= 50)")
    if band == "Medium" and harm_band == "Medium":
        return ("Monitor - refer to Safer Gambling", "Band Medium and Safer Gambling band Medium")
    if band == "Medium":
        return ("Monitor - review again if the pattern continues", "Band Medium, no label")
    if harm_band == "Medium":
        return ("Monitor - refer to Safer Gambling", "Safer Gambling band Medium, context band Low")
    peer = next((c for c in (checks or []) if c.key == "peer"), None)
    peers = "" if peer is None or peer.reason.startswith("Not scored") else " and peers"
    return (f"Dismiss - consistent with income{',' if peers else ' and'} own history{peers}", "Band Low, no label")


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
        "sessions": q("SELECT player_id, start_ts, end_ts, net_result, location_region FROM session"
                      " WHERE start_ts >= %s AND start_ts < %s ORDER BY start_ts", C.WIN_START, C.WIN_END),
    }


def score_all(data: dict, rules=None) -> list[PlayerScore]:
    from app.scoring.rules import Rules, DEFAULTS

    R = rules or Rules(1, dict(DEFAULTS))
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
        sessions[s["player_id"]].append((s["start_ts"], s["location_region"], s["end_ts"], float(s["net_result"])))

    dep30 = {pid: monthly[pid][C.HIST_MONTHS] for pid in players}
    peers = defaultdict(list)
    for pid, p in players.items():
        peers[p["peer_segment"]].append(dep30[pid])
    for seg in peers:
        peers[seg].sort()

    # Peer "normal range" per month (10th-90th percentile) for the player-page chart.
    seg_month = defaultdict(lambda: [[] for _ in range(len(C.MONTH_STARTS) - 1)])
    for pid, p in players.items():
        for k, v in enumerate(monthly[pid]):
            seg_month[p["peer_segment"]][k].append(v)
    peer_range = {}
    for seg, cols in seg_month.items():
        rng = []
        for vals in cols:
            vals = sorted(vals)
            lo, hi = vals[int(0.10 * (len(vals) - 1))], vals[int(0.90 * (len(vals) - 1))]
            rng.append((round(lo, 2), round(hi, 2)))
        peer_range[seg] = rng

    results = []
    for pid, p in players.items():
        results.append(_score_one(p, monthly[pid], dep30[pid], peers[p["peer_segment"]], win_deposits[pid],
                                  win_withdrawals[pid], all_money[pid], wagers[pid], sessions[pid],
                                  card_users, acct_users, first_seen_card, first_seen_acct, R))
    for r in results:
        r.metrics["peer_range_monthly"] = peer_range[players[r.player_id]["peer_segment"]]
    results.sort(key=lambda r: r.priority)
    return results


def _score_one(p, months, d30, peer_vals, wdeps, wwds, money, wagers, sessions,
               card_users, acct_users, first_card, first_acct, R) -> PlayerScore:
    pid = p["id"]
    hist_avg = sum(months[: C.HIST_MONTHS]) / C.HIST_MONTHS
    est_monthly = C.INCOME_MIDPOINT[p["income_band"]] / 12
    checks, labels, evidence = [], [], []

    # (a) Income fit
    r = d30 / est_monthly
    pts = 0 if r < R.income_fit_floor else min(25, _round(25 * (r - R.income_fit_floor) / R.income_fit_span))
    reason = (f"Deposits of {_money(d30)} in 30 days are {r:.0%} of estimated monthly income "
              f"for the {p['income_band']} band ({p['occupation']}).")
    checks.append(Check("income", "Income fit", pts, reason, C.SOURCES["income"]))

    # (b) Own history
    base = max(R.history_min_base, hist_avg)
    r = d30 / base
    pts = 0 if r < R.history_floor else min(25, _round(25 * (r - R.history_floor) / R.history_span))
    if pts:
        reason = f"Deposits rose from about {_money(hist_avg)} a month to {_money(d30)} in the last 30 days, {r:.0f} times usual."
    else:
        reason = f"Consistent with own history: about {_money(hist_avg)} a month over the previous 5 months."
    checks.append(Check("history", "Own history", pts, reason, C.SOURCES["history"]))

    # (c) Peers: share of other players in the same age band x income band below this player.
    others = list(peer_vals)
    others.remove(d30)
    pct = bisect_left(others, d30) / len(others) if others else 0.0
    pts = 25 if pct > R.peer_p99 else 15 if pct >= R.peer_p95 else 0
    n_o = len(others)
    who = f"{n_o} player{'s' if n_o != 1 else ''} aged {p['age_band']} earning {p['income_band']}"
    # Review 2026-10-15 #2: "Higher than 100% of ..." read like an error.
    reason = f"Higher than all {who}." if others and pct >= 1 else f"Higher than {pct:.0%} of {who}."
    if R.peer_min_group and len(others) < R.peer_min_group:
        pts = 0
        reason = (f"Not scored: only {len(others)} comparable player{'s' if len(others) != 1 else ''} (aged {p['age_band']}, earning "
                  f"{p['income_band']}); at least {R.peer_min_group} are needed for a fair comparison.")
    checks.append(Check("peer", "Peers", pts, reason, C.SOURCES["peer"]))

    # (d) Location: sessions from 3+ different cities within 24 hours.
    pts, reason = 0, "No unusual locations in the last 30 days."
    for i, (t0, _, _, _) in enumerate(sessions):
        cities = {c for t, c, _, _ in sessions[i:] if t - t0 <= timedelta(hours=R.location_hours)}
        if len(cities) >= R.location_cities:
            span = [t for t, c, _, _ in sessions[i:] if t - t0 <= timedelta(hours=R.location_hours)]
            hours = (max(span) - t0).total_seconds() / 3600
            pts = 25
            reason = (f"Sessions from {', '.join(sorted(cities))} within {hours:.1f} hours"
                      + (": too far apart to travel in that time." if hours < 12 else "."))
            break
    checks.append(Check("location", "Location", pts, reason, C.SOURCES["location"]))

    # ---- labels (no points) ----
    str_reasons = []
    near = [t for t in wdeps if R.structuring_low <= float(t["amount"]) <= R.structuring_high]
    if len(near) >= R.structuring_min:
        evidence += [t["id"] for t in near]
        str_reasons.append((f"{len(near)} deposits of {_money(R.structuring_low)}-{_money(10_000 - 1)} in 30 days, "
                            f"each just under $10,000 ({_money(sum(float(t['amount']) for t in near))} total).",
                            C.SOURCES["structuring"]))
    for wd in wwds:
        prior = [t for t in money if t["type"] == "withdrawal" and t["ts"] < wd["ts"]]
        since = max((t["ts"] for t in prior), default=wd["ts"] - timedelta(days=7))
        since = max(since, wd["ts"] - timedelta(days=7))
        deps = [t for t in money if t["type"] == "deposit" and since <= t["ts"] < wd["ts"]]
        dep_sum = sum(float(t["amount"]) for t in deps)
        wag_sum = sum(a for ts, a in wagers if since <= ts < wd["ts"])
        if dep_sum >= 100 and float(wd["amount"]) >= 0.5 * dep_sum and wag_sum < R.minimal_play_ratio * dep_sum:
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
            labels.append(Label("urgent", "URGENT", f"Impossible travel between cities together with {' and '.join(parts)}: "
                                f"possible account takeover." if checks[3].reason.endswith("that time.") else
                                f"Unusual locations together with {' and '.join(parts)}: possible account takeover.", C.SOURCES["location"]))

    # ---- Safer Gambling score: four checks x 25, separate from the AML score (D-2026-10-15-19) ----
    harm = []
    run = best = 0
    for a, b in zip(months, months[1:]):
        run = run + 1 if a > 0 and b >= a * (1 + R.sg_escalation_min_rise) else 0  # review #4: tiny rises do not count
        best = max(best, run)
    pts = 25 if best >= R.sg_escalating_months else 15 if best >= R.sg_escalating_months - 1 else 0
    reason = (f"Deposits have risen at least {R.sg_escalation_min_rise:.0%} a month, {best} months in a row." if best >= 2
              else "No sustained rise in monthly deposits.")
    harm.append(Check("escalation", "Escalation", pts, reason, C.SOURCES["safer"]))

    n_sess = len(sessions)
    night = sum(1 for t, _, _, _ in sessions if C.NIGHT_START_H <= t.astimezone(C.EDT).hour < C.NIGHT_END_H)
    share = night / n_sess if n_sess else 0.0
    if n_sess < R.sg_night_min_sessions:
        pts, reason = 0, f"Not scored: only {n_sess} session{'s' if n_sess != 1 else ''} in the last 30 days."
    else:
        pts = 25 if share >= R.sg_night_share else 15 if share >= R.sg_night_share * 2 / 3 else 0
        reason = f"{share:.0%} of {n_sess} sessions were between midnight and 4 a.m."
    harm.append(Check("night", "Night play", pts, reason, C.SOURCES["night"]))

    chase = 0
    losing_ends = [e for _, _, e, net in sessions if net < 0]
    for t in wdeps:
        if any(0 <= (t["ts"] - e).total_seconds() <= R.sg_chase_minutes * 60 for e in losing_ends):
            chase += 1
    pts = 25 if chase >= R.sg_chase_count else 15 if chase >= R.sg_chase_count - 1 else 5 if chase >= 1 else 0
    reason = (f"{chase} deposits within {R.sg_chase_minutes} minutes of a losing session in 30 days."
              if chase else "No deposits made right after a losing session.")
    harm.append(Check("chase", "Loss chasing", pts, reason, C.SOURCES["chase"]))

    days = len({t.astimezone(C.EDT).date() for t, _, _, _ in sessions})
    pts = 25 if days >= R.sg_days_played else 15 if days >= 14 else 0
    reason = f"Played on {days} of the last 30 days."
    harm.append(Check("intensity", "Intensity", pts, reason, C.SOURCES["intensity"]))

    harm_score = sum(c.points for c in harm)
    harm_band = "High" if harm_score >= R.sg_band_high else "Medium" if harm_score >= R.sg_band_medium else "Low"

    score = sum(c.points for c in checks)
    band = "High" if score >= R.band_high else "Medium" if score >= R.band_medium else "Low"
    keys = {l.key for l in labels}
    caught = band != "Low" or bool(keys & {"str", "urgent"}) or harm_band != "Low"
    scored = sorted((c for c in checks + (harm if harm_band != "Low" else [])
                     if c.points), key=lambda c: -c.points)
    pinned = [l for l in labels if l.key in ("urgent", "str")]
    top = pinned[0].reason if pinned else scored[0].reason if scored else "No unusual activity."

    big = [t for t in wdeps if float(t["amount"]) >= R.v1_threshold]
    suggestion, rule = suggest(band, labels, checks, harm_band)
    return PlayerScore(
        suggestion=suggestion, suggestion_rule=rule, harm_score=harm_score, harm_band=harm_band, harm_checks=harm,
        rule_version=R.version,
        player_id=pid, display_name=p["display_name"], occupation=p["occupation"], age_band=p["age_band"],
        income_band=p["income_band"], region=p["region"], score=score, band=band, checks=checks, labels=labels,
        caught=caught, top_reason=top, v1_flagged=bool(big), v1_reason="Deposit over limit" if big else "",
        metrics={"dep30": round(d30, 2), "hist_monthly_avg": round(hist_avg, 2), "est_monthly_income": round(est_monthly, 2),
                 "peer_percentile": round(pct, 4), "peer_count": len(others), "monthly_deposits": [round(m, 2) for m in months]},
        evidence_txn_ids=sorted(set(evidence + [t["id"] for t in big])),
    )
