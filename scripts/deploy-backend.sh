#!/bin/bash
# ============================================
# Deploy TRAMOS Backend Fix ke VPS
# ============================================
# Jalankan di terminal laptop kamu:
#   bash scripts/deploy-backend.sh
# ============================================

set -e

VPS_HOST="202.83.120.98"
VPS_PORT="22028"
VPS_USER="ivander"
VPS_PASS="tetapsemicolon"
TRAMOS_DIR="/opt/tramos"

echo "=========================================="
echo "Deploy TRAMOS Backend Fix ke VPS"
echo "=========================================="

# Step 1: Buat patch files
echo "[1/4] Membuat patch..."
PATCH_FILES=(
    "app/routes/whatsapp.py"
    "app/services/chatbot/dialog_dispatcher.py"
    "app/services/chatbot/intent_classifier.py"
    "app/services/chatbot/conversation_coordinator.py"
    "app/services/chatbot/session_manager.py"
    "app/services/chatbot/smart_dialog_flow.py"
)

PATCH_DIR="/tmp/tramos-deploy-$$"
rm -rf "$PATCH_DIR"
mkdir -p "$PATCH_DIR/app/routes"
mkdir -p "$PATCH_DIR/app/services/chatbot"

for f in "${PATCH_FILES[@]}"; do
    mkdir -p "$(dirname "$PATCH_DIR/$f")"
    cp "/Users/vdr/Documents/TRAMOS/$f" "$PATCH_DIR/$f"
done

tar -czf /tmp/tramos-deploy.tar.gz -C "$PATCH_DIR" .
rm -rf "$PATCH_DIR"

# Step 2: Upload patch
echo "[2/4] Upload patch..."
expect << 'EOF'
set timeout 120
spawn scp -o StrictHostKeyChecking=accept-new -P 22028 /tmp/tramos-deploy.tar.gz ivander@202.83.120.98:/tmp/
expect {
    "password:" { send "tetapsemicolon\r"; exp_continue }
    eof
}
EOF

# Step 3: Extract dan replace
echo "[3/4] Extract dan replace files..."
expect << 'EOF'
set timeout 60
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 "cd /opt/tramos && tar -xzf /tmp/tramos-deploy.tar.gz && rm /tmp/tramos-deploy.tar.gz && echo FILES_REPLACED && ls -la app/routes/whatsapp.py app/services/chatbot/dialog_dispatcher.py"
expect {
    "password:" { send "tetapsemicolon\r"; exp_continue }
    eof
}
EOF

# Step 4: Rebuild container
echo "[4/4] Rebuild container backend..."
expect << 'EOF'
set timeout 600
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 "cd /opt/tramos && docker compose -f docker-compose.prod.yml build backend --no-cache 2>&1 | tail -5 && docker compose -f docker-compose.prod.yml up -d backend && echo RESTARTED && docker ps --format 'table {{.Names}}\t{{.Status}}' | grep tramos"
expect {
    "password:" { send "tetapsemicolon\r"; exp_continue }
    eof
}
EOF

echo ""
echo "=========================================="
echo "Deploy SELESAI!"
echo "Test WhatsApp sekarang!"
echo "=========================================="
