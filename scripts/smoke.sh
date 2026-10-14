#!/usr/bin/env bash
# Demo-path smoke test. Usage: scripts/smoke.sh [base_url]  (default: live URL)
set -euo pipefail
BASE="${1:-https://ultrabyte.denysetya.com}"
fail() { echo "FAIL: $*"; exit 1; }
echo "1/3 health";  curl -fsS "$BASE/health" | grep -q '"db":"ok"'           || fail "/health db not ok"
echo "2/3 queue";   curl -fsS "$BASE/" | grep -q 'SYNTHETIC DATA'             || fail "/ missing synthetic banner"
echo "3/3 reset";   curl -fsS -X POST "$BASE/reset" | grep -q '"reset":"ok"'  || fail "/reset failed"
echo "SMOKE OK ($BASE)"
