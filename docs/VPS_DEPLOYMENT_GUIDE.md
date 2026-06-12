# TRAMOS VPS Deployment Guide

Panduan ini menyiapkan TRAMOS AI, Dashboard, PostgreSQL + pgvector, Redis, Knowledge Base RAG, WhatsApp webhook, dan koneksi osTicket di VPS client.

## 1. Target Arsitektur

Rekomendasi production:

- `api.domain-client.com` -> Nginx -> FastAPI TRAMOS di `127.0.0.1:9999`
- `dashboard.domain-client.com` -> Nginx -> static React dashboard
- `support.domain-client.com` atau `/osTicket` -> osTicket/XAMPP/Apache/PHP
- PostgreSQL + pgvector -> Docker container, hanya bind ke localhost
- Redis -> Docker container, hanya bind ke localhost
- Ollama embedding -> disarankan jalan di VPS client, bukan memakai server kantor/development

Catatan:

- Jangan pakai ngrok di production.
- Jangan expose PostgreSQL, Redis, Ollama, atau port backend langsung ke internet.
- Meta WhatsApp webhook wajib HTTPS.

## 2. Persiapan VPS

Minimal yang disarankan:

- Ubuntu 22.04/24.04 LTS
- 2 vCPU, 4 GB RAM minimum untuk demo
- 4 vCPU, 8 GB RAM lebih aman jika menjalankan Ollama embedding di VPS
- Domain/subdomain sudah mengarah ke IP VPS

Install dependency dasar:

```bash
sudo apt update
sudo apt install -y git curl nginx certbot python3-certbot-nginx
```

Install Docker dan Docker Compose plugin sesuai standar distro/VPS client.

## 3. Upload Project

Contoh folder production:

```bash
sudo mkdir -p /opt/tramos
sudo chown -R $USER:$USER /opt/tramos
cd /opt/tramos
git clone <repo-tramos-anda> .
```

Jika tidak pakai git, upload folder project dengan `rsync`/SFTP, tapi jangan upload:

- `.env`
- `venv/`
- `dashboard/node_modules/`
- file token pribadi

## 4. Siapkan Environment Production

Copy template:

```bash
cp deploy/env.production.example deploy/env.production
nano deploy/env.production
```

Yang wajib diganti:

```env
TRAMOS_POSTGRES_PASSWORD=isi-password-kuat
DATABASE_URL=postgresql://tramos:isi-password-kuat@postgres:5432/tramos_db

CORS_ORIGINS=https://dashboard.domain-client.com

WHATSAPP_API_TOKEN=token-production-meta
WHATSAPP_PHONE_ID=phone-number-id-production
WHATSAPP_WEBHOOK_VERIFY_TOKEN=random-token-kuat

OSTICKET_BASE_URL=https://support.domain-client.com/osTicket/api
OSTICKET_API_KEY=api-key-osticket

ANTHROPIC_API_KEY=api-key-claude-atau-bluepack
JWT_SECRET_KEY=random-minimal-64-karakter
```

Jika Ollama embedding jalan sebagai container di VPS client, gunakan:

```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:4b
EMBEDDING_DIMENSIONS=2560
EMBEDDING_OLLAMA_URL=http://ollama:11434
```

Jika memakai managed embedding Gemini:

```env
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=1536
GEMINI_API_KEY=isi-api-key-gemini
```

Hindari memakai server Ollama kantor untuk production client kecuali sudah ada izin resmi, koneksi aman/VPN, dan persetujuan bahwa query client boleh diproses di server tersebut.

## 5. Start Database dan Backend

Dari root project:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  up -d --build
```

Pull model embedding jika memakai Ollama lokal di VPS:

```bash
docker exec -it tramos-ollama ollama pull qwen3-embedding:4b
```

Cek status:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  ps
docker logs -f tramos-backend
```

Jalankan ingest KB setelah backend/database sehat:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  exec backend \
  python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
```

Cek preflight:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  exec backend \
  python scripts/vps_preflight_check.py
```

Jika ingin cek LLM dan embedding juga:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  exec backend \
  python scripts/vps_preflight_check.py --check-llm --check-embedding
