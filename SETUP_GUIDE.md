# 🚀 TRAMOS - Complete Setup & Run Guide

Panduan lengkap untuk menjalankan TRAMOS AI Support System dari awal.

---

## ⚡ Quick Start (3 Terminal)

Buka **3 terminal** dan jalankan perintah berikut **secara bersamaan**:

### Terminal 1: Backend (Port 9999)
```bash
cd /Users/vdr/Documents/TRAMOS
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 9999
```

✅ Tunggu sampai muncul: `Application startup complete.`

---

### Terminal 2: Frontend (Port 3000)
```bash
cd /Users/vdr/Documents/TRAMOS/dashboard
npm run dev
```

✅ Tunggu sampai muncul: `Local: http://localhost:3000`

---

### Terminal 3: ngrok (Untuk WhatsApp Webhook & osTicket)
```bash
# Install ngrok jika belum
# brew install ngrok
# atau download dari https://ngrok.com/download

cd /Users/vdr/Documents/TRAMOS
ngrok start --config ngrok.yml
```

✅ Akan muncul URL seperti: `https://xxxx-xx-xxx-xxx-xx.ngrok-free.app`

---

## 📋 Step-by-Step Setup

### Step 1: Setup Database (PostgreSQL)
```bash
# Check if PostgreSQL running
psql --version

# Jika belum, install:
# brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb tramos_db

# Run migrations
python init_db.py
```

---

### Step 2: Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env dengan settings Anda
nano .env
```

**Minimal configuration diperlukan:**

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/tramos_db

# osTicket
OSTICKET_BASE_URL=http://your-osticket-domain.com
OSTICKET_API_KEY=your-api-key-from-osticket

# WhatsApp (optional, untuk send messages)
WHATSAPP_API_TOKEN=your-token
WHATSAPP_PHONE_ID=your-phone-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=tramos_webhook_token_change_me

# Webhook
WEBHOOK_VERIFY_TOKEN=tramos_webhook_token_change_me

# LLM / RAG
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
KB_RAG_ENABLED=true
```

### Step 2b: Setup Knowledge Base RAG

TRAMOS AI sekarang mendukung production-ready knowledge base dengan PostgreSQL RAG.
Knowledge base disimpan di folder `knowledge_base/`, lalu di-ingest ke tabel
`kb_documents` dan `kb_chunks`.

Pastikan `.env` memiliki konfigurasi berikut:

```env
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=1536
KB_RAG_ENABLED=true
KB_SOURCE_DIR=knowledge_base
KB_TOP_K=5
KB_MIN_SCORE=0.35
KB_PGVECTOR_REQUIRED=false
```

Jalankan migration dan ingestion:

```bash
cd /Users/vdr/Documents/TRAMOS
source venv/bin/activate
python scripts/database_migration_kb_rag.py
python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
python scripts/test_kb_retrieval.py
```

Jika PostgreSQL lokal belum memiliki pgvector, sistem tetap berjalan memakai
fallback cosine similarity dari `embedding_json`. Untuk production penuh,
install/enable pgvector di PostgreSQL agar kolom `embedding_vector` aktif.

---

### Step 3: Setup osTicket dengan ngrok

#### 3a. Hubungkan osTicket ke Webhook TRAMOS

1. **Jalankan ngrok:**
   ```bash
   cd /Users/vdr/Documents/TRAMOS
   ngrok start --config ngrok.yml
   ```
   
   Catat URL: `https://xxxx-xxxx.ngrok-free.app`

2. **Setup di osTicket:**
   - Buka: `http://your-osticket.com/admin`
   - Navigasi ke: **Settings → Email** 
   - Jika ingin auto-create ticket dari WhatsApp, setup POP3/IMAP atau gunakan API direct

3. **Alternative: Direct API Call dari WhatsApp**
   - Backend TRAMOS akan langsung POST ke osTicket API
   - Pastikan `OSTICKET_API_KEY` benar

---

### Step 4: Setup WhatsApp Webhook

#### 4a. Configure di Meta Business Platform

