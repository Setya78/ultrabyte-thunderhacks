"""UltraByte - explainable alert triage (ThunderHacks II). All data is SYNTHETIC."""
import os
from pathlib import Path

import secrets

from psycopg.types.json import Jsonb

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse, Response
from urllib.parse import quote
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import auth, db, importer, judge, llm, validation, v1 as legacy
from app.audit import log as audit
from app.scoring import config as C
from app.scoring import engine
from app.scoring import rules as RL

BASE = Path(__file__).resolve().parent
VERSION = "0.15.0-worklist"

app = FastAPI(title="UltraByte Solutions", version=VERSION)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
app.include_router(legacy.router)  # Version 1.0 reconstruction at /v1 (D-2026-10-15-22); not linked from Version 2.0 navigation


@app.middleware("http")
async def require_login(request: Request, call_next):
    """Every page needs a signed session when OPERATOR_ACCOUNTS is set (D-2026-10-15-20)."""
    request.state.user, request.state.role = None, None
    path = request.url.path
    if auth.enabled():
        who = auth.read_cookie(request.cookies.get(auth.COOKIE))
        if who:
            request.state.user, request.state.role = who
        elif not path.startswith(auth.PUBLIC):
            if request.method == "GET":
                return RedirectResponse(f"/login?next={quote(path)}", status_code=303)
            return JSONResponse({"error": "sign in required"}, status_code=401)
    return await call_next(request)


def _actor(request: Request) -> str:
    return request.state.user or audit.ACTOR


def _require_role(request: Request, role: str):
    if auth.enabled() and request.state.role != role:
        raise HTTPException(403, f"{role} role required")


@app.get("/login")
def login_page(request: Request, next: str = "/"):
    if not auth.enabled():
        return RedirectResponse("/", status_code=303)
    if request.state.user:
        return RedirectResponse(next if next.startswith("/") else "/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": "", "next": next})


@app.post("/login")
def login_post(request: Request, username: str = Form(""), password: str = Form(""), next: str = Form("/")):
    role = auth.check(username.strip(), password)
    if not role:
        return templates.TemplateResponse(request, "login.html", {"error": "Wrong username or password.", "next": next}, status_code=401)
    with db.connect() as conn:
        conn.execute("INSERT INTO audit_event (actor, action, note) VALUES (%s, 'login', %s)", (username.strip(), f"Signed in as {role}"))
        conn.commit()
    resp = RedirectResponse(next if next.startswith("/") and not next.startswith("//") else "/", status_code=303)
    resp.set_cookie(auth.COOKIE, auth.make_cookie(username.strip(), role), max_age=auth.TTL_S, httponly=True, samesite="lax",
                    secure=request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https")
    return resp


@app.get("/about")
def about(request: Request):
    return templates.TemplateResponse(request, "about.html", {"llm_model": "claude-haiku-5-5"})


@app.get("/profile")
def profile(request: Request):
    if not request.state.user:
        return RedirectResponse("/", status_code=303)
    from datetime import datetime, timezone

    raw = request.cookies.get(auth.COOKIE) or ""
    try:
        exp = datetime.fromtimestamp(int(raw.split("|")[2]), tz=timezone.utc)
    except (IndexError, ValueError):
        exp = datetime.now(tz=timezone.utc)
    with db.connect() as conn:
        rows = conn.execute("SELECT id, ts, player_id, action, note FROM audit_event WHERE actor = %s ORDER BY ts DESC, id DESC LIMIT 20",
                            (request.state.user,)).fetchall()
    return templates.TemplateResponse(request, "profile.html", {
        "me": {"user": request.state.user, "role": request.state.role, "expires": exp}, "rows": rows, "edt": C.EDT})


@app.post("/logout")
def logout(request: Request):
    if request.state.user:
        with db.connect() as conn:
            conn.execute("INSERT INTO audit_event (actor, action, note) VALUES (%s, 'logout', 'Signed out')", (request.state.user,))
            conn.commit()
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.COOKIE)
    return resp
templates = Jinja2Templates(directory=BASE / "templates")
# One-time form tokens: a second click (or a browser retry) with the same token is not saved twice.
from collections import deque
_used_tokens: deque = deque(maxlen=2000)


