# Checklist Deploy TRAMOS ke VPS Client

Dokumen ini khusus untuk skenario: aplikasi TRAMOS dan osTicket akan dipasang di VPS client skripsi, sedangkan server Ollama kantor Jababeka hanya pernah dipakai untuk development/embedding percobaan.

## Keputusan Penting

Jangan jadikan server Ollama kantor sebagai dependency production client, kecuali ada izin resmi dari kantor dan client. Alasannya:

- Data pertanyaan driver/operator client akan melewati server kantor.
- Jika jaringan kantor mati, chatbot client ikut turun.
- Sulit dipertanggungjawabkan untuk production dan skripsi jika infrastrukturnya bercampur.
- IP `10.x.x.x` biasanya private network kantor dan tidak bisa diakses dari VPS client tanpa VPN.

Rekomendasi paling aman:

1. **VPS client menjalankan backend, PostgreSQL, Redis, dashboard, osTicket, dan Ollama embedding sendiri.**
2. Claude/Anthropic tetap dipakai untuk jawaban LLM.
3. Ollama di VPS client hanya dipakai untuk embedding RAG, bukan untuk chat utama.

## Pilihan Arsitektur

### Opsi A - Full Mandiri di VPS Client

Ini rekomendasi utama untuk skripsi dan demo production.

- Backend TRAMOS: Docker
- PostgreSQL + pgvector: Docker
- Redis: Docker
- Ollama embedding: Docker di VPS client
- osTicket: Apache/PHP/MySQL di VPS client
- Nginx + SSL: host VPS

Kelebihan:

- Tidak bergantung pada server kantor.
- Lebih mudah dijelaskan ke dosen/client.
- Data client tetap di VPS client.

Kekurangan:

- VPS perlu RAM lebih besar. Rekomendasi minimal 8 GB RAM jika menjalankan Ollama.

### Opsi B - Managed Embedding

Gunakan Gemini Embedding atau provider embedding lain.

Kelebihan:

- VPS lebih ringan.
- Tidak perlu install Ollama.

Kekurangan:

- Butuh billing/API key yang stabil.
- Ada biaya API.

### Opsi C - Server Ollama Kantor

Hanya gunakan jika benar-benar ada izin dan koneksi aman.

Wajib:

- Ada approval tertulis/eksplisit.
- Koneksi lewat VPN/private peering, bukan expose port 11434 ke internet.
- Client tahu bahwa query embedding diproses di server kantor.

Untuk skripsi, opsi ini tidak direkomendasikan.

## Spesifikasi VPS

Minimum demo tanpa Ollama lokal:

- Ubuntu 22.04/24.04
- 2 vCPU
- 4 GB RAM
- 40 GB storage

Rekomendasi dengan Ollama lokal:

- Ubuntu 22.04/24.04
- 4 vCPU
- 8 GB RAM atau lebih
- 80 GB storage

## Domain yang Disarankan

Gunakan subdomain agar rapi:

```text
api.domain-client.com        -> Backend TRAMOS
dashboard.domain-client.com  -> Dashboard operator
support.domain-client.com    -> osTicket
```

Jika hanya punya satu domain, tetap bisa:

```text
domain-client.com/api        -> Backend
domain-client.com/dashboard  -> Dashboard
domain-client.com/osTicket   -> osTicket
```

Namun subdomain lebih bersih untuk production.

## Step Deploy Ringkas

### 1. Install dependency VPS

```bash
sudo apt update
sudo apt install -y git curl nginx certbot python3-certbot-nginx
```

Install Docker + Docker Compose plugin dari dokumentasi resmi Docker.

### 2. Upload project

```bash
sudo mkdir -p /opt/tramos
sudo chown -R $USER:$USER /opt/tramos
cd /opt/tramos
git clone <repo-tramos> .
```

Jika pakai upload manual, jangan upload:

- `.env`
- `venv/`
- `node_modules/`
- file token/API key pribadi

### 3. Siapkan environment

```bash
cp deploy/env.production.example deploy/env.production
nano deploy/env.production
```

