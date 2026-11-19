#!/usr/bin/env bash
# One-shot production setup for Coder on a fresh Ubuntu 22.04/24.04 server
# (tested target: Oracle Cloud Always Free ARM VM).
#
# Usage:
#   sudo bash deploy/setup-server.sh yourname.duckdns.org
#
# Run it from the repository root (clone the repo to /opt/coder first - see
# deploy/DEPLOY.md). Safe to re-run; every step is idempotent.
set -euo pipefail

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
    echo "Usage: sudo bash deploy/setup-server.sh <your-domain>"
    echo "Example: sudo bash deploy/setup-server.sh coder-demo.duckdns.org"
    exit 1
fi
if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo."
    exit 1
fi

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "==> App directory: $APP_DIR"
echo "==> Domain:        $DOMAIN"

# ─── 1. Base packages ─────────────────────────────────────────────────────────
echo "==> Installing base packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -yq python3-venv python3-pip git ca-certificates curl gnupg \
    debian-keyring debian-archive-keyring apt-transport-https

# ─── 2. Docker (code-execution sandbox) ───────────────────────────────────────
if ! command -v docker >/dev/null 2>&1; then
    echo "==> Installing Docker..."
    curl -fsSL https://get.docker.com | sh
else
    echo "==> Docker already installed."
fi

# ─── 3. Caddy (HTTPS reverse proxy) ───────────────────────────────────────────
if ! command -v caddy >/dev/null 2>&1; then
    echo "==> Installing Caddy..."
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
        | gpg --dearmor --yes -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
        > /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -q && apt-get install -yq caddy
else
    echo "==> Caddy already installed."
fi

# ─── 4. Node.js (to build the frontend) ───────────────────────────────────────
if ! command -v node >/dev/null 2>&1; then
    echo "==> Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -yq nodejs
else
    echo "==> Node.js already installed ($(node --version))."
fi

# ─── 5. Service user ──────────────────────────────────────────────────────────
if ! id coder >/dev/null 2>&1; then
    echo "==> Creating 'coder' service user..."
    useradd --system --create-home --shell /usr/sbin/nologin coder
fi
usermod -aG docker coder
chown -R coder:coder "$APP_DIR"

# ─── 6. Python environment ────────────────────────────────────────────────────
echo "==> Setting up Python virtualenv..."
sudo -u coder python3 -m venv "$APP_DIR/venv"
sudo -u coder "$APP_DIR/venv/bin/pip" install -q --upgrade pip
sudo -u coder "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/backend/requirements.txt"

# ─── 7. Production .env (secrets generated, AI key left for you) ─────────────
ENV_FILE="$APP_DIR/backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "==> Creating backend/.env with generated secrets..."
    cp "$APP_DIR/deploy/env.production.example" "$ENV_FILE"
    SECRET=$("$APP_DIR/venv/bin/python" -c "import secrets; print(secrets.token_urlsafe(48))")
    TCODE=$("$APP_DIR/venv/bin/python" -c "import secrets; print(secrets.token_urlsafe(9))")
    sed -i "0,/__GENERATE__/s//$SECRET/" "$ENV_FILE"
    sed -i "0,/__GENERATE__/s//$TCODE/" "$ENV_FILE"
    sed -i "s/__DOMAIN__/$DOMAIN/" "$ENV_FILE"
    chown coder:coder "$ENV_FILE"
    chmod 600 "$ENV_FILE"
else
    echo "==> backend/.env already exists - leaving it untouched."
fi

# ─── 8. Sandbox image + frontend build ────────────────────────────────────────
echo "==> Building python-runner sandbox image..."
docker build -q -t python-runner "$APP_DIR/backend/docker/python_runner"

echo "==> Building frontend..."
sudo -u coder bash -c "cd '$APP_DIR/frontend' && npm ci --silent && npm run build --silent"

# ─── 9. systemd service ───────────────────────────────────────────────────────
echo "==> Installing systemd service..."
sed "s|__APP_DIR__|$APP_DIR|g" "$APP_DIR/deploy/coder-backend.service" \
    > /etc/systemd/system/coder-backend.service
systemctl daemon-reload
systemctl enable --now coder-backend
systemctl restart coder-backend

# ─── 10. Caddy config ─────────────────────────────────────────────────────────
echo "==> Configuring Caddy for $DOMAIN..."
sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__APP_DIR__|$APP_DIR|g" \
    "$APP_DIR/deploy/Caddyfile" > /etc/caddy/Caddyfile
systemctl enable --now caddy
systemctl reload caddy

# ─── 11. Host firewall (Oracle Ubuntu images block 80/443 by default) ────────
echo "==> Opening ports 80/443 in the host firewall..."
if iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null; then
    echo "    already open"
else
    iptables -I INPUT -p tcp --dport 80 -j ACCEPT
    iptables -I INPUT -p tcp --dport 443 -j ACCEPT
    command -v netfilter-persistent >/dev/null 2>&1 && netfilter-persistent save || true
fi

# ─── 12. Smoke test ───────────────────────────────────────────────────────────
echo "==> Smoke test..."
sleep 3
if curl -fsS http://127.0.0.1:8100/health | grep -q '"ok"'; then
    echo "    backend: OK"
else
    echo "    backend: FAILED - check: journalctl -u coder-backend -n 50"
    exit 1
fi

echo ""
echo "============================================================"
echo " Setup complete."
echo ""
if ! grep -q '^AI_API_KEY=.\+' "$ENV_FILE"; then
    echo " !! AI_API_KEY is empty. AI features are disabled until you:"
    echo "    1. sudo nano $ENV_FILE   (paste your Groq key)"
    echo "    2. sudo systemctl restart coder-backend"
    echo ""
fi
echo " Teacher signup code (give this only to teachers):"
grep '^TEACHER_SIGNUP_CODE=' "$ENV_FILE" | sed 's/^/    /'
echo ""
echo " App URL: https://$DOMAIN"
echo " (Also open ports 80+443 in the Oracle Cloud security list - see DEPLOY.md)"
echo "============================================================"
