"""Version 1.0: an illustrative reconstruction of today's threshold-alert routine (D-2026-10-15-22).

Not OLG's system. It reproduces the routine the team assumes an investigator follows today:
an alert with no reason, separate screens to look things up, and a decision kept outside the system.
It reads the same synthetic data as Version 2.0 and writes nothing. No scores, no labels, no audit.
Steps are counted in the browser (static/steps.js) so the Before and After runs are measured the same way.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app import db
from app.scoring import config as C
from app.scoring import rules as RL

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE / "templates")
router = APIRouter(prefix="/v1")


def _threshold(conn) -> float:
    return float(RL.current(conn).v1_threshold)


@router.get("")
@router.get("/")
def alerts(request: Request):
    """Screen 1: every single deposit at or above the threshold, oldest first. No ranking, no reason."""
    with db.connect() as conn:
        t = _threshold(conn)
        rows = conn.execute(
            "SELECT id, player_id, ts, amount FROM txn WHERE type = 'deposit' AND amount >= %s"
            " AND ts >= %s AND ts < %s ORDER BY ts", (t, C.WIN_START, C.WIN_END)).fetchall()
    return templates.TemplateResponse(request, "v1_alerts.html", {"rows": rows, "threshold": t, "edt": C.EDT})


@router.get("/alert/{tid}")
def alert(request: Request, tid: int):
    """Screen 2: the one transaction that fired the rule. Nothing else."""
    with db.connect() as conn:
        t = _threshold(conn)
        a = conn.execute(
            "SELECT id, player_id, ts, amount, method, method_last4, location_region FROM txn"
            " WHERE id = %s AND type = 'deposit' AND amount >= %s", (tid, t)).fetchone()
    if not a:
        raise HTTPException(404, "alert not found")
    return templates.TemplateResponse(request, "v1_alert.html", {"a": a, "threshold": t, "edt": C.EDT})


@router.get("/history")
def history(request: Request, pid: str = ""):
    """Screen 3: raw deposit and withdrawal history (6 months) and raw play (30 days). No chart, no peers."""
    money, play = [], []
    if pid:
        with db.connect() as conn:
            money = conn.execute(
                "SELECT ts, type, amount, method, method_last4, method_fingerprint, location_region, payout_holder_match"
                " FROM txn WHERE player_id = %s AND type IN ('deposit','withdrawal') AND ts >= %s AND ts < %s ORDER BY ts DESC",
                (pid, C.HIST_START, C.WIN_END)).fetchall()
            play = conn.execute(
                "SELECT ts, amount FROM txn WHERE player_id = %s AND type = 'wager' AND ts >= %s AND ts < %s ORDER BY ts DESC LIMIT 200",
                (pid, C.WIN_START, C.WIN_END)).fetchall()
    return templates.TemplateResponse(request, "v1_history.html", {"pid": pid, "money": money, "play": play, "edt": C.EDT})


@router.get("/profile")
def profile(request: Request, pid: str = ""):
    """Screen 4: the customer record as an account system would show it."""
    p = None
    if pid:
        with db.connect() as conn:
            p = conn.execute("SELECT id, occupation, age_band, income_band, region, created_at FROM player WHERE id = %s",
                             (pid,)).fetchone()
    return templates.TemplateResponse(request, "v1_profile.html", {"pid": pid, "p": p, "edt": C.EDT})


@router.get("/lookup")
def lookup(request: Request, last4: str = ""):
    """Screen 5: the investigator types a card's last four digits to find other players using it."""
    rows = []
    last4 = last4.strip()[:4]
    if last4:
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT player_id, method_fingerprint, count(*) AS n, min(ts) AS first, max(ts) AS last FROM txn"
                " WHERE method_last4 = %s GROUP BY 1, 2 ORDER BY 1", (last4,)).fetchall()
    return templates.TemplateResponse(request, "v1_lookup.html", {"last4": last4, "rows": rows, "edt": C.EDT})


@router.get("/decision")
def decision(request: Request, pid: str = "", alert: str = ""):
    """Screen 6: a note box. Nothing is stored; the text is copied for the team spreadsheet."""
    return templates.TemplateResponse(request, "v1_decision.html", {"pid": pid, "alert": alert})
