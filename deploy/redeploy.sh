#!/usr/bin/env bash
# ============================================================
#  Zebra Factory - redeploy after code changes
#  Run as root on the server:
#
#     bash redeploy.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

log() { echo -e "\n\033[1;32m==> $*\033[0m"; }

log "Pulling latest code..."
git -C "$APP_DIR" pull --ff-only

log "Updating dependencies..."
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
"$APP_DIR/.venv/bin/pip" install gunicorn

log "Restarting service..."
systemctl restart zebra-factory
sleep 2
systemctl status zebra-factory --no-pager | head -n 5

log "Done. Live at your configured domain(s)."