def _fresh_token() -> str:
    return secrets.token_urlsafe(12)


def _already_used(tok: str) -> bool:
    if not tok:
        return False
    if tok in _used_tokens:
        return True
    _used_tokens.append(tok)
    return False


GLOSSARY = {
    "STR": "Suspicious Transaction Report: a report a casino or online operator must file with FINTRAC when it suspects money laundering. 'STR candidate' means the pattern matches a FINTRAC indicator and an investigator should review it.",
    "AML": "Anti-money laundering: the checks that look for money moving through the account rather than being played.",
    "SG": "Safer Gambling: player-protection checks that look for signs of harm to the player (rising deposits, night play, chasing losses, playing most days).",
    "FINTRAC": "Financial Transactions and Reports Analysis Centre of Canada: the federal agency that receives suspicious transaction reports.",
    "URGENT": "Possible account takeover: unusual locations together with a new card or bank account. Handled by the fraud team first.",
    "EDT": "Eastern Daylight Time (Ontario).",
    "V1": "Version 1.0: today's routine. A threshold alarm (any single deposit of $10,000 or more) with no ranking and no reason; the investigator opens separate screens and keeps the decision outside the system.",
    "V2": "Version 2.0: this app. Two scores with reasons, labels with evidence, and an audit trail.",
    "ROLE_investigator": "Reviews the queue, records decisions, enters transactions, requests AI summaries. Sees rules read-only.",
    "ROLE_compliance": "Everything an investigator can do, plus changing the rule thresholds and closing escalated cases (Mark as handling / Mark resolved); each step is versioned and audited.",
    "STATUS": "Case status = the latest decision or hand-off step in the audit trail. Investigators escalate; compliance marks the case In progress, then Resolved. Both roles see the same status; nothing is edited in place.",
}
templates.env.globals.update(version=VERSION, llm_enabled=llm.enabled(), labels=audit.LABELS, gloss=GLOSSARY, form_token=_fresh_token, auth_enabled=auth.enabled)

_cache: dict = {}


def scores() -> list[engine.PlayerScore]:
    """Score everyone once and keep it until the data is reset (data is static between resets)."""
    if "scores" not in _cache:
        with db.connect() as conn:
            _cache["scores"] = engine.score_all(engine.load(conn), RL.current(conn))
    return _cache["scores"]


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION, "data": "SYNTHETIC", **db.status()}


@app.get("/")
def queue(request: Request):
    """Version 2.0 queue only. Version 1.0 is a separate console at /v1 (D-2026-10-15-22 supersedes the Before | After split)."""
    status = db.status()
    rows = []
    decided: dict = {}
    if status.get("db") == "ok" and status.get("players"):
        rows = [r for r in scores() if r.caught]
        # Owner 2026-10-15: the queue is the worklist. A player with a recorded decision moves to "Decided" below the
        # players that still need one; the latest decision per player comes from the append-only audit trail.
        with db.connect() as conn:
            decided = audit.case_status(conn)
    todo = [r for r in rows if r.player_id not in decided]
    order = {s: i for i, s in enumerate(audit.STATE_ORDER)}
    done = sorted((r for r in rows if r.player_id in decided), key=lambda r: (order[decided[r.player_id]["state"]], r.priority))
    return templates.TemplateResponse(request, "queue.html", {"rows": rows, "todo": todo, "done": done, "decided": decided,
                                                              "status": status, "edt": C.EDT})


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
def player(request: Request, pid: str):
    r = _by_id(pid)
    with db.connect() as conn:
        txns = conn.execute(
            "SELECT id, ts, type, amount, method, method_last4, location_region, payout_holder_match, entry_source,"
            " payout_account IS NOT NULL AND payout_account NOT IN (SELECT payout_account FROM txn h WHERE h.player_id = %s"
            "   AND h.payout_account IS NOT NULL AND h.ts < %s) AS new_account FROM txn"
            " WHERE player_id = %s AND (type IN ('deposit','withdrawal') OR (type = 'win' AND amount >= %s))"
            " AND ts >= %s AND ts < %s ORDER BY ts",
            (pid, C.WIN_START, pid, BIG_WIN, C.WIN_START, C.WIN_END)).fetchall()
        places = conn.execute(
            "SELECT location_region AS city, count(*) AS sessions, min(start_ts) AS first, max(start_ts) AS last"
            " FROM session WHERE player_id = %s AND start_ts >= %s AND start_ts < %s GROUP BY 1 ORDER BY 3",
            (pid, C.WIN_START, C.WIN_END)).fetchall()
        history = audit.for_player(conn, pid)
        case = audit.case_status(conn).get(pid)
    can_status = (not auth.enabled()) or request.state.role == "compliance"
    return templates.TemplateResponse(request, "player.html", {
        "r": r, "txns": txns, "places": places, "history": history, "chart": _chart(r),
        "evidence": set(r.evidence_txn_ids), "edt": C.EDT, "actions": audit.ACTIONS,
        "case": case, "status_actions": audit.STATUS_ACTIONS, "can_status": can_status,
        "summary": _summary_for(r)})