```

## 6. Build Dashboard

Di VPS:

```bash
cd /opt/tramos/dashboard
npm ci
npm run build
```

Copy hasil build:

```bash
sudo mkdir -p /var/www/tramos-dashboard
sudo rsync -a dist/ /var/www/tramos-dashboard/dist/
sudo chown -R www-data:www-data /var/www/tramos-dashboard
```

Dashboard memakai API relative `/api`, jadi Nginx dashboard akan proxy `/api/` ke backend.

## 7. Konfigurasi Nginx

Copy template:

```bash
sudo cp /opt/tramos/deploy/nginx/tramos-api.conf /etc/nginx/sites-available/tramos-api.conf
sudo cp /opt/tramos/deploy/nginx/tramos-dashboard.conf /etc/nginx/sites-available/tramos-dashboard.conf
```

Edit domain:

```bash
sudo nano /etc/nginx/sites-available/tramos-api.conf
sudo nano /etc/nginx/sites-available/tramos-dashboard.conf
```

Ganti:

- `api.example.com` -> domain API client
- `dashboard.example.com` -> domain dashboard client

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/tramos-api.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/tramos-dashboard.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Pasang SSL HTTPS

```bash
sudo certbot --nginx -d api.domain-client.com
sudo certbot --nginx -d dashboard.domain-client.com
```

Untuk osTicket:

```bash
sudo certbot --nginx -d support.domain-client.com
```

## 9. Konfigurasi osTicket

Di osTicket admin:

1. Aktifkan API.
2. Buat API key.
3. Whitelist IP server backend. Jika TRAMOS dan osTicket di VPS yang sama, whitelist `127.0.0.1` dan IP private/public sesuai cara akses.
4. Pastikan endpoint ini valid:

```text
https://support.domain-client.com/osTicket/api/tickets.json
```

Di `.env.production`, base URL cukup:

```env
OSTICKET_BASE_URL=https://support.domain-client.com/osTicket/api
```

Kode TRAMOS otomatis menambahkan `/tickets.json`.

## 10. Konfigurasi Meta WhatsApp

Di Meta Developer:

Callback URL:

```text
https://api.domain-client.com/webhook/whatsapp
```

Verify token:

```text
isi sama dengan WHATSAPP_WEBHOOK_VERIFY_TOKEN
```

Subscribe field:

- `messages`

Tes dari terminal:

```bash
curl "https://api.domain-client.com/webhook/whatsapp?hub.mode=subscribe&hub.challenge=TEST&hub.verify_token=TOKEN_ANDA"
```

Harus balik:

```text
TEST
```

## 11. Test Production

Health:

```bash
curl https://api.domain-client.com/health
curl https://api.domain-client.com/api/kb/health
```

Test KB:

```bash
docker compose --env-file deploy/env.production -f deploy/docker-compose.prod.yml exec backend \
  python scripts/test_kb_retrieval.py "gps tidak update di jalan" --audience driver
```

Test dialog flow tanpa spam WhatsApp:

```bash
docker compose --env-file deploy/env.production -f deploy/docker-compose.prod.yml exec backend \
  python scripts/whatsapp_dialog_50_test.py --quick10 --report docs/production_dialog_10_report.md
```

Test WhatsApp asli:

1. Kirim `halo` dari nomor user yang sudah boleh test ke nomor WhatsApp business.
2. Pantau log:

```bash
docker logs -f tramos-backend
```

## 12. Backup

PostgreSQL:

```bash
docker exec tramos-postgres pg_dump -U tramos tramos_db > tramos_db_$(date +%F).sql
```

osTicket:

- Backup database MySQL/MariaDB osTicket.
- Backup folder attachment osTicket.
- Backup file konfigurasi osTicket.

## 13. Update Project Setelah Ada Perubahan

```bash
cd /opt/tramos
git pull
docker compose --env-file deploy/env.production -f deploy/docker-compose.prod.yml up -d --build
docker compose --env-file deploy/env.production -f deploy/docker-compose.prod.yml exec backend \
  python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
```

Jika dashboard berubah:

```bash
cd /opt/tramos/dashboard
npm ci
npm run build
sudo rsync -a dist/ /var/www/tramos-dashboard/dist/
sudo systemctl reload nginx
```

## 14. Troubleshooting Cepat

Webhook Meta gagal verify:

- Cek HTTPS aktif.
- Cek callback path `/webhook/whatsapp`.
- Cek verify token sama persis.
- Cek Nginx proxy ke `127.0.0.1:9999`.

Bot tidak membalas:

- Cek `docker logs -f tramos-backend`.
- Cek WhatsApp token dan phone ID.
- Pastikan user mengirim pesan dulu agar window 24 jam Meta terbuka.

Ticket gagal dibuat:

- Cek `OSTICKET_BASE_URL`.
- Cek API key osTicket.
- Cek whitelist IP di osTicket.
- Cek `https://support.domain-client.com/osTicket/api/tickets.json`.

KB tidak muncul:

- Jalankan migration dan ingest ulang.
- Cek embedding Ollama reachable.
- Cek `/api/kb/health`.

Embedding 2560 dan pgvector:

- `qwen3-embedding:4b` punya dimensi 2560.
- pgvector column bisa menyimpan vector 2560.
- Index `ivfflat` pgvector dibatasi 2000 dimensi, jadi untuk 2560 sistem memakai exact vector scan/fallback. Untuk ukuran KB TRAMOS saat ini ini aman.