Minimal isi:

```env
TRAMOS_POSTGRES_PASSWORD=password-kuat
CORS_ORIGINS=https://dashboard.domain-client.com

WHATSAPP_API_TOKEN=token-meta-production
WHATSAPP_PHONE_ID=phone-number-id-meta
WHATSAPP_WEBHOOK_VERIFY_TOKEN=token-random-kuat

OSTICKET_BASE_URL=https://support.domain-client.com/osTicket/api
OSTICKET_API_KEY=api-key-osticket

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=api-key-claude-atau-bluepack
ANTHROPIC_BASE_URL=https://ai.bluepack.my.id/anthropic
ANTHROPIC_MODEL=claude-haiku-4-5

JWT_SECRET_KEY=random-minimal-64-karakter
```

Untuk Ollama lokal VPS:

```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:4b
EMBEDDING_DIMENSIONS=2560
EMBEDDING_OLLAMA_URL=http://ollama:11434
```

### 4. Start backend + database + Ollama

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  up -d --build
```

Download model embedding di container Ollama:

```bash
docker exec -it tramos-ollama ollama pull qwen3-embedding:4b
```

### 5. Migrasi dan ingest KB

Entry point backend akan menjalankan migration dasar saat container start. Setelah model embedding siap, ingest ulang KB:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  exec backend python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
```

### 6. Cek readiness

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  exec backend python scripts/vps_preflight_check.py --check-llm --check-embedding
```

Tes retrieval KB:

```bash
docker compose \
  --env-file deploy/env.production \
  -f deploy/docker-compose.prod.yml \
  -f deploy/docker-compose.ollama.yml \
  exec backend python scripts/test_kb_retrieval.py "gps tidak update di jalan" --audience driver
```

### 7. Setup osTicket

Jika osTicket dari XAMPP lokal ingin dipindah:

1. Export database MySQL/MariaDB osTicket.
2. Copy folder osTicket ke VPS.
3. Import database ke MySQL/MariaDB VPS.
4. Sesuaikan file config osTicket.
5. Buat API key di admin panel osTicket.
6. Whitelist IP backend atau `127.0.0.1` jika satu VPS.

Endpoint yang harus bisa diakses:

```text
https://support.domain-client.com/osTicket/api/tickets.json
```

### 8. Setup Nginx dan SSL

Ikuti template di folder `deploy/nginx/`.

Callback Meta nanti:

```text
https://api.domain-client.com/webhook/whatsapp
```

Verify token:

```text
sama dengan WHATSAPP_WEBHOOK_VERIFY_TOKEN
```

### 9. Test WhatsApp production

1. Kirim `halo` dari nomor tester ke nomor WhatsApp Business.
2. Pantau log:

```bash
docker logs -f tramos-backend
```

3. Jika tidak masuk, cek:

- Callback URL HTTPS.
- Verify token.
- Subscribe field `messages`.
- Phone number ID benar.
- Token Meta masih valid.

## Catatan Tentang Embedding

Embedding dokumen saat ingest saja tidak cukup untuk chatbot production. Saat user bertanya, sistem juga perlu membuat embedding untuk query user agar bisa mencari chunk KB paling relevan.

Artinya, di production tetap butuh salah satu:

- Ollama embedding lokal di VPS client.
- Gemini/managed embedding.
- Server embedding eksternal yang resmi dan disetujui.

Fallback `hash` hanya untuk emergency/test offline, bukan kualitas production.

## Checklist Sebelum Demo ke Dosen/Client

- Backend `/health` hijau.
- `/api/kb/health` menunjukkan dokumen dan chunk sudah terisi.
- Test query KB driver berhasil.
- Test dialog flow masalah selesai tidak membuat tiket.
- Test dialog flow masalah gagal membuat tiket.
- osTicket menerima tiket dari TRAMOS.
- WhatsApp webhook verified.
- Dashboard bisa login dan membaca analytics.
- Domain HTTPS aktif.
- Secret production tidak tersimpan di git.
