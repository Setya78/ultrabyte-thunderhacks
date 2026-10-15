#!/usr/bin/env bash
# Demo-path smoke test. Usage: scripts/smoke.sh [base_url]  (default: live URL)
set -euo pipefail
BASE="${1:-https://ultrabyte.denysetya.com}"
fail() { echo "FAIL: $*"; exit 1; }
echo "1/5 health";  curl -fsS "$BASE/health" | grep -q '"db":"ok"'              || fail "/health db not ok"
echo "2/5 queue";   PAGE=$(curl -fsS "$BASE/"); echo "$PAGE" | grep -qi 'synthetic data' || fail "/ missing synthetic badge"
echo "3/5 reset";   curl -fsS -X POST "$BASE/reset" | grep -q '"reset":"ok"'     || fail "/reset failed"
echo "4/5 judge";   LOC=$(curl -sS -o /dev/null -w '%{redirect_url}' -X POST "$BASE/enter" -d player_id= -d new_age=19-29 -d "new_income=<20k" -d "new_city=Sault Ste. Marie" -d new_occupation=student -d type=deposit -d amount=9500 -d date=2026-10-10 -d time=14:00 -d method=cash_cage -d "city=Sault Ste. Marie" -d wagered=0)
                    echo "$LOC" | grep -q 'pid=M-001' || fail "/enter did not create M-001"
                    curl -fsS "$BASE/player/M-001" | grep -qi 'manual entry' || fail "M-001 page missing judge row"
echo "5/5 reset";   curl -fsS -X POST "$BASE/reset" | grep -q '"reset":"ok"'     || fail "/reset (2) failed"
                    [ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/player/M-001")" = "404" ] || fail "M-001 survived reset"
echo "6/6 rules";   curl -fsS "$BASE/rules" | grep -q "version [0-9]" || fail "/rules missing version"
echo "SMOKE OK ($BASE)"
