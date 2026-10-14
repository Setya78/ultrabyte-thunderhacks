"""UltraByte - explainable alert triage (ThunderHacks II). All data is SYNTHETIC."""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.scoring import engine

BASE = Path(__file__).resolve().parent
VERSION = "0.2.0-m1"

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
