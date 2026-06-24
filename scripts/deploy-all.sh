#!/bin/bash
# FULL Deploy TRAMOS - Backend + Dashboard
# Jalankan: cd ~/Documents/TRAMOS && bash scripts/deploy-all.sh

echo "=========================================="
echo "FULL Deploy TRAMOS"
echo "=========================================="

# Patch backend files
echo "[Patch] Buat patch backend..."
rm -rf /tmp/tfix
mkdir -p /tmp/tfix/app/routes
mkdir -p /tmp/tfix/app/services/chatbot
cp $HOME/Documents/TRAMOS/app/routes/whatsapp.py /tmp/tfix/app/routes/
cp $HOME/Documents/TRAMOS/app/services/chatbot/dialog_dispatcher.py /tmp/tfix/app/services/chatbot/
cp $HOME/Documents/TRAMOS/app/services/chatbot/intent_classifier.py /tmp/tfix/app/services/chatbot/
cp $HOME/Documents/TRAMOS/app/services/chatbot/conversation_coordinator.py /tmp/tfix/app/services/chatbot/
cp $HOME/Documents/TRAMOS/app/services/chatbot/session_manager.py /tmp/tfix/app/services/chatbot/
cp $HOME/Documents/TRAMOS/app/services/chatbot/smart_dialog_flow.py /tmp/tfix/app/services/chatbot/
tar -czf /tmp/tramos-fix.tar.gz -C /tmp/tfix .
rm -rf /tmp/tfix
echo "Patch siap ($(du -sh /tmp/tramos-fix.tar.gz | cut -f1))"

# Build dashboard
echo "[Build] Build dashboard..."
bash -c "cd $HOME/Documents/TRAMOS/dashboard && npm run build > /dev/null 2>&1"
tar -czf /tmp/tramos-dash.tar.gz -C $HOME/Documents/TRAMOS/dashboard/dist .
echo "Dashboard siap ($(du -sh /tmp/tramos-dash.tar.gz | cut -f1))"

# Upload backend
echo "[1/4] Upload backend fix..."
expect -c "
set timeout 120
spawn scp -o StrictHostKeyChecking=accept-new -P 22028 /tmp/tramos-fix.tar.gz ivander@202.83.120.98:/tmp/
expect {
    password: { send \"tetapsemicolon\r\"; exp_continue }
    eof
}
"

# Upload dashboard
echo "[2/4] Upload dashboard..."
expect -c "
set timeout 120
spawn scp -o StrictHostKeyChecking=accept-new -P 22028 /tmp/tramos-dash.tar.gz ivander@202.83.120.98:/tmp/
expect {
    password: { send \"tetapsemicolon\r\"; exp_continue }
    eof
}
"

# Extract di VPS
echo "[3/4] Extract di VPS..."
expect -c "
set timeout 60
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 {cd /opt/tramos && tar -xzf /tmp/tramos-fix.tar.gz && rm /tmp/tramos-fix.tar.gz && tar -xzf /tmp/tramos-dash.tar.gz && rm /tmp/tramos-dash.tar.gz && echo FILES_OK && echo Backend: \$(ls app/routes/whatsapp.py) && echo Dashboard: \$(du -sh dashboard/dist/ | cut -f1)}
expect {
    password: { send \"tetapsemicolon\r\"; exp_continue }
    eof
}
"

# Rebuild container
echo "[4/4] Rebuild container backend..."
expect -c "
set timeout 600
spawn ssh -o StrictHostKeyChecking=accept-new -p 22028 ivander@202.83.120.98 {cd /opt/tramos && docker compose -f docker-compose.prod.yml build backend --no-cache 2>&1 | tail -3 && docker compose -f docker-compose.prod.yml up -d backend && echo RESTARTED}
expect {
    password: { send \"tetapsemicolon\r\"; exp_continue }
    eof
}
"

echo ""
echo "=========================================="
echo "Deploy SELESAI!"
echo "Test WhatsApp sekarang!"
echo "=========================================="