BIG_WIN = 1000  # wins of $1,000 or more are listed on the player page so a large payout has its source (review #9)

_summary_tries: dict[str, dict] = {}


def _summary_for(r: engine.PlayerScore) -> dict | None:
    """AI summary if one exists for this exact score; otherwise the last attempt's fallback; else rule text when LLM is off."""
    d = r.to_dict()
    k = llm.key(llm.payload(d))
    return llm.cached(d) or _summary_tries.get(k)


@app.post("/player/{pid}/summary")
def summary(request: Request, pid: str, tok: str = Form("", alias="_tok")):
    if _already_used(tok):
        return RedirectResponse(f"/player/{pid}?ok=Already+requested#summary", status_code=303)
    r = _by_id(pid)
    d = r.to_dict()
    res = llm.summarize(d)
    _summary_tries[llm.key(llm.payload(d))] = res
    if res["source"] == "ai":
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO audit_event (actor, player_id, action, note, score_snapshot) VALUES (%s, %s, 'ai_summary', %s, %s)",
                (f"AI summary ({res['model']} via n8n), requested by {_actor(request)}", pid, res["text"], Jsonb(d)))
            conn.commit()
    return RedirectResponse(f"/player/{pid}?ok=Summary+{'generated' if res['source'] == 'ai' else 'unavailable,+rule+text+shown'}#summary", status_code=303)


@app.post("/player/{pid}/decision")
def decision(request: Request, pid: str, action: str = Form(...), note: str = Form(""), tok: str = Form("", alias="_tok")):
    if _already_used(tok):
        return RedirectResponse(f"/player/{pid}?ok=Already+saved+(duplicate+click+ignored)#audit", status_code=303)
    r = _by_id(pid)
    with db.connect() as conn:
        audit.record(conn, pid, action, note, r.to_dict(), actor=_actor(request))
    return RedirectResponse(f"/player/{pid}?ok=Decision+saved+to+the+audit+trail#audit", status_code=303)


@app.post("/player/{pid}/status")
def case_status_post(request: Request, pid: str, action: str = Form(...), note: str = Form(""), tok: str = Form("", alias="_tok")):
    """Compliance-only hand-off: 'handling' (picked up) or 'resolve' (closed). Append-only, like a decision."""
    _require_role(request, "compliance")
    if action not in audit.STATUS_ACTIONS:
        raise HTTPException(400, "unknown status")
    if _already_used(tok):
        return RedirectResponse(f"/player/{pid}?ok=Already+saved+(duplicate+click+ignored)#audit", status_code=303)
    r = _by_id(pid)
    with db.connect() as conn:
        audit.record(conn, pid, action, note, r.to_dict(), actor=_actor(request))
    return RedirectResponse(f"/player/{pid}?ok=Case+status+saved+to+the+audit+trail#audit", status_code=303)


_entries: dict[str, dict] = {}


@app.get("/enter")
def enter_page(request: Request, r: str = "", pid: str = ""):
    return templates.TemplateResponse(request, "enter.html", {
        "res": _entries.get(r), "errors": [], "form": {"player_id": pid}, "cities": judge.CITIES,
        "methods": judge.METHODS, "ages": importer.AGE_BANDS, "incomes": importer.INCOME_BANDS,
        "occupations": judge.OCCUPATIONS})


