# TRAMOS AI Support System - Local Development

TRAMOS is an enterprise-style AI Support System for fleet management.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── config.py                 # Settings and environment variables
│   ├── routes/                   # API endpoints
│   │   ├── webhook.py           # WhatsApp webhook handlers
│   │   └── tickets.py           # Ticket management endpoints
│   ├── schemas/                 # Pydantic models
│   │   ├── whatsapp.py          # WhatsApp data models
│   │   └── ticket.py            # Ticket data models
│   ├── services/                # Business logic
│   │   ├── osticket_service.py  # osTicket API integration
│   │   └── conversation_state.py # User session tracking
│   └── utils/                   # Utilities
│       └── ai_logic.py          # Troubleshooting AI logic
├── main.py                       # FastAPI application entry point
├── requirements.txt              # Python dependencies
└── .env.example                  # Environment variables template
```

## Installation

1. Create a Python virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Configure your environment variables in `.env`:
   - `OSTICKET_API_URL`: Your osTicket API URL
   - `OSTICKET_API_KEY`: Your osTicket API key
   - `WEBHOOK_VERIFY_TOKEN`: Your webhook verification token

## Running the Application

```bash
# Development with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- Docs: `http://localhost:8000/api/docs`
- OpenAPI: `http://localhost:8000/api/openapi.json`

## API Endpoints

### Webhook Management
- **POST** `/webhook/whatsapp` - Handle incoming WhatsApp messages
- **GET** `/webhook/whatsapp` - Verify webhook (used by WhatsApp provider)

### Ticket Management
- **POST** `/tickets` - Create a new ticket
- **GET** `/tickets/health` - Check ticket service health

### Health Checks
- **GET** `/` - Root endpoint (API info)
- **GET** `/health` - Application health check
- **GET** `/config/status` - Configuration status

## Architecture

### Flow: WhatsApp Message to Ticket

1. User sends WhatsApp message
2. WhatsApp Provider → POST `/webhook/whatsapp`
3. System extracts message & sender info
4. AI Engine detects intent:
   - `troubleshooting`: Send help steps
   - `unresolved`: Ask for more details
   - `escalate`: Create ticket immediately
   - `resolved`: Close conversation
   - `unknown`: Request clarification
5. Update conversation state (per phone number)
6. If escalation needed:
   - POST `/tickets` to create osTicket ticket
   - Send ticket number back to user via WhatsApp

### Conversation State

Each phone number has a conversation state tracking:
- Last message & timestamp
- Issue status (initial, troubleshooting, awaiting_details, resolved, escalated)
- Issue category (GPS, Camera, Battery, etc)
- Collected details for the issue
- Associated ticket ID

## Development Notes

- All responses include proper logging for debugging
- osTicket API integration is modular and testable
- Conversation state is in-memory (use Redis/DB for production)
- AI logic is simple (keyword-based) - ready for LLM integration
- Next phase: RAG knowledge base, remote actions, n8n orchestration

## Future Enhancements

1. **LLM Integration**: Replace keyword logic with real AI
2. **Knowledge Base (RAG)**: Add troubleshooting KB with vector search
3. **Remote Actions**: Vehicle diagnostics, system commands
4. **Multi-language Support**: Auto-translate responses
5. **Analytics Dashboard**: Ticket trends, resolution rates
6. **Database Persistence**: Store conversations, tickets, user profiles
7. **n8n Workflows**: Route to specialized teams, escalation logic
