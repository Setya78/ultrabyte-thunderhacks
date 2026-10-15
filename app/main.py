"""UltraByte - explainable alert triage (ThunderHacks II). All data is SYNTHETIC."""
import os
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db, validation
from app.audit import log as audit
from app.scoring import config as C
from app.scoring import engine

BASE = Path(__file__).resolve().parent
VERSION = "0.6.0-c1"

app = FastAPI(title="UltraByte", version=VERSION)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals.update(version=VERSION, llm_enabled=os.environ.get("LLM_ENABLED", "false") == "true")

_cache: dict = {}


def scores() -> list[engine.PlayerScore]:
    """Score everyone once and keep it until the data is reset (data is static between resets)."""
    if "scores" not in _cache:
        with db.connect() as conn:
            _cache["scores"] = engine.score_all(engine.load(conn))
    return _cache["scores"]


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION, "data": "SYNTHETIC", **db.status()}


@app.get("/")
def queue(request: Request, mode: str = "v2"):
    status = db.status()
    rows, mode = [], ("v1" if mode == "v1" else "v2")
    if status.get("db") == "ok" and status.get("players"):
        all_rows = scores()
        if mode == "v1":
            rows = [r for r in all_rows if r.v1_flagged]  # Version 1.0: alert list, no ranking, no reasons
        else:
            rows = [r for r in all_rows if r.caught]
    return templates.TemplateResponse(request, "queue.html", {"rows": rows, "mode": mode, "status": status})


def _by_id(pid: str) -> engine.PlayerScore:
    for r in scores():
        if r.player_id == pid:
            return r
    raise HTTPException(404, "player not found")


def _chart(r: engine.PlayerScore) -> dict:
    """Six monthly deposit bars with the peer group's 10th-90th percentile range behind them."""
    vals = r.metrics["monthly_deposits"]
    rng = r.metrics["peer_range_monthly"]
    top = max(vals + [hi for _, hi in rng] + [1.0]) * 1.1
    w, h, pad, n = 560, 180, 28, len(vals)
    slot = (w - pad) / n
    y = lambda v: h - pad - (h - 2 * pad) * v / top
    labels = ["Apr-May", "May-Jun", "Jun-Jul", "Jul-Aug", "Aug-Sep", "Last 30 days"]
    bars = []
    for k, v in enumerate(vals):
        x = pad + k * slot
        lo, hi = rng[k]
        bars.append({"x": x + slot * 0.2, "bw": slot * 0.6, "y": y(v), "bh": max(1.0, y(0) - y(v)),
                     "band_y": y(hi), "band_h": max(1.0, y(lo) - y(hi)), "band_x": x + 2, "band_w": slot - 4,
                     "value": v, "label": labels[k], "current": k == n - 1})
    return {"w": w, "h": h, "base": y(0), "bars": bars, "max": top}


@app.get("/player/{pid}")
def player(request: Request, pid: str, mode: str = "v2"):
    r = _by_id(pid)
    with db.connect() as conn:
        txns = conn.execute(
            "SELECT id, ts, type, amount, method_last4, location_region, payout_holder_match FROM txn"
            " WHERE player_id = %s AND type IN ('deposit','withdrawal') AND ts >= %s AND ts < %s ORDER BY ts",
            (pid, C.WIN_START, C.WIN_END)).fetchall()
        places = conn.execute(
            "SELECT location_region AS city, count(*) AS sessions, min(start_ts) AS first, max(start_ts) AS last"
            " FROM session WHERE player_id = %s AND start_ts >= %s AND start_ts < %s GROUP BY 1 ORDER BY 3",
            (pid, C.WIN_START, C.WIN_END)).fetchall()
        history = audit.for_player(conn, pid)
    return templates.TemplateResponse(request, "player.html", {
        "r": r, "txns": txns, "places": places, "history": history, "chart": _chart(r),
        "evidence": set(r.evidence_txn_ids), "edt": C.EDT, "actions": audit.ACTIONS, "mode": mode})


@app.post("/player/{pid}/decision")
def decision(pid: str, action: str = Form(...), note: str = Form("")):
    r = _by_id(pid)
    with db.connect() as conn:
        audit.record(conn, pid, action, note, r.to_dict())
    return RedirectResponse(f"/player/{pid}#audit", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request):
    rows = scores()

    def group(key, title, desc, team, pick):
        players = [(r, why) for r in rows for why in [pick(r)] if why]
        return {"key": key, "title": title, "desc": desc, "team": team, "players": players}

    def label_reason(key):
        return lambda r: next((l.reason for l in r.labels if l.key == key), None)

    groups = [
        group("urgent", "URGENT: possible account takeover", "Unusual locations + new card or bank account",
              "Fraud", label_reason("urgent")),
        group("str", "STR candidates", "FINTRAC indicators: structuring, minimal play, shared or third-party accounts",
              "AML", label_reason("str")),
        group("aml", "Context risk (no label)", "Medium or High score from the four checks, no STR / URGENT label",
              "AML", lambda r: r.top_reason if r.band != "Low" and not any(l.key in ("str", "urgent") for l in r.labels) else None),
        group("safer", "Safer Gambling", "Rising deposits or mostly night play",
              "Safer Gambling", label_reason("safer")),
    ]
    return templates.TemplateResponse(request, "dashboard.html", {"groups": groups})


@app.get("/network")
def network(request: Request):
    with db.connect() as conn:
        rows = conn.execute("""
            SELECT 'Card' AS kind, method_fingerprint AS ref, max(method_last4) AS last4,
                   array_agg(DISTINCT player_id ORDER BY player_id) AS players, count(*) AS uses
              FROM txn WHERE type = 'deposit' AND method_fingerprint IS NOT NULL GROUP BY method_fingerprint
            HAVING count(DISTINCT player_id) > 1
            UNION ALL
            SELECT 'Payout bank account', payout_account, NULL, array_agg(DISTINCT player_id ORDER BY player_id), count(*)
              FROM txn WHERE type = 'withdrawal' AND payout_account IS NOT NULL GROUP BY payout_account
            HAVING count(DISTINCT player_id) > 1
            ORDER BY 1, 2""").fetchall()
    by_id = {r.player_id: r for r in scores()}
    links = [{"kind": r["kind"], "ref": r["ref"][:9] + "...", "last4": r["last4"], "uses": r["uses"],
              "players": [by_id[p] for p in r["players"]]} for r in rows]
    return templates.TemplateResponse(request, "network.html", {"links": links})


@app.get("/validation")
def validation_page(request: Request):
    with db.connect() as conn:
        v = validation.build(conn, scores())
    return templates.TemplateResponse(request, "validation.html", {"v": v})


@app.get("/audit")
def audit_page(request: Request):
    with db.connect() as conn:
        rows = audit.recent(conn)
    return templates.TemplateResponse(request, "audit.html", {"rows": rows, "edt": C.EDT})


@app.get("/api/scores")
def api_scores(caught_only: bool = True):
    return [r.to_dict() for r in scores() if r.caught or not caught_only]


@app.post("/reset")
def reset(request: Request):
    """Restore the synthetic seed so the demo can be repeated."""
    from db.seed.generate import load

    if not db.database_url():
        return JSONResponse({"reset": "skipped", "reason": "db not_configured"}, status_code=503)
    with db.connect() as conn:
        counts = load(conn)
        conn.execute(
            "INSERT INTO audit_event (actor, action, note) VALUES ('system', 'reset', 'Demo data restored to synthetic seed')"
        )
        conn.commit()
    _cache.clear()
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/", status_code=303)
    return {"reset": "ok", **counts}