@app.post("/enter")
async def enter_post(request: Request):
    form = {k: str(v) for k, v in (await request.form()).items()}
    if _already_used(form.get("_tok", "")):
        return RedirectResponse(f"/enter?pid={form.get('player_id', '')}&ok=Already+saved+(duplicate+click+ignored)", status_code=303)
    entry, errors = judge.parse(form)
    before = None
    if entry and entry.player_id:
        try:
            before = _by_id(entry.player_id).to_dict()
        except HTTPException:
            errors = [f"No player with ID {entry.player_id}. Check the Review queue, or switch to New player (the ID is assigned automatically)."]
    if errors:
        return templates.TemplateResponse(request, "enter.html", {
            "res": None, "errors": errors, "form": form, "cities": judge.CITIES, "methods": judge.METHODS,
            "ages": importer.AGE_BANDS, "incomes": importer.INCOME_BANDS, "occupations": judge.OCCUPATIONS}, status_code=400)
    with db.connect() as conn:
        pid = judge.save(conn, entry)
        _cache.clear()
        after = _by_id(pid).to_dict()
        judge.record(conn, pid, entry, before, after, actor=_actor(request))
    tok = secrets.token_urlsafe(8)
    if len(_entries) > 50:
        _entries.clear()
    _entries[tok] = {"pid": pid, "before": before, "after": after, "diff": judge.diff(before, after),
                     "entry": entry}
    return RedirectResponse(f"/enter?r={tok}&pid={pid}&ok=Saved.+{pid}+rescored.", status_code=303)


@app.get("/rules")
def rules_page(request: Request, saved: int = 0):
    with db.connect() as conn:
        cur = RL.current(conn)
        hist = RL.history(conn)
    return templates.TemplateResponse(request, "rules.html", {
        "spec": RL.SPEC, "values": cur.values, "rule_version": cur.version, "defaults": RL.DEFAULTS,
        "history": hist, "errors": [], "saved": saved, "edt": C.EDT,
        "can_edit": (not auth.enabled()) or request.state.role == "compliance"})


@app.post("/rules")
async def rules_post(request: Request):
    _require_role(request, "compliance")
    form = {k: str(v) for k, v in (await request.form()).items()}
    if _already_used(form.get("_tok", "")):
        return RedirectResponse("/rules?ok=Already+saved+(duplicate+click+ignored)", status_code=303)
    if form.get("step") == "defaults":
        values, errors = dict(RL.DEFAULTS), []
        note = "Reset to defaults (version 1)"
    else:
        values, errors = RL.validate(form)
        note = (form.get("note") or "").strip()[:200]
        if not note:
            errors.append("A reason is required: it goes into the audit trail with the change.")
    with db.connect() as conn:
        prev = RL.current(conn)
        if not errors and not RL.changed_keys(prev.values, values):
            errors.append("Nothing changed.")
        if errors:
            hist = RL.history(conn)
            return templates.TemplateResponse(request, "rules.html", {
                "spec": RL.SPEC, "values": {**prev.values, **{k: form.get(k, v) for k, v in prev.values.items()}},
                "rule_version": prev.version, "defaults": RL.DEFAULTS, "history": hist, "errors": errors, "saved": 0,
                "edt": C.EDT, "can_edit": True}, status_code=400)
        vid = RL.save(conn, values, _actor(request), note, prev)
    _cache.clear()
    llm.clear()
    return RedirectResponse(f"/rules?saved={vid}&ok=Saved+as+rules+version+{vid}.+All+players+rescored.", status_code=303)


