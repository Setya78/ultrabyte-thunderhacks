"""AI case summary (B, D-2026-10-14-16). Optional, behind LLM_ENABLED; the score never depends on it.

The app sends only what the rules scorer already computed (score, band, check reasons, labels,
suggestion) to an n8n webhook, which asks Claude for a 3-sentence summary. No raw transactions,
no names. The reply is checked: every number in it must appear in the input; otherwise the rule
text is shown instead. Summaries are cached per score snapshot and written to the audit trail.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request

TIMEOUT_S = 25
_cache: dict[str, dict] = {}


def enabled() -> bool:
    return os.environ.get("LLM_ENABLED", "false") == "true" and bool(os.environ.get("N8N_WEBHOOK_URL"))


def payload(r: dict) -> dict:
    """Minimal input: computed reasons only (data minimization)."""
    return {
        "player_id": r["player_id"], "score": r["score"], "band": r["band"],
        "checks": [{"name": c["name"], "points": c["points"], "max": c["max"], "reason": c["reason"]} for c in r["checks"]],
        "labels": [{"text": l["text"], "reason": l["reason"]} for l in r["labels"]],
        "safer_gambling": {"score": r.get("harm_score", 0), "band": r.get("harm_band", "Low"),
                           "checks": [{"name": c["name"], "points": c["points"], "max": c["max"], "reason": c["reason"]}
                                      for c in r.get("harm_checks", [])]},
        "suggestion": r["suggestion"], "suggestion_rule": r["suggestion_rule"],
        "rule_version": r.get("rule_version", 1),
    }


def key(p: dict) -> str:
    return hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:16]


def rule_text(r: dict) -> str:
    scored = sorted((c for c in r["checks"] if c["points"]), key=lambda c: -c["points"])
    s1 = f"Score {r['score']} ({r['band']})" + (": " + " ".join(c["reason"] for c in scored[:2]) if scored else ": no check scored.")
    labels = list(dict.fromkeys(f"{l['text']}: {l['reason']}" for l in r["labels"]))
    sg = r.get("harm_band", "Low")
    if sg != "Low":
        top_sg = sorted((c for c in r.get("harm_checks", []) if c["points"]), key=lambda c: -c["points"])
        labels.append(f"Safer Gambling {r.get('harm_score', 0)} ({sg}): " + " ".join(c["reason"] for c in top_sg[:2]))
    s2 = " ".join(labels[:3]) if labels else "No labels."
    return f"{s1} {s2} Suggested: {r['suggestion']}."


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _norm(x: str) -> str:
    x = x.replace(",", "")
    return x[:-2] if x.endswith(".0") else x


def unsupported_numbers(summary: str, p: dict) -> list[str]:
    """Numbers in the summary that are not in the input (small counts 0-10 are allowed)."""
    source = {_norm(n) for n in _NUM.findall(json.dumps(p))}
    out = []
    for n in _NUM.findall(summary):
        v = _norm(n)
        if v in source:
            continue
        try:
            if float(v) <= 10:
                continue
        except ValueError:
            pass
        out.append(n)
    return out


def cached(r: dict) -> dict | None:
    return _cache.get(key(payload(r)))


def summarize(r: dict) -> dict:
    """Returns {text, source: 'ai'|'rules', model, note}. Never raises."""
    p = payload(r)
    k = key(p)
    if k in _cache:
        return _cache[k]
    fallback = {"text": rule_text(r), "source": "rules", "model": None, "note": ""}
    if not enabled():
        return {**fallback, "note": "LLM is off; showing rule text."}
    req = urllib.request.Request(os.environ["N8N_WEBHOOK_URL"], data=json.dumps(p).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          os.environ.get("N8N_WEBHOOK_HEADER", "X-UltraByte-Key"):
                                              os.environ.get("N8N_WEBHOOK_KEY", "")})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode() or "{}")
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return {**fallback, "note": f"AI summary unavailable ({type(exc).__name__}); showing rule text."}
    text = str(body.get("summary") or "").strip()
    if not text or len(text) > 1200:
        return {**fallback, "note": "AI reply was empty or too long; showing rule text."}
    bad = unsupported_numbers(text, p)
    if bad:
        return {**fallback, "note": f"AI reply rejected: {', '.join(bad[:3])} not in the computed reasons; showing rule text."}
    out = {"text": text, "source": "ai", "model": str(body.get("model") or "claude"), "note": ""}
    _cache[k] = out
    return out


def clear() -> None:
    _cache.clear()