1. Buka: [Meta Business Platform](https://business.facebook.com)
2. Pilih **Akunmu → WhatsApp Business Account**
3. Navigasi ke: **Configuration → Webhooks**
4. **Webhook URL**: `https://ngrok-url-anda.ngrok-free.app/webhook/whatsapp`
5. **Verify Token**: `tramos_webhook_token_change_me` (dari `.env`)

#### 4b. Test Webhook

```bash
# Test subscribe
curl "http://localhost:9999/webhook/whatsapp?hub.mode=subscribe&hub.challenge=TEST&hub.verify_token=tramos_webhook_token_change_me"

# Atau via ngrok
curl "https://ngrok-url-anda.ngrok-free.app/webhook/whatsapp?hub.mode=subscribe&hub.challenge=TEST&hub.verify_token=tramos_webhook_token_change_me"
```

---

### Step 5: Verify Semua Service Berjalan

```bash
# Check Backend Health
curl http://localhost:9999/health

# Expected output:
# {"status":"healthy", ...}

# Check Knowledge Base RAG
curl http://localhost:9999/api/kb/health

# Check Database
python query_db.py
```

---

## 📊 Access Points

Setelah semua running:

| Service | URL | Purpose |
|---|---|---|
| **Frontend Dashboard** | http://localhost:3000 | Analytics & Management |
| **API Docs** | http://localhost:9999/api/docs | Swagger UI |
| **API ReDoc** | http://localhost:9999/api/redoc | ReDoc Documentation |
| **Webhook (Local)** | http://localhost:9999/webhook/whatsapp | WhatsApp messages |
| **Webhook (Public)** | https://ngrok-url.ngrok-free.app/webhook/whatsapp | WhatsApp production |

---

## 🔧 Troubleshooting

### ❌ Port 3000 sudah terpakai
```bash
# Cek port
lsof -i :3000

# Ganti port di dashboard/vite.config.js
# Ubah "port: 3000" ke "port: 3001"
```

### ❌ Port 9999 sudah terpakai
```bash
lsof -i :9999
kill -9 <PID>
```

### ❌ Database connection error
```bash
# Cek PostgreSQL
brew services list

# Start jika belum
brew services start postgresql@15

# Check connection
psql -U postgres -d tramos_db
```

### ❌ WhatsApp Webhook tidak terima message
```bash
# Pastikan:
1. ngrok URL di Meta Business Platform sudah update
2. WEBHOOK_VERIFY_TOKEN match di code & Meta
3. Cek ngrok log: http://localhost:4040

# Reset ngrok tunnel:
ngrok stop
ngrok start --config ngrok.yml
```

### ❌ Gemini atau RAG error (jika menggunakan AI/KB)
```bash
# Cek health backend
curl http://localhost:9999/health

# Cek status knowledge base
curl http://localhost:9999/api/kb/health

# Re-ingest knowledge base dari folder knowledge_base
python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
```

---

## 📝 Environment Variables Reference

```env
# ===== APP =====
DEBUG=true
APP_NAME=TRAMOS AI Support System
APP_VERSION=1.0.0

# ===== DATABASE =====
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/tramos_db

# ===== OSTICKET =====
OSTICKET_BASE_URL=http://localhost:81  # atau ngrok URL
OSTICKET_API_KEY=<get-from-osticket-admin>
OSTICKET_TICKETS_ENDPOINT=/api/tickets.json
DEFAULT_TICKET_IP=127.0.0.1
DEFAULT_TICKET_PRIORITY=normal

# ===== WHATSAPP =====
WHATSAPP_API_URL=https://graph.facebook.com/v19.0
WHATSAPP_API_TOKEN=<your-meta-token>
WHATSAPP_PHONE_ID=<your-phone-id>
WHATSAPP_MODE=sandbox  # atau production
WHATSAPP_WEBHOOK_VERIFY_TOKEN=tramos_webhook_token_change_me
WEBHOOK_VERIFY_TOKEN=tramos_webhook_token_change_me

# ===== AI/LLM =====
LLM_PROVIDER=gemini
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_PROJECT_ID=<optional>
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=1536
USE_LLM=true
AI_CONFIDENCE_THRESHOLD=0.7

# ===== KNOWLEDGE BASE / RAG =====
KB_RAG_ENABLED=true
KB_SOURCE_DIR=knowledge_base
KB_TOP_K=5
KB_MIN_SCORE=0.35
KB_PGVECTOR_REQUIRED=false

# ===== EMAIL (optional) =====
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-email>
SMTP_PASSWORD=<your-password>
SMTP_FROM_EMAIL=noreply@tramos.local
OPERATOR_EMAILS=admin@example.com,support@example.com

# ===== CORS =====
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 🚀 Production Deployment

### Backend (Gunicorn)
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:9999
```

### Frontend (Build)
```bash
cd dashboard
npm run build
# Output di: dashboard/dist/
```

### Reverse Proxy (nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://127.0.0.1:9999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}
```

---

## 📞 Getting Help

Check logs:
```bash
# Backend logs (di terminal where it's running)
# Frontend logs (di terminal where it's running)

# Database query log
tail -f /usr/local/var/log/postgresql.log

# ngrok logs
# http://localhost:4040
```

---

**Last Updated:** May 18, 2026
**Version:** 1.0.0
