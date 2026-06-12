# Deploy TRAMOS ke Debian Trixie VPS Client

## Prerequisites dari Client

### Wajib Didapat
- [ ] Akses SSH VPS (IP, username, password/SSH key)
- [ ] Akses sudo
- [ ] Domain yang sudah diarahkan ke IP VPS:
  - `api.domain-client.com` → backend
  - `dashboard.domain-client.com` → frontend
  - `support.domain-client.com` → osTicket (kalau mau pakai subdomain)

### Spek VPS
```
Minimal: 2 vCPU, 4 GB RAM
Rekomendasi: 4 vCPU, 8 GB RAM (karena Ollama embedding)
Debian Trixie ✓
```

---

## Langkah 1: Setup Awal VPS Debian Trixie

```bash
# Login sebagai root atau user dengan sudo
ssh root@IP_VPS
# atau
ssh username@IP_VPS

# Update sistem
apt update && apt upgrade -y

# Install paket dasar
apt install -y curl wget git ufw fail2ban certbot python3-certbot-nginx nginx

# Buat user deployer (opsional tapi disarankan)
adduser deployer
usermod -aG sudo deployer
su - deployer
```

## Langkah 2: Install Docker di Debian Trixie

```bash
# Install Docker Official GPG key dan repo
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian bookworm stable" > /etc/apt/sources.list.d/docker.list

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Test Docker
docker --version
docker compose version
```

## Langkah 3: Setup Domain & SSL

```bash
# Arahkan DNS dulu di panel domain client ke IP VPS
# Tunggu propagasi DNS (biasanya 5-30 menit)

# Test propagasi DNS
nslookup api.domain-client.com
nslookup dashboard.domain-client.com

# Install SSL dengan Certbot
sudo certbot --nginx -d api.domain-client.com -d dashboard.domain-client.com

# Auto-renew SSL (otomatis sudah setup sama certbot)
sudo systemctl status certbot.timer
```

## Langkah 4: Clone & Setup Project

```bash
# Buat folder deploy
mkdir -p /opt/tramos
cd /opt/tramos

# Clone project (atau upload via scp/rsync)
git clone https://github.com/username/tramos.git .

# Copy dan edit env production
cp .env.example .env
nano .env
```

### Isi `.env` Production (dari credentials yang kamu punya):

```env
# === CRITICAL - WAJIB DIISI ===
WHATSAPP_API_TOKEN=EA.eyJhbGciOiJIUzI1NiJ9...
WHATSAPP_PHONE_ID=123456789
WEBHOOK_VERIFY_TOKEN=secret_token_kamu

OSTICKET_BASE_URL=https://support.domain-client.com/osTicket/api
OSTICKET_API_KEY=apikey_osTicket

# AI Provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...  # Bluepack atau Anthropic key kamu
ANTHROPIC_BASE_URL=https://ai.bluepack.my.id/anthropic

# Database
DATABASE_URL=postgresql://tramos:TRAMOS_PASSWORD_STRONG@postgres:5432/tramos_db
TRAMOS_POSTGRES_PASSWORD=TRAMOS_PASSWORD_STRONG

# JWT
JWT_SECRET_KEY=generate_random_string_64_char
TOKEN_EXPIRE_MINUTES=480

# Domain
CORS_ORIGINS=https://dashboard.domain-client.com

# Email (untuk notifikasi)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=email@gmail.com
SMTP_PASSWORD=app_password_gmail
```

## Langkah 5: Deploy dengan Docker

```bash
# Build dan start semua service
docker compose up -d --build

# Cek status
docker compose ps
docker compose logs -f backend

# Pull model embedding Ollama
docker exec -it tramos-ollama-1 ollama pull qwen3-embedding:4b

# Ingest knowledge base
docker compose exec backend python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
```

## Langkah 6: Setup Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/tramos-api
server {
    listen 80;
    server_name api.domain-client.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.domain-client.com;

    ssl_certificate /etc/letsencrypt/live/api.domain-client.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.domain-client.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name dashboard.domain-client.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard.domain-client.com;

    ssl_certificate /etc/letsencrypt/live/dashboard.domain-client.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.domain-client.com/privkey.pem;

    root /var/www/dashboard;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
    }
}
```

```bash
# Aktifkan konfigurasi
ln -s /etc/nginx/sites-available/tramos-api /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

## Langkah 7: Build & Deploy Dashboard

```bash
# Build dashboard
cd /opt/tramos/dashboard
npm install
npm run build

# Copy hasil build
rm -rf /var/www/dashboard
cp -r dist /var/www/dashboard

# Set permissions
chown -R www-data:www-data /var/www/dashboard
```

## Langkah 8: Setup osTicket (Jika Dipindah dari Lokal)

```bash
# Install LAMP stack
apt install -y apache2 php php-mysql php-cli php-curl php-json php-gd php-mbstring php-xml php-imap php-ldap php-apcu php-intl php-bcmath php-xmlrpc php-soap php-zip mariadb-server

# Setup database osTicket
mysql_secure_installation
mysql -u root -p
CREATE DATABASE osTicket;
CREATE USER 'osticket'@'localhost' IDENTIFIED BY 'OSTICKET_PASSWORD';
GRANT ALL PRIVILEGES ON osTicket.* TO 'osticket'@'localhost';
FLUSH PRIVILEGES;

# Upload osTicket ke /var/www/support atau /opt/osticket
# Sesuaikan Nginx config untuk support.domain-client.com
```

## Verifikasi Deployment

```bash
# Cek semua service jalan
curl https://api.domain-client.com/health
curl https://dashboard.domain-client.com
docker compose ps

# Cek logs
docker compose logs -f

# Test webhook WhatsApp
curl -X GET "https://api.domain-client.com/webhook/whatsapp?hub.mode=subscribe&hub.challenge=TEST&hub.verify_token=TOKEN_KAMU"
```

## Checklist Handover ke Client

```markdown
### Akses yang Client Simpan
- [ ] SSH credentials VPS
- [ ] Akun panel domain
- [ ] Akun hosting osTicket (kalau ada)
- [ ] Akun Meta/WhatsApp Business

### Password yang Client Ganti
- [ ] Database TRAMOS
- [ ] Database osTicket
- [ ] SSH root password
- [ ] Dashboard admin password

### Domain SSL Certificate
- [ ] Auto-renew sudah aktif (certbot timer)
- [ ] Email notifikasi renew tersetting
```

---

## Perintah Pemeliharaan

```bash
# Restart semua service
docker compose restart

# Update deployment
git pull
docker compose up -d --build

# Backup database
docker compose exec postgres pg_dump -U postgres tramos_db > backup_$(date +%Y%m%d).sql

# Monitoring
docker stats
docker compose logs --tail=100
```

---

## Kontak Darurat

Jika ada masalah:
1. SSH ke VPS
2. `docker compose logs -f backend`
3. `systemctl status nginx`
4. `certbot certificates` (cek SSL)
