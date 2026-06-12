# TRAMOS AI Support System - Project Instructions

## Overview

TRAMOS adalah sistem monitoring dan support operasional transportasi/logistik berbasis WhatsApp chatbot dengan AI-powered troubleshooting dan dashboard analytics.

**Tech Stack:**
- Backend: FastAPI (Python) - Port 9999
- Frontend: React 18 + Vite - Port 3000
- Database: PostgreSQL dengan pgvector (Docker port 5434)
- AI: Anthropic Claude / Google Gemini via unified LLM client
- Ticketing: osTicket API
- WhatsApp: Meta WhatsApp Business API via webhook

## Project Structure

```
TRAMOS/
├── app/                          # FastAPI backend
│   ├── config.py                 # Environment config
│   ├── database_models.py        # SQLAlchemy models
│   ├── routes/                   # API endpoints
│   │   ├── whatsapp.py          # WhatsApp webhook handler
│   │   ├── tickets.py          # Ticket management
│   │   ├── analytics.py        # Dashboard analytics
│   │   ├── auth.py             # JWT authentication
│   │   └── kb.py               # Knowledge base API
│   ├── services/                # Business logic
│   │   ├── chatbot/            # Dialog flow
│   │   │   ├── smart_dialog_flow.py   # Main dialog handler
│   │   │   ├── session_manager.py     # Session state
│   │   │   ├── nlp_extractor.py       # Problem extraction
│   │   │   └── solution_searcher.py   # KB search
│   │   ├── knowledge_base.py    # RAG retrieval
│   │   ├── llm_client.py       # Multi-provider LLM
│   │   └── osticket_service.py # Ticket API
│   ├── schemas/                 # Pydantic models
│   └── utils/                   # AI utilities
├── dashboard/                    # React frontend
│   └── src/
│       ├── pages/              # Dashboard pages
│       │   ├── OverviewPage.jsx    # Main KPI dashboard
│       │   ├── PerformancePage.jsx  # AI performance
│       │   └── InsightsPage.jsx    # Reports & health
│       ├── components/         # Reusable components
│       └── api.js             # Axios service
├── knowledge_base/              # RAG source files
│   ├── tramos_driver_chatbot_kb.txt      # Driver chatbot KB
│   └── tramos_systems_operator_kb.txt   # Operator KB
├── scripts/                     # Utility scripts
│   ├── validate_kb.py         # KB validation
│   ├── ingest_knowledge_base.py  # KB ingestion
│   └── test_kb_retrieval.py   # Retrieval test
└── docs/                        # Documentation
```

## Dialog Flow States

WhatsApp chatbot menggunakan state machine dengan 13 state:

```
GREETING → COLLECTING_NAME → COLLECTING_PROBLEM → ASKING_SOLUTION_WORKED →
COLLECTING_UNIT → COLLECTING_LOCATION → COLLECTING_TIME → CONFIRMING_DETAILS →
CREATING_TICKET → (RESOLVED | CLOSED)
```

**Logic penting:**
- User menjawab "berhasil"/"sudah bisa" → RESOLVED, tidak buat tiket
- User menjawab "tidak"/"masih error" → mulai eskalasi ke tim support
- Acknowledgment ("oke", "siap") → tanya lagi untuk konfirmasi
- Ticket gagal 2x → escape hatch, jangan terus retry

## Knowledge Base System

**Ingestion:**
```bash
python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
```

**Validation:**
```bash
python scripts/validate_kb.py
```

**Retrieval Strategy:**
1. pgvector (jika tersedia) - paling akurat
2. Cosine similarity (fallback) - dari embedding_json
3. Keyword search (selalu jalan) - pelengkap

## Environment Variables

Lihat `.env.example` untuk template lengkap. Variabel kritis:

| Variable | Purpose |
|----------|---------|
| `LLM_PROVIDER` | "gemini" atau "anthropic" |
| `DATABASE_URL` | PostgreSQL connection |
| `WHATSAPP_API_TOKEN` | Meta WhatsApp token |
| `OSTICKET_BASE_URL` | osTicket API endpoint |
| `KB_RAG_ENABLED` | Enable/disable RAG |

## Running the Project

**Backend (Port 9999):**
```bash
cd /Users/vdr/Documents/TRAMOS
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 9999
```

**Frontend (Port 3000):**
```bash
cd dashboard
npm run dev
```

**ngrok (WhatsApp webhook):**
```bash
ngrok start --config ngrok.yml
```

## Important Notes

### Jangan Modify Langsung
- `app/services/chatbot/dialog_flow_handler.py` - DELETED, gunakan SmartDialogFlowHandler
- `app/utils/dialog_flow_engine.py` - DELETED, tidak digunakan di flow utama

### Session Management
- Session timeout: 300 detik (5 menit)
- Session persistence: PostgreSQL via WhatsAppSession table
- `problem_severity` di-restore saat session dari DB

### Error Handling
- osTicket gagal → graceful message ke user, simpan session
- LLM gagal → fallback ke keyword matching
- KB retrieval gagal → kosongkan hasil, jangan fabricate

### Security
- JANGAN expose API key/token di code atau log
- Gunakan `.env` untuk semua secrets
- CORS Origins harus dibatasi untuk production

## Testing

**Backend syntax check:**
```bash
python -m py_compile app/**/*.py
```

**Health endpoint:**
```bash
curl http://localhost:9999/health
```

**KB validation:**
```bash
python scripts/validate_kb.py
```

## Common Issues

1. **WhatsApp webhook tidak terima message**
   - Cek ngrok URL di Meta Business Platform
   - Verifikasi WEBHOOK_VERIFY_TOKEN match
   - Cek ngrok logs: http://localhost:4040

2. **Database connection error**
   - Pastikan PostgreSQL Docker running
   - Check port (5434 bukan 5432)

3. **KB tidak return hasil**
   - Jalankan `python scripts/ingest_knowledge_base.py`
   - Check `python scripts/validate_kb.py`

4. **Ticket creation gagal**
   - Cek osTicket API accessibility
   - Check OSTICKET_API_KEY valid

## Contact for Issues

- Backend: cek logs di terminal uvicorn
- Frontend: cek console browser
- ngrok: http://localhost:4040
- Database: `python query_db.py`