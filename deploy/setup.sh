#!/usr/bin/env bash
# ============================================================
#  Zebra Factory - one-time Hetzner setup
#  Run as root on a fresh Ubuntu 24.04 server:
#
#     bash setup.sh
#
#  It is safe to re-run this script; it will update/repair.
# ============================================================
set -euo pipefail

# --- Load config -------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/config.env"

PRIMARY_DOMAIN="$(echo "$DOMAINS" | awk '{print $1}')"

log() { echo -e "\n\033[1;32m==> $*\033[0m"; }
err() { echo -e "\n\033[1;31mERROR: $*\033[0m" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || err "Please run as root (e.g. 'sudo bash setup.sh')."

# --- 1. System dependencies -------------------------------------
log "Installing system packages (Python, MySQL build deps, Nginx)..."
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y python3-venv python3-pip git nginx \
  build-essential pkg-config default-libmysqlclient-dev \
  certbot python3-certbot-nginx ufw

# --- 2. Clone or update the repo --------------------------------
if [ -d "$APP_DIR/.git" ]; then
  log "Repo already present - pulling latest..."
  git -C "$APP_DIR" pull --ff-only
else
  log "Cloning repo into $APP_DIR..."
  git clone "$REPO_URL" "$APP_DIR"
fi

# --- 3. Python virtualenv + dependencies ------------------------
log "Setting up Python virtualenv and installing dependencies..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
"$APP_DIR/.venv/bin/pip" install gunicorn

# --- 4. .env file -----------------------------------------------
if [ ! -f "$APP_DIR/.env" ]; then
  log "Creating .env template - YOU MUST EDIT IT before the app will work."
  cp "$SCRIPT_DIR/env.example" "$APP_DIR/.env"
  sed -i "s|__PRIMARY_DOMAIN__|$PRIMARY_DOMAIN|g" "$APP_DIR/.env"
  NEEDS_ENV=1
else
  log ".env already exists - leaving it untouched."
  NEEDS_ENV=0
fi

# --- 5. systemd service -----------------------------------------
log "Installing systemd service..."
cat > /etc/systemd/system/zebra-factory.service <<EOF
[Unit]
Description=Zebra Factory (Flask-SocketIO)
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
ExecStart=$APP_DIR/.venv/bin/gunicorn -k eventlet -w 1 -b 127.0.0.1:$APP_PORT run:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable zebra-factory
systemctl restart zebra-factory

# --- 6. Nginx reverse proxy -------------------------------------
log "Configuring Nginx for: $DOMAINS"
cat > /etc/nginx/sites-available/zebra-factory <<EOF
server {
    listen 80;
    server_name $DOMAINS;

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:$APP_PORT/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

ln -sf /etc/nginx/sites-available/zebra-factory /etc/nginx/sites-enabled/zebra-factory
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# --- 7. Firewall ------------------------------------------------
log "Configuring firewall (SSH + HTTP/HTTPS)..."
ufw allow OpenSSH >/dev/null 2>&1 || true
ufw allow 'Nginx Full' >/dev/null 2>&1 || true
ufw --force enable >/dev/null 2>&1 || true

# --- 8. HTTPS via Let's Encrypt ---------------------------------
log "Requesting HTTPS certificates for: $DOMAINS"
CERT_DOMAIN_FLAGS=""
for d in $DOMAINS; do CERT_DOMAIN_FLAGS="$CERT_DOMAIN_FLAGS -d $d"; done
if certbot --nginx $CERT_DOMAIN_FLAGS --non-interactive --agree-tos \
     -m "$CERTBOT_EMAIL" --redirect; then
  log "HTTPS enabled."
else
  echo "WARNING: certbot failed. Make sure your DNS A records point to this"
  echo "server, then re-run:  certbot --nginx $CERT_DOMAIN_FLAGS"
fi

# --- Done -------------------------------------------------------
echo
log "Setup complete!"
echo "   App URL:   https://$PRIMARY_DOMAIN"
echo "   Service:   systemctl status zebra-factory"
echo "   Logs:      journalctl -u zebra-factory -f"
echo
if [ "$NEEDS_ENV" -eq 1 ]; then
  echo -e "\033[1;33mIMPORTANT:\033[0m You still need to fill in credentials:"
  echo "   nano $APP_DIR/.env"
  echo "   systemctl restart zebra-factory"
  echo
  echo "Also: allow this server's IP in your AWS RDS security group (port 3306)."
fi
