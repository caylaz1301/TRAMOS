#!/bin/bash
# ============================================
# Reload Nginx config TRAMOS
# ============================================
# Jalankan di terminal laptop kamu:
#   bash scripts/reload-nginx.sh
# ============================================

set -e

VPS_HOST="202.83.120.98"
VPS_PORT="22028"
VPS_USER="ivander"
VPS_PASS="tetapsemangat"

echo "=========================================="
echo "Reload Nginx Config TRAMOS"
echo "=========================================="

# Test Nginx config syntax
echo "[1] Test Nginx config..."
expect << 'EOF'
set timeout 30
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 "sudo nginx -t 2>&1"
expect {
    "password:" {
        send "tetapsemangat\r"
        exp_continue
    }
    eof
}
EOF

# Reload Nginx
echo "[2] Reload Nginx..."
expect << 'EOF'
set timeout 30
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 "sudo nginx -s reload 2>&1; echo NGINX_RELOADED"
expect {
    "password:" {
        send "tetapsemangat\r"
        exp_continue
    }
    eof
}
EOF

echo ""
echo "=========================================="
echo "Nginx reload selesai!"
echo "Cek: https://helpdesk.tramos.systems/dashboard/"
echo "=========================================="
