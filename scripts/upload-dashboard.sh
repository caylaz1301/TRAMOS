#!/bin/bash
# ============================================
# Upload TRAMOS Dashboard to VPS
# ============================================
# Jalankan di terminal laptop kamu:
#   bash scripts/upload-dashboard.sh
# ============================================

set -e

DASHBOARD_DIR="/Users/vdr/Documents/TRAMOS/dashboard/dist"
VPS_HOST="202.83.120.98"
VPS_PORT="22028"
VPS_USER="ivander"
VPS_PASS="tetapsemicolon"

echo "=========================================="
echo "Upload Dashboard TRAMOS ke VPS"
echo "=========================================="

# Step 1: Buat archive
echo "[1/3] Membuat archive dashboard..."
tar -czf /tmp/tramos-dashboard-upload.tar.gz -C "$DASHBOARD_DIR" .

# Step 2: Upload
echo "[2/3] Upload ke VPS..."
expect << 'EOF'
set timeout 120
spawn scp -o StrictHostKeyChecking=accept-new -P 22028 /tmp/tramos-dashboard-upload.tar.gz ivander@202.83.120.98:/tmp/
expect {
    "password:" {
        send "tetapsemicolon\r"
        exp_continue
    }
    eof
}
EOF

# Step 3: Extract di VPS
echo "[3/3] Extract di VPS..."
expect << 'EOF'
set timeout 60
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 "cd /opt/tramos && tar -xzf /tmp/tramos-dashboard-upload.tar.gz && rm /tmp/tramos-dashboard-upload.tar.gz && echo 'DONE' && du -sh dashboard/dist/"
expect {
    "password:" {
        send "tetapsemicolon\r"
        exp_continue
    }
    eof
}
EOF

echo ""
echo "=========================================="
echo "Dashboard uploaded! Cek:"
echo "https://helpdesk.tramos.systems/dashboard/"
echo "=========================================="
