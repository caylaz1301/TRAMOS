# Handover Deploy TRAMOS ke VPS Client

Dokumen ini bisa dipakai untuk menjelaskan ke client apa yang dibutuhkan agar TRAMOS AI dan osTicket bisa dipasang di VPS mereka.

## Status Project

Dari sisi aplikasi, TRAMOS sudah disiapkan untuk deployment ke VPS:

- Backend FastAPI sudah punya Dockerfile production.
- PostgreSQL + pgvector sudah disiapkan lewat Docker Compose.
- Redis sudah disiapkan lewat Docker Compose.
- Knowledge Base/RAG sudah siap di-ingest ke PostgreSQL.
- Embedding tidak memakai server kantor Jababeka untuk production.
- Opsi embedding production yang disarankan: Ollama lokal di VPS client.
- Dashboard bisa dibuild sebagai static web dan disajikan lewat Nginx.
- osTicket bisa dihubungkan lewat API.
- Webhook WhatsApp siap diarahkan ke domain HTTPS production.

Artinya, yang masih dibutuhkan bukan perubahan besar di aplikasi, tetapi data dan akses deployment dari pihak client.

## Yang Harus Disiapkan Client

Minta client menyiapkan:

1. VPS Ubuntu 22.04/24.04
   - Minimum demo: 2 vCPU, 4 GB RAM.
   - Rekomendasi jika embedding Ollama jalan di VPS: 4 vCPU, 8 GB RAM.

2. Domain atau subdomain
   - `api.domain-client.com`
   - `dashboard.domain-client.com`
   - `support.domain-client.com`

3. Akses VPS
   - SSH user.
   - IP VPS.
   - Hak sudo.

4. Akses Meta Developer / WhatsApp Cloud API
   - WhatsApp API token production.
   - Phone Number ID.
   - WhatsApp Business Account ID jika dibutuhkan.
   - Izin untuk mengatur webhook.

5. Akses osTicket production
   - Folder/source osTicket jika akan dipindah dari lokal.
   - Database MySQL/MariaDB osTicket.
   - Admin osTicket.
   - API key osTicket.

6. Email/SMTP jika notifikasi email mau dipakai.

## Arsitektur yang Akan Dipasang

Rencana production:

```text
Internet
  |
  v
Nginx + SSL
  |-- api.domain-client.com        -> TRAMOS Backend FastAPI
  |-- dashboard.domain-client.com  -> TRAMOS Dashboard
  |-- support.domain-client.com    -> osTicket

Docker
  |-- tramos-backend
  |-- tramos-postgres + pgvector
  |-- tramos-redis
  |-- tramos-ollama untuk embedding lokal
```

Server Ollama kantor Jababeka tidak dipakai di production client.

## Pesan Singkat untuk Client

Kamu bisa kirim ini ke client:

```text
Halo Bapak/Ibu, untuk deployment project TRAMOS AI ke VPS, kami membutuhkan:

1. Akses SSH ke VPS Ubuntu dengan hak sudo.
2. Domain/subdomain untuk API, dashboard, dan osTicket.
3. Akses Meta Developer/WhatsApp Cloud API untuk konfigurasi webhook.
4. Token WhatsApp production dan Phone Number ID.
5. Akses admin osTicket serta API key osTicket.
6. Jika osTicket lama ingin dipindahkan, kami membutuhkan backup database dan folder osTicket.

Sistem akan dipasang secara mandiri di VPS client. Server internal kantor/development tidak akan digunakan untuk production. Komponen yang akan dipasang adalah backend TRAMOS, dashboard, PostgreSQL + pgvector, Redis, osTicket, dan service embedding lokal di VPS.
```

## Data Environment yang Perlu Diisi

File production yang harus dibuat di VPS:

```text
deploy/env.production
```

Isian wajib:

```env
TRAMOS_POSTGRES_PASSWORD=<password-kuat>
CORS_ORIGINS=https://dashboard.domain-client.com

WHATSAPP_API_TOKEN=<token-meta-production>
WHATSAPP_PHONE_ID=<phone-number-id>
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<token-random-kuat>

OSTICKET_BASE_URL=https://support.domain-client.com/osTicket/api
OSTICKET_API_KEY=<api-key-osticket>

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<api-key-claude-atau-bluepack>
ANTHROPIC_BASE_URL=https://ai.bluepack.my.id/anthropic
ANTHROPIC_MODEL=claude-haiku-4-5

EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=qwen3-embedding:4b
EMBEDDING_DIMENSIONS=2560
EMBEDDING_OLLAMA_URL=http://ollama:11434

JWT_SECRET_KEY=<random-minimal-64-karakter>
```

## Kesimpulan

Project sudah siap dari sisi struktur deployment. Langkah berikutnya adalah:

1. Tentukan domain/subdomain client.
2. Ambil akses VPS.
3. Pindahkan osTicket ke VPS atau siapkan osTicket baru di VPS.
4. Isi `deploy/env.production`.
5. Jalankan Docker Compose production.
6. Ingest knowledge base.
7. Pasang Nginx + SSL.
8. Pasang callback webhook WhatsApp di Meta Developer.
9. Jalankan test end-to-end.
