# TRAMOS Deploy Kit

Isi folder ini:

- `env.production.example`: template environment production.
- `docker-compose.prod.yml`: PostgreSQL pgvector, Redis, dan FastAPI backend.
- `docker-compose.ollama.yml`: opsi Ollama lokal di VPS client untuk embedding RAG.
- `backend.Dockerfile`: image backend production.
- `backend-entrypoint.sh`: migration ringan saat container start.
- `dashboard.Dockerfile`: opsi build dashboard sebagai container Nginx.
- `nginx/`: template Nginx host.
- `systemd/`: alternatif jika backend dijalankan tanpa Docker.

Panduan lengkap ada di:

```text
docs/VPS_DEPLOYMENT_GUIDE.md
docs/VPS_CLIENT_DEPLOYMENT_CHECKLIST.md
docs/CLIENT_HANDOVER_MESSAGE.md
```
