"""Operator login (D-2026-10-15-20). Demo-grade: static accounts from the environment, signed cookie session.

OPERATOR_ACCOUNTS="investigator:<password>:investigator,compliance:<password>:compliance"
SECRET_KEY=<random string>   (signs the session cookie)
Both live only in the VPS .env (HS2). If OPERATOR_ACCOUNTS is unset, login is off and every page says so.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time

ROLES = ("investigator", "compliance")
COOKIE = "ub_session"
TTL_S = 8 * 3600
PUBLIC = ("/login", "/health", "/static")


def accounts() -> dict[str, tuple[str, str]]:
    out = {}
    for part in os.environ.get("OPERATOR_ACCOUNTS", "").split(","):
        bits = part.strip().split(":")
        if len(bits) == 3 and bits[2] in ROLES and bits[0] and bits[1]:
            out[bits[0]] = (bits[1], bits[2])
    return out


def enabled() -> bool:
    return bool(accounts()) and bool(os.environ.get("SECRET_KEY"))


def check(user: str, password: str) -> str | None:
    """Returns the role on success. Constant-time compare."""
    acc = accounts().get(user)
    if not acc:
        hmac.compare_digest(password, password)  # keep timing similar
        return None
    return acc[1] if hmac.compare_digest(acc[0], password) else None


def _sign(payload: str) -> str:
    return hmac.new(os.environ["SECRET_KEY"].encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_cookie(user: str, role: str) -> str:
    payload = f"{user}|{role}|{int(time.time()) + TTL_S}|{secrets.token_hex(4)}"
    return payload + "|" + _sign(payload)


def read_cookie(value: str | None) -> tuple[str, str] | None:
    if not value or not enabled():
        return None
    try:
        payload, sig = value.rsplit("|", 1)
        user, role, exp, _ = payload.split("|")
    except ValueError:
        return None
    if not hmac.compare_digest(sig, _sign(payload)) or int(exp) < time.time() or role not in ROLES:
        return None
    return user, role
