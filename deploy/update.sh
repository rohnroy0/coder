#!/usr/bin/env bash
# Pull the latest code and redeploy. Usage: sudo bash deploy/update.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then echo "Run with sudo."; exit 1; fi
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Backing up database..."
BACKUP_DIR="$APP_DIR/backups"
mkdir -p "$BACKUP_DIR"
[ -f "$APP_DIR/backend/ai_code_classroom.db" ] && \
    cp "$APP_DIR/backend/ai_code_classroom.db" "$BACKUP_DIR/db-$(date +%Y%m%d-%H%M%S).sqlite"
chown -R coder:coder "$BACKUP_DIR"

echo "==> Pulling latest code..."
sudo -u coder git -C "$APP_DIR" pull --ff-only

echo "==> Updating dependencies and builds..."
sudo -u coder "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"
docker build -q -t python-runner "$APP_DIR/backend/docker/python_runner"
sudo -u coder bash -c "cd '$APP_DIR/frontend' && npm ci --silent && npm run build --silent"

echo "==> Restarting services..."
systemctl restart coder-backend
systemctl reload caddy

sleep 3
curl -fsS http://127.0.0.1:8100/health | grep -q '"ok"' && echo "==> Update complete, backend healthy." \
    || { echo "==> Backend unhealthy - check: journalctl -u coder-backend -n 50"; exit 1; }
