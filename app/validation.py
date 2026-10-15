"""Validation panel (S1): Version 1.0 vs 2.0 on the planted cases and on the whole normal population.

This is the only place that reads `planted_case`. The scorer never does.
"""
from app.scoring.engine import PlayerScore

CAUGHT_RULE = "band Medium or High, or an STR candidate / URGENT label"


def build(conn, scores: list[PlayerScore]) -> dict:
    planted = conn.execute(
        "SELECT case_id, player_id, label, expected, expected_category FROM planted_case ORDER BY case_id, player_id"
    ).fetchall()
    by_id = {s.player_id: s for s in scores}
    planted_ids = {p["player_id"] for p in planted}
    rank = {s.player_id: i + 1 for i, s in enumerate(s for s in scores if s.caught)}

    rows = []
    for p in planted:
        s = by_id[p["player_id"]]
        flag = p["expected"] == "flag"
        rows.append({
            "case": p["case_id"], "player_id": s.player_id, "name": s.display_name, "label": p["label"],
            "expected": "Review" if flag else "Clear", "category": p["expected_category"],
            "v1": s.v1_flagged, "v1_ok": s.v1_flagged == flag,
            "score": s.score, "band": s.band, "labels": sorted({l.text for l in s.labels}),
            "v2": s.caught, "v2_ok": s.caught == flag, "rank": rank.get(s.player_id),
        })

    risky = [r for r in rows if r["expected"] == "Review"]
    controls = [r for r in rows if r["expected"] == "Clear"]
    normal = [s for s in scores if s.player_id not in planted_ids]
    v2_fp = [s for s in normal if s.caught]
    return {
        "rows": rows,
        "caught_rule": CAUGHT_RULE,
        "summary": {
            "risky_total": len(risky),
            "v1_risky_caught": sum(r["v1"] for r in risky),
            "v2_risky_caught": sum(r["v2"] for r in risky),
            "controls_total": len(controls),
            "v1_controls_flagged": sum(r["v1"] for r in controls),
            "v2_controls_flagged": sum(r["v2"] for r in controls),
            "normal_total": len(normal),
            "v1_normal_flagged": sum(s.v1_flagged for s in normal),
            "v2_normal_flagged": len(v2_fp),
            "v2_normal_high": sum(s.band == "High" for s in v2_fp),
            "v1_alerts_total": sum(s.v1_flagged for s in scores),
            "v2_alerts_total": sum(s.caught for s in scores),
        },
        "fp_examples": v2_fp[:10],
    }
