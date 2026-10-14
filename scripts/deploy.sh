#!/usr/bin/env bash
# One-command deploy (no CI, no secrets in repo). Runs the VPS-side script that lives outside the repo.
# Usage: DEPLOY_TARGET=user@host scripts/deploy.sh
set -euo pipefail
: "${DEPLOY_TARGET:?set DEPLOY_TARGET=user@host}"
ssh "$DEPLOY_TARGET" '/opt/ultrabyte/deploy.sh'
