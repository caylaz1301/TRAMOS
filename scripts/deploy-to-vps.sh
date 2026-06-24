#!/usr/bin/env bash
# ============================================================
# TRAMOS — Deploy Backend ke VPS
# ============================================================
# Cara pakai:
#   cd ~/Documents/TRAMOS
#   bash scripts/deploy-to-vps.sh
#
# Script ini akan:
#   1. Upload kode terbaru ke VPS (tanpa menghapus file apapun di VPS)
#   2. Rebuild container backend
#   3. Verifikasi health check
# ============================================================

set -euo pipefail

# ===== KONFIGURASI =====
VPS_HOST="202.83.120.98"
VPS_PORT="22028"
VPS_USER="ivander"
VPS_PASS="tetapsemangat"
REMOTE_DIR="/opt/tramos"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Compose files
COMPOSE_CMD="docker compose \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  -f deploy/docker-compose.osticket.yml \
  -f deploy/docker-compose.dashboard-port.yml \
  --env-file deploy/env.production \
  --env-file deploy/env.osticket.production"

SSH_OPTS="-o ConnectTimeout=30 -o StrictHostKeyChecking=accept-new -p ${VPS_PORT}"

# ===== WARNA =====
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       TRAMOS — Deploy ke VPS             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# ===== STEP 1: Test SSH =====
echo -e "${YELLOW}[1/4] Testing SSH connection...${NC}"
if ! sshpass -p "${VPS_PASS}" ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST} "echo OK" > /dev/null 2>&1; then
    echo -e "${RED}❌ SSH gagal. Cek koneksi/firewall/password.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH connected${NC}"

# ===== STEP 2: Upload kode =====
echo ""
echo -e "${YELLOW}[2/4] Uploading kode ke VPS...${NC}"
sshpass -p "${VPS_PASS}" rsync -avz \
  --exclude='venv' --exclude='node_modules' --exclude='.git' \
  --exclude='__pycache__' --exclude='dashboard/dist' --exclude='dashboard/node_modules' \
  --exclude='.DS_Store' --exclude='*.pyc' --exclude='.pytest_cache' \
  --exclude='.deploy' --exclude='deploy/env.production' --exclude='deploy/env.osticket.production' \
  --exclude='loginpage.jpg' --exclude='Copy of Form4-Implementation.docx' \
  -e "ssh ${SSH_OPTS}" \
  "${LOCAL_DIR}/" "${VPS_USER}@${VPS_HOST}:${REMOTE_DIR}/"
echo -e "${GREEN}✅ Upload selesai${NC}"

# ===== STEP 3: Rebuild & restart backend =====
echo ""
echo -e "${YELLOW}[3/4] Rebuilding backend container...${NC}"
sshpass -p "${VPS_PASS}" ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST} \
  "cd ${REMOTE_DIR} && ${COMPOSE_CMD} up -d --build backend 2>&1"
echo -e "${GREEN}✅ Backend rebuilt & started${NC}"

# ===== STEP 4: Verifikasi =====
echo ""
echo -e "${YELLOW}[4/4] Verifikasi health (tunggu 10 detik)...${NC}"
sleep 10
HEALTH=$(sshpass -p "${VPS_PASS}" ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST} \
  "curl -s http://localhost:9999/health 2>/dev/null" || echo '{"status":"error"}')

STATUS=$(echo "${HEALTH}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")

if [ "${STATUS}" = "healthy" ]; then
    echo -e "${GREEN}✅ Backend HEALTHY — Deploy berhasil!${NC}"
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        ✅ DEPLOY SUKSES                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}⚠️  Health check gagal. Cek logs:${NC}"
    echo -e "${YELLOW}  sshpass -p '${VPS_PASS}' ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST} 'docker logs tramos-backend --tail 30'${NC}"
    exit 1
fi

echo ""
echo "Container status:"
sshpass -p "${VPS_PASS}" ssh ${SSH_OPTS} ${VPS_USER}@${VPS_HOST} \
  "docker ps --format 'table {{.Names}}\t{{.Status}}'"
echo ""
