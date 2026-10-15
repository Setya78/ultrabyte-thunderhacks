#!/usr/bin/env bash
# Demo-path smoke test. Usage: SMOKE_USER=investigator SMOKE_PASS=... scripts/smoke.sh [base_url]
# Without SMOKE_USER/SMOKE_PASS only the public checks run (health, sign-in page, redirect).
set -euo pipefail
BASE="${1:-https://ultrabyte.denysetya.com}"
J=$(mktemp); trap 'rm -f "$J"' EXIT
fail() { echo "FAIL: $*"; exit 1; }
echo "1/8 health";   curl -fsS "$BASE/health" | grep -q '"db":"ok"' || fail "/health db not ok"
echo "2/8 sign-in";  curl -fsS "$BASE/login" | grep -qi 'sign' || fail "/login missing"
echo "3/8 guard";    [ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/")" = "303" ] || fail "/ reachable without sign-in"
if [ -z "${SMOKE_USER:-}" ] || [ -z "${SMOKE_PASS:-}" ]; then echo "SMOKE OK (public checks only; set SMOKE_USER/SMOKE_PASS for the full path)"; exit 0; fi
echo "4/8 login";    [ "$(curl -s -c "$J" -o /dev/null -w '%{http_code}' -X POST "$BASE/login" -d "username=$SMOKE_USER" -d "password=$SMOKE_PASS")" = "303" ] || fail "sign-in rejected"
                     curl -fsS -b "$J" "$BASE/" | grep -qi 'synthetic data' || fail "/ missing synthetic badge after sign-in"
echo "5/8 reset";    curl -fsS -b "$J" -X POST "$BASE/reset" | grep -q '"reset":"ok"' || fail "/reset failed"
echo "6/8 entry";    LOC=$(curl -sS -b "$J" -o /dev/null -w '%{redirect_url}' -X POST "$BASE/enter" -d player_id= -d new_age=19-29 -d "new_income=<20k" -d "new_city=Sault Ste. Marie" -d new_occupation=student -d type=deposit -d amount=9500 -d date=2026-10-10 -d time=14:00 -d method=cash_cage -d "city=Sault Ste. Marie" -d wagered=0)
                     echo "$LOC" | grep -q 'pid=M-001' || fail "/enter did not create M-001"
                     curl -fsS -b "$J" "$BASE/player/M-001" | grep -qi 'manual entry' || fail "M-001 page missing manual entry row"
echo "7/8 reset";    curl -fsS -b "$J" -X POST "$BASE/reset" | grep -q '"reset":"ok"' || fail "/reset (2) failed"
                     [ "$(curl -s -b "$J" -o /dev/null -w '%{http_code}' "$BASE/player/M-001")" = "404" ] || fail "M-001 survived reset"
echo "8/8 rules";    curl -fsS -b "$J" "$BASE/rules" | grep -q "version [0-9]" || fail "/rules missing version"
echo "SMOKE OK ($BASE)"