@app.get("/dashboard")
def dashboard(request: Request):
    rows = scores()

    short = {"urgent": "URGENT", "str": "STR", "aml": "AML context", "safer": "Safer Gambling", "new": "Newly added"}

    def team_view(key, r):
        """Each group shows its own team's score and next step (review 2026-10-15 #7)."""
        if key == "safer":
            step = ("Escalate - Safer Gambling: proactive outreach, consider limits" if r.harm_band == "High"
                    else "Monitor - refer to Safer Gambling")
            return r.harm_score, step
        return r.score, engine.suggest(r.band, r.labels, r.checks)[0]

    def group(key, title, desc, team, pick):
        players = [(r, why) + team_view(key, r) for r in rows for why in [pick(r)] if why]
        players.sort(key=lambda x: -x[2])
        return {"key": key, "title": title, "desc": desc, "team": team, "players": players, "short": short[key]}

    def label_reason(key):
        return lambda r: next((l.reason for l in r.labels if l.key == key), None)

    groups = [
        group("urgent", "URGENT: possible account takeover", "Unusual locations together with a new card or bank account",
              "Fraud", label_reason("urgent")),
        group("str", "STR candidates (Suspicious Transaction Report)", "FINTRAC indicators: deposits just under $10,000, little play before withdrawal, shared or third-party accounts",
              "AML", label_reason("str")),
        group("aml", "AML context risk (no label)", "Medium or High anti-money-laundering score from the four checks, no label",
              "AML", lambda r: r.top_reason if r.band != "Low" and not any(l.key in ("str", "urgent") for l in r.labels) else None),
        group("safer", "Safer Gambling", "Safer Gambling score Medium or High: escalation, night play, loss chasing, intensity",
              "Safer Gambling", lambda r: next((c.reason for c in sorted(r.harm_checks, key=lambda c: -c.points) if c.points), None)
              if r.harm_band != "Low" else None),
        # Owner 2026-10-15: players added during the session (Manual entry or Import) get their own group, whatever their score.
        group("new", "Newly added (manual entry or import)", "Players created in this demo session, not part of the seed; scored by the same rules",
              "Data", lambda r: f"Added by {r.source}: {r.top_reason}" if r.source != "seed" else None),
    ]
    # Team feedback 2026-10-15: show when the same player sits in more than one group, so it is not read as two people.
    member = {}
    for g in groups:
        for r, *_ in g["players"]:
            member.setdefault(r.player_id, []).append(g["short"])
    return templates.TemplateResponse(request, "dashboard.html", {"groups": groups, "member": member})


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


_pending: dict[str, importer.Result] = {}


@app.get("/import")
def import_page(request: Request):
    return templates.TemplateResponse(request, "import.html", {"result": None, "loaded": None})


@app.get("/import/template.xlsx")
def import_template():
    return Response(importer.template_xlsx(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="ultrabyte-import-template.xlsx"'})


@app.post("/import")
async def import_post(request: Request, step: str = Form("check"), mode: str = Form("replace"),
                      token: str = Form(""), file: UploadFile | None = File(None)):
    mode = "append" if mode == "append" else "replace"
    if step == "load":
        res = _pending.pop(token, None)
        if res is None or not res.ok:
            raise HTTPException(400, "Nothing to load: check the file first")
        with db.connect() as conn:
            try:
                counts = importer.load(conn, res, mode)
            except ValueError as exc:
                return templates.TemplateResponse(request, "import.html",
                                                  {"result": importer.Result(errors=[str(exc)]), "loaded": None, "filename": ""})
        _cache.clear()
        return templates.TemplateResponse(request, "import.html", {"result": None, "loaded": counts})
    if file is None or not file.filename:
        raise HTTPException(400, "Choose a file")
    data = await file.read()
    if len(data) > 5_000_000:
        res = importer.Result(errors=["File is larger than 5 MB"])
    else:
        res = importer.parse(file.filename, data)
    tok = ""
    if res.ok:
        tok = secrets.token_urlsafe(12)
        _pending.clear()  # single-user demo: keep only the latest checked file
        _pending[tok] = res
    return templates.TemplateResponse(request, "import.html",
                                      {"result": res, "loaded": None, "filename": file.filename, "token": tok, "mode": mode})


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
            "INSERT INTO audit_event (actor, action, note) VALUES (%s, 'reset', 'Demo data restored to synthetic seed')",
            (_actor(request) if request.state.user else "system",)
        )
        conn.commit()
    _cache.clear()
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/?ok=Demo+data+reset+to+the+synthetic+seed", status_code=303)
    return {"reset": "ok", **counts}
