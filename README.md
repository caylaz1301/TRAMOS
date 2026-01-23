# TRAMOS AI Support System

TRAMOS (Tracking Monitor Safety) is an enterprise-grade AI-powered WhatsApp support system for logistics fleet management. It provides intelligent troubleshooting guidance to drivers and automatically creates support tickets when issues are escalated.

## Features

✅ **WhatsApp Integration** - Receive and respond to driver messages via Meta WhatsApp Business API  
✅ **AI Intent Detection** - Understand what drivers need using Google Gemini AI  
✅ **Knowledge Base** - Provide automated troubleshooting steps for GPS, connectivity, etc  
✅ **Automatic Ticketing** - Create osTicket tickets from conversations  
✅ **Multi-turn Conversations** - Remember context with PostgreSQL persistence  
✅ **Async Architecture** - High performance with httpx async HTTP client  

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **AI/LLM**: Google Gemini
- **Ticketing**: osTicket API
- **Messaging**: Meta WhatsApp Business API
- **HTTP Client**: httpx (async)

## Project Structure

```
TRAMOS/
├── main.py                            # FastAPI application entry point
├── requirements.txt                   # Python dependencies
├── .env.example                       # Configuration template
├── app/
│   ├── config.py                      # Environment & settings
│   ├── database_models.py             # SQLAlchemy models
│   ├── routes/
│   │   ├── whatsapp.py               # WhatsApp webhook handler
│   │   └── tickets.py                # Ticket API endpoints
│   ├── schemas/
│   │   ├── whatsapp.py               # WhatsApp data models
│   │   └── ticket.py                 # Ticket request/response models
│   ├── services/
│   │   ├── osticket_service.py       # osTicket API client (async)
│   │   ├── whatsapp_service.py       # WhatsApp API client (async)
│   │   └── conversation_manager.py   # Multi-turn conversation manager
│   └── utils/
│       ├── ai_logic.py               # AI intent detection (Gemini)
│       └── kb_troubleshooting.py     # Knowledge base data
└── README.md
```

## Installation

### 1. Clone and Setup

```bash
cd /Users/vdr/Documents/TRAMOS
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your settings
```

Required settings:
- `OSTICKET_API_URL` - Your osTicket API endpoint
- `OSTICKET_API_KEY` - API key from osTicket admin panel
- `WEBHOOK_VERIFY_TOKEN` - Change to a strong random value

Optional (for outbound WhatsApp messages):
- `WHATSAPP_API_URL` - WhatsApp Graph API URL
- `WHATSAPP_API_TOKEN` - Your WhatsApp token
- `WHATSAPP_PHONE_ID` - Your phone number ID

### 3. Run Application

```bash
# Development (with auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

Access the app:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## How It Works

### 1. Message Received
```
WhatsApp User → WhatsApp Provider → POST /webhook/whatsapp
```

### 2. Intent Detection
System analyzes message and detects:
- **troubleshooting**: Issue found, provide solutions (GPS, Camera, Battery, Connectivity)
- **unresolved**: Solutions didn't work, ask for more details
- **escalate**: User indicates urgent/critical issue
- **resolved**: User confirms problem is fixed
- **unknown**: Unclear, ask for clarification

### 3. Response Sent
Appropriate response is sent back to WhatsApp user based on detected intent.

### 4. Ticket Creation (if needed)
For escalated issues:
```
System → POST /tickets/whatsapp/{phone_number} → osTicket API
```

Ticket is created and user receives ticket number via WhatsApp.

### 5. Conversation State Tracked
Each user's conversation is tracked per phone number with:
- Message history
- Current issue status
- Issue category
- Associated ticket ID

## API Endpoints

### Webhook Endpoints

**Verify Webhook** (WhatsApp calls this on setup)
```
GET /webhook/whatsapp?hub_mode=subscribe&hub_challenge=...&hub_verify_token=...
```

**Receive Messages**
```
POST /webhook/whatsapp
```

### Ticket Endpoints

**Create Ticket (Direct)**
```
POST /tickets
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "GPS Issue",
  "message": "Device not tracking",
  "ip": "127.0.0.1"
}
```

**Create Ticket from WhatsApp**
```
POST /tickets/whatsapp/{phone_number}?email=...&subject=...&message=...
```

**Health Check**
```
GET /tickets/health
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete endpoint reference.

## Testing

Complete testing guide available in [TESTING_GUIDE.md](TESTING_GUIDE.md).

Quick start:

```bash
# Test health check
curl http://localhost:8000/tickets/health

# Test webhook verification
curl "http://localhost:8000/webhook/whatsapp?hub_mode=subscribe&hub_challenge=TEST&hub_verify_token=tramos_webhook_token_change_me"

# Test ticket creation
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Test Ticket",
    "message": "Test message"
  }'
```

## For Production Deployment

1. **Use a VPS/Cloud Provider** (AWS, DigitalOcean, Linode, etc)
2. **Use a Production ASGI Server** (Gunicorn + Uvicorn)
3. **Set up Database** (PostgreSQL recommended for conversation persistence)
4. **Use Environment Variables** for all secrets
5. **Enable HTTPS** (Let's Encrypt with nginx)
6. **Monitor Logs** (Use logging service like Sentry)
7. **Set up Backups** for conversation data
8. **Configure Firewall** to allow only necessary ports

Example nginx config:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Development

### Code Style
- Clear variable naming
- Docstrings for all functions
- Type hints for parameters and returns
- Modular design with separation of concerns
- Minimal but scalable

### Adding New Troubleshooting Categories

Edit `app/utils/ai_logic.py`:

```python
TROUBLESHOOTING_KB = {
    "your_category": {
        "keywords": ["keyword1", "keyword2"],
        "response": "Your troubleshooting steps...",
        "category": "Category Name"
    }
}
```

### Adding New Endpoints

Create route in `app/routes/` and include in `main.py`:

```python
from app.routes import your_new_route

app.include_router(your_new_route.router)
```

## Future Enhancements

### Phase 2: Intelligence
- **LLM Integration**: Replace keyword matching with GPT-4/Claude
- **RAG Knowledge Base**: Vector embeddings for semantic search
- **Multi-language**: Auto-detect and respond in user's language

### Phase 3: Automation
- **Remote Actions**: Vehicle restart, diagnostic commands
- **Scheduled Tasks**: Health checks, automated reports
- **n8n Workflows**: Complex routing and escalation logic

### Phase 4: Analytics & Persistence
- **Database**: PostgreSQL for persistent storage
- **Analytics Dashboard**: Issue trends, resolution metrics
- **Conversation Archive**: Store for future reference and ML training
- **User Profiles**: Track driver history and patterns

## Troubleshooting

**WhatsApp messages not sending?**
- Check WhatsApp API credentials in .env
- Verify phone number format (with country code)
- Review logs for API errors

**Tickets not creating?**
- Verify osTicket API key is valid
- Check osTicket API is enabled in admin
- Test with direct cURL request

**Webhook not receiving messages?**
- Verify webhook URL is publicly accessible (use ngrok for dev)
- Check verify token matches in .env and WhatsApp settings
- Monitor app logs for incoming requests

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for detailed debugging steps.

## Contributing

To contribute improvements:
1. Create a new branch
2. Make your changes with clear commit messages
3. Test thoroughly
4. Submit a pull request with description of changes

## License

This project is part of the TRAMOS fleet management system.

## Support

For issues or questions:
1. Check [TESTING_GUIDE.md](TESTING_GUIDE.md) for debugging steps
2. Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint details
3. Check application logs for error messages
4. Review osTicket logs for ticket creation issues
