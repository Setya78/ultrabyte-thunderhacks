"""UltraByte - explainable alert triage (ThunderHacks II). All data is SYNTHETIC."""
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db

BASE = Path(__file__).resolve().parent
VERSION = "0.1.0-m0"

app = FastAPI(title="UltraByte", version=VERSION)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals.update(version=VERSION, llm_enabled=os.environ.get("LLM_ENABLED", "false") == "true")


@app.get("/health")
def health():
    return {"status": "ok", "version": VERSION, "data": "SYNTHETIC", **db.status()}


@app.get("/")
def queue(request: Request):
    # M0: empty queue. Ranked, explainable scores arrive in M1/M2.
    return templates.TemplateResponse(request, "queue.html", {"rows": [], "status": db.status()})


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
    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/", status_code=303)
    return {"reset": "ok", **counts}
