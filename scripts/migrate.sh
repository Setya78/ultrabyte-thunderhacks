#!/usr/bin/env bash
# Gate pattern (Infra Runbook R3): dry-run in a rolled-back transaction -> apply -> verify.
# Usage: PSQL="docker exec -i ultrabyte-postgres psql -U ultrabyte_app -d thx_ultrabyte" scripts/migrate.sh db/migrations/001_init.sql [apply]
set -euo pipefail
PSQL="${PSQL:?set PSQL to a psql command}"
FILE="${1:?migration file}"
echo "== dry-run (BEGIN ... ROLLBACK)"
{ echo "BEGIN;"; cat "$FILE"; echo "ROLLBACK;"; } | $PSQL -v ON_ERROR_STOP=1 -q
echo "dry-run OK"
if [ "${2:-}" = "apply" ]; then
  echo "== apply (single transaction)"
  $PSQL -v ON_ERROR_STOP=1 --single-transaction -q < "$FILE"
  echo "== verify"
  $PSQL -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1;"
fi
