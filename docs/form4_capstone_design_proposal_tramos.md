# Form 4

# Capstone Design Proposal

## Design and Development of a WhatsApp-Based Issue Reporting and Analytics Dashboard System for TRAMOS Web at PT Andakara Informatika Nusantara

---

## Group Member

| No. | Student Name | Student ID | Study Program |
|---|---|---|---|
| 1 | Cayla Winri Azzahra | 012202300098 | Information System |
| 2 | Ivander Johana Pratama | 012202300030 | Information System |

Advisor: Hadi Suprayitno, S.Kom., M.M.

Submitted for Capstone Design Project to Faculty of Computer Science, President University

---

# Table of Content

1. Statement of Originality
2. Screenshot of ZeroGPT
3. A. Designs Implementation
   - A.1 Functions / Procedure / Class Implementation
   - A.2 Database Implementation
   - A.3 User Interface Implementation
   - A.4 Integration Module
4. B. Product Display
   - B.1 Software Product Display
   - B.2 Hardware Product Display
5. C. Component Cost Analysis
6. D. Functional Testing
7. E. Manual Guide
   - E.1 System Build Documentation from the Source
   - E.2 End-User System Installation
   - E.3 User Guide per User Role
8. References

---

# Statement of Originality

In my capacity as an active student at President University and as the author of the Capstone Design Project stated below:

Name:

1. Cayla Winri Azzahra - 012202300098
2. Ivander Johana Pratama - 012202300030

Faculty: Computer Science

I hereby declare that my Capstone Design Project entitled "Design and Development of a WhatsApp-Based Issue Reporting and Analytics Dashboard System for TRAMOS Web at PT Andakara Informatika Nusantara" is to the best of my knowledge and belief, an original piece of work based on sound academic principles. If there is any plagiarism detected in this final project, I am willing to be personally responsible for the consequences of these acts of plagiarism and will accept the sanctions against these acts in accordance with the rules and policies of President University.

I also declare that this work, either in whole or in part, has not been submitted to another university to obtain a degree.

Cikarang, May 2026

| Signer 1 | Signer 2 |
|---|---|
| Cayla Winri Azzahra - 012202300098 | Ivander Johana Pratama - 012202300030 |

---

# Screenshot of ZeroGPT

Insert the ZeroGPT originality checking screenshot in this section after the final document is checked.

---

# A. Designs Implementation

## A.1 Functions / Procedure / Class Implementation

The implementation of the TRAMOS system consists of several major modules: WhatsApp Webhook and AI Chatbot Processing, Ticketing System Integration, Database Tracking, Authentication, and Analytics Dashboard. These modules are implemented in a modular structure to support maintainability and separation of concerns. The backend is developed using FastAPI, while the dashboard is developed using React and Vite.

The main implementation files are:

| Module | Main Files |
|---|---|
| FastAPI application entry point | `main.py` |
| Configuration | `app/config.py` |
| WhatsApp webhook | `app/routes/whatsapp.py` |
| Ticket API | `app/routes/tickets.py` |
| Authentication API | `app/routes/auth.py` |
| Analytics API | `app/routes/analytics.py` |
| Database models | `app/database_models.py` |
| Database tracking service | `app/services/database_tracker.py` |
| Chatbot session management | `app/services/chatbot/session_manager.py` |
| Smart dialog flow | `app/services/chatbot/smart_dialog_flow.py` |
| Knowledge base | `app/utils/kb_troubleshooting.py` |
| AI logic | `app/utils/ai_logic.py` |
| osTicket service | `app/services/osticket_service.py` |
| WhatsApp outbound service | `app/services/chatbot/whatsapp_service.py` |
| Dashboard API client | `dashboard/src/api.js` |
| Dashboard pages | `dashboard/src/pages/OverviewPage.jsx`, `PerformancePage.jsx`, `InsightsPage.jsx` |

### A.1.1 FastAPI Application Initialization

The system backend is initialized in `main.py`. This file configures logging, CORS, database initialization, session manager initialization, database tracker initialization, and router registration.

```python
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered WhatsApp support system for TRAMOS fleet management",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

app.include_router(tickets.router)
app.include_router(whatsapp.router)
app.include_router(analytics.router)
app.include_router(auth.router)
```

During startup, the application initializes the database and the conversation session manager:

```python
db_manager = DatabaseManager(settings.DATABASE_URL)
db_manager.init_db()
init_session_manager(db_manager.SessionLocal)
init_db_tracker()
```

This implementation allows the system to store conversation sessions persistently and track operational data for analytics.

### A.1.2 WhatsApp Webhook and AI Intent Processing

The WhatsApp webhook module is implemented in `app/routes/whatsapp.py`. It is the main entry point for incoming WhatsApp messages from Meta WhatsApp Business Platform.

The webhook verification function validates Meta's webhook subscription request:

```python
@router.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
) -> Response:
    if hub_verify_token != settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        return Response(status_code=403, content="Invalid token")

    if hub_mode != "subscribe":
        return Response(status_code=400, content="Invalid mode")

    return Response(content=hub_challenge, media_type="text/plain")
```

Incoming messages are processed by `handle_incoming_message`. This function parses the webhook payload, validates the message type, checks duplicate message IDs, sends the user message to the AI dialog flow, and sends a response back to WhatsApp if the WhatsApp API is configured.

```python
@router.post("/webhook/whatsapp")
async def handle_incoming_message(request: Request) -> Response:
    body = await request.json()

    if body.get("object") != "whatsapp_business_account":
        return Response(content=json.dumps({"status": "ignored"}), media_type="application/json")

    entry = body.get("entry", [{}])[0]
    changes = entry.get("changes", [{}])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [])

    if not messages:
        return Response(content=json.dumps({"status": "ok"}), media_type="application/json")

    message = messages[0]
    from_phone = message.get("from")
    message_type = message.get("type")

    if message_type != "text":
        return Response(content=json.dumps({"status": "ok"}), media_type="application/json")

    message_body = message.get("text", {}).get("body", "").strip()
    response_text = await process_message_with_ai(
        message_body=message_body,
        user_name=user_name,
        phone_number=from_phone
    )
```

To prevent duplicated webhook processing, the system stores recently processed WhatsApp message IDs in memory:

```python
def _is_duplicate_message(message_id: str) -> bool:
    if message_id in _processed_message_ids:
        return True

    _processed_message_ids[message_id] = now
    return False
```

This implementation is important because webhook providers may send the same event more than once.

### A.1.3 Conversation State Machine

The AI chatbot conversation is implemented using a state machine approach. The state definitions are stored in `app/services/chatbot/session_manager.py`.

```python
class DialogState(Enum):
    GREETING = "greeting"
    COLLECTING_NAME = "collecting_name"
    COLLECTING_PROBLEM = "collecting_problem"
    SEARCHING_KB_SOLUTION = "searching_kb_solution"
    PRESENTING_SOLUTION = "presenting_solution"
    ASKING_SOLUTION_WORKED = "asking_solution_worked"
    COLLECTING_UNIT = "collecting_unit"
    COLLECTING_LOCATION = "collecting_location"
    COLLECTING_TIME = "collecting_time"
    CONFIRMING_DETAILS = "confirming_details"
    CREATING_TICKET = "creating_ticket"
    RESOLVED = "resolved"
    CLOSED = "closed"
```

The `ConversationSession` class stores user-specific session data:

```python
class ConversationSession:
    def __init__(self, phone_number: str, session_id: str):
        self.phone_number = phone_number
        self.session_id = session_id
        self.current_state = DialogState.GREETING
        self.message_count = 0
        self.driver_name = None
        self.problem_description = None
        self.problem_category = None
        self.vehicle_unit = None
        self.location = None
        self.issue_time = None
        self.kb_solution = None
        self.conversation_history = []
```

The `SessionManager` class creates, restores, updates, and closes sessions. It also persists session records into the `whatsapp_sessions` table.

```python
def get_or_create_session(self, phone_number: str) -> ConversationSession:
    session = self.get_session(phone_number)
    if session is None:
        session = self.create_session(phone_number)
    else:
        session.update_activity()
    return session
```

### A.1.4 Problem Classification and Knowledge Base Search

Problem classification is implemented in `app/services/chatbot/smart_dialog_flow.py`. The system uses keyword mapping and fallback AI-supported matching to identify problem categories such as GPS, camera, connectivity, battery/device, vehicle, billing, maintenance, and account.

```python
PROBLEM_KEYWORDS = {
    "GPS": {
        "keywords": ["gps", "tracking", "lokasi", "signal", "koordinat", "sinyal", "map"],
        "emoji": "🗺️",
    },
    "Camera": {
        "keywords": ["kamera", "video", "rekam", "dashboard", "feed", "cam"],
        "emoji": "📹",
    },
    "Connectivity": {
        "keywords": ["internet", "koneksi", "network", "offline", "disconnect", "timeout"],
        "emoji": "📡",
    },
}
```

The method `analyze_problem` checks the user's message and returns category, severity, word count, and other problem metadata.

```python
@staticmethod
def analyze_problem(problem_description: str) -> Dict[str, Any]:
    description_lower = problem_description.lower()
    category = None

    for cat, info in SmartDialogFlowHandler.PROBLEM_KEYWORDS.items():
        if any(kw in description_lower for kw in info["keywords"]):
            category = cat
            break

    return {
        "category": category,
        "severity": severity,
        "word_count": word_count
    }
```

The Knowledge Base is implemented in `app/utils/kb_troubleshooting.py`. It contains structured troubleshooting content for GPS, connectivity, camera, device, application, account, report, and other TRAMOS-related issue categories. Each category stores keywords, first response, troubleshooting steps, workaround, escalation triggers, and metadata.

Solution matching is handled by `app/services/chatbot/solution_searcher.py`. It first attempts AI-supported semantic matching with Gemini if configured, then falls back to keyword matching.

```python
def search_solutions(self, problem_description: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    if self.use_llm and self.gemini_available:
        solutions = self._ai_search_solutions(problem_description)
        if solutions:
            return solutions

    return self._keyword_search_solutions(problem_description, category)
```

### A.1.5 AI Logic with Gemini and Fallback Matching

The AI component is implemented in `app/utils/ai_logic.py`. The system configures the Gemini API using the `GEMINI_API_KEY` value from environment variables. If the Gemini API key is not configured, the system continues to work using rule-based and keyword-based fallback logic.

```python
gemini_api_key = getattr(settings, 'GEMINI_API_KEY', '')
self.gemini_available = False

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    self.gemini_client = genai.GenerativeModel(GEMINI_MODEL)
    self.gemini_available = True
else:
    self.gemini_client = None
```

The `detect_intent` method first attempts AI-supported intent detection. If the confidence score is below the configured threshold, the system uses keyword matching.

```python
def detect_intent(self, message: str, context: Optional[str] = None, phone_number: Optional[str] = None):
    if self.use_llm and self.gemini_available:
        intent, category, metadata = self._detect_intent_with_custom_prompt(prompt, user_profile)
        confidence = metadata.get("confidence", 0)
        if confidence >= settings.AI_CONFIDENCE_THRESHOLD:
            return (intent, category, metadata)

    intent, category = self._detect_intent_with_keywords(message)
    return (intent, category, {"source": "keywords", "confidence": 0.6})
```

This approach allows the system to remain functional even when the AI service is unavailable.

### A.1.6 Auto-Ticketing API Integration

The ticketing module is implemented using the osTicket API. When a reported issue cannot be solved by Knowledge Base troubleshooting, the system collects additional information and creates a ticket.

The ticket creation flow from WhatsApp session is implemented in `_create_ticket_from_session` in `app/routes/whatsapp.py`.

```python
async def _create_ticket_from_session(session, phone_number: str, user_name: str) -> str:
    driver_name = session.driver_name or "Unknown Driver"
    problem_desc = session.problem_description or "Tidak ada deskripsi"
    equipment = session.vehicle_unit or "Tidak disebutkan"
    location = session.location or "Tidak disebutkan"
    issue_time = session.issue_time or "Tidak disebutkan"
    problem_cat = session.problem_category or "Service"
    severity = session.problem_severity or "medium"

    subject = f"[TRAMOS] {severity.upper()} - {problem_cat}: {problem_desc[:50]}"

    ticket_request = CreateTicketRequest(
        name=session.driver_name or user_name,
        email=f"{phone_number}@whatsapp.tramos.id",
        subject=subject,
        message=message_body.strip(),
        source="whatsapp",
        ip="127.0.0.1"
    )

    result = await osticket_service.create_ticket(ticket_request)
```

The osTicket service is implemented in `app/services/osticket_service.py`. It sends an HTTP POST request to the osTicket ticket endpoint.

```python
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.post(
        f"{self.base_url}/tickets.json",
        json=payload,
        headers=self.headers
    )
```

The system also provides a direct ticket creation endpoint in `app/routes/tickets.py`:

```python
@router.post("", response_model=CreateTicketResponse)
async def create_ticket(ticket_data: CreateTicketRequest) -> CreateTicketResponse:
    result = await osticket_service.create_ticket(ticket_data)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)

    return result
```

This module ensures that unresolved issues are recorded in the helpdesk system with structured information, including reporter name, phone number, category, priority, unit, location, and conversation history.

### A.1.7 Database Tracking Service

Database writes are centralized in `app/services/database_tracker.py`. This service records users, conversations, turns, messages, tickets, resolutions, analytics data, user profile data, solution attempts, and solution effectiveness.

```python
class DatabaseTracker:
    def get_or_create_user(self, phone_number: str, user_name: str = None) -> Optional[int]:
        user = db.query(User).filter_by(phone_number=phone_number).first()
        if not user:
            user = User(
                phone_number=phone_number,
                user_name=user_name,
                language="id",
                preferred_language="id"
            )
            db.add(user)
            db.commit()
        return user.id
```

The method `track_full_turn` logs a complete interaction turn between the user and the chatbot.

```python
def track_full_turn(self, phone_number: str, user_message: str, bot_response: str,
                    conversation_id: int, turn_number: int, bot_state: str,
                    intent: str = None, category: str = None, processing_time_ms: int = 0):
    self.log_message(...)
    self.log_turn(...)
    self.update_context(...)
    self.increment_user_messages(phone_number)
```

This implementation allows the dashboard and analytics module to use accurate historical data.

### A.1.8 Dashboard Analytics API

The analytics API is implemented in `app/routes/analytics.py`. It provides multiple endpoints for operational dashboard data.

Important endpoints include:

| Endpoint | Purpose |
|---|---|
| `GET /api/analytics/stats/overview` | Total sessions, tickets, active sessions, total messages, success rate |
| `GET /api/analytics/stats/categories` | Issue category distribution |
| `GET /api/analytics/stats/severity` | Issue severity distribution |
| `GET /api/analytics/stats/quality` | Completion rate, average messages, duration, abandoned sessions |
| `GET /api/analytics/data/recent-sessions` | Recent WhatsApp sessions |
| `GET /api/analytics/dashboard` | Combined dashboard data |
| `GET /api/analytics/ml-insights` | Weekly trend, KB effectiveness, top escalated categories, peak hours |
| `GET /api/analytics/activity-log` | Recent activity timeline |
| `GET /api/analytics/alerts/active` | Active system alerts |
| `GET /api/analytics/reports/daily` | Daily report |
| `GET /api/analytics/export/csv` | CSV export |

Example implementation of overview statistics:

```python
@router.get("/stats/overview")
async def get_overview_stats(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    total_sessions = filtered_query.count()
    total_tickets = tickets_filtered.count()
    total_messages = msg_filtered.scalar() or 0
    success_rate = (total_tickets / total_sessions * 100) if total_sessions > 0 else 0

    return {
        "total_sessions": total_sessions,
        "total_tickets": total_tickets,
        "active_sessions": active_sessions,
        "total_messages": total_messages,
        "success_rate": round(success_rate, 2),
        "avg_messages_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
    }
```

### A.1.9 Authentication Module

The dashboard authentication module is implemented in `app/routes/auth.py`. It supports registration, email OTP verification, email/password login, Google login, JWT creation, token verification, and logout.

Password hashing uses bcrypt:

```python
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
```

JWT token generation:

```python
def create_access_token(subject: str, name: str = "", role: str = "user", email: str = ""):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": subject,
        "name": name,
        "role": role,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

This module protects dashboard access so only authenticated users can view analytics.

### A.1.10 React Dashboard Implementation

The frontend communicates with the backend through `dashboard/src/api.js`. Axios is used to call backend API endpoints.

```javascript
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
});
```

The dashboard has three main pages:

1. Overview Page
2. Performance Page
3. Insights Page

Example dashboard data fetching in `OverviewPage.jsx`:

```javascript
const fetchData = async () => {
  try {
    setError(null);
    const dashData = await analyticsService.getDashboard(dateRange.startDate, dateRange.endDate);
    setData(dashData);
  } catch (err) {
    setError('Gagal memuat data. Pastikan server backend aktif.');
  } finally {
    setLoading(false);
  }
};
```

Example insight page data fetching in `InsightsPage.jsx`:

```javascript
const [alertsData, healthData, dashData, mlData, logData] = await Promise.all([
  analyticsService.getActiveAlerts().catch(() => null),
  analyticsService.getHealthCheck().catch(() => null),
  analyticsService.getDashboard(dateRange.startDate, dateRange.endDate).catch(() => null),
  analyticsService.getMLInsights(dateRange.startDate, dateRange.endDate).catch(() => null),
  analyticsService.getActivityLog(15).catch(() => null),
]);
```

This implementation enables the dashboard to display real-time support metrics and operational insights.

## A.2 Database Implementation

The TRAMOS system uses PostgreSQL as the main database management system. PostgreSQL is selected because the project requires relational consistency, transactional reliability, foreign key support, indexing, aggregation queries, and structured analytics.

The SQLAlchemy ORM models are implemented in `app/database_models.py`. The database is initialized using the `DatabaseManager` class:

```python
class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_db(self):
        Base.metadata.create_all(self.engine)
```

### A.2.1 Advantages of Using PostgreSQL

1. High reliability through ACID compliance.
2. Strong relationship integrity using primary keys, foreign keys, indexes, and unique constraints.
3. Effective query execution for analytics, reporting, joins, and aggregation.
4. Scalability for growing numbers of conversations, tickets, messages, and dashboard records.
5. Compatibility with SQLAlchemy ORM and FastAPI backend services.

### A.2.2 Database Architecture

The TRAMOS database is structured around operational support workflow and analytics. The database includes the following entities:

| Table | Description |
|---|---|
| `dashboard_users` | Stores dashboard user accounts, OTP data, Google login data, roles, and login status |
| `users` | Stores WhatsApp user or driver profile data |
| `conversations` | Stores main conversation lifecycle records |
| `message_history` | Stores individual messages from users, bot, and system |
| `tickets` | Stores support ticket records linked to users and conversations |
| `resolutions` | Stores resolution records for tickets |
| `analytics_data` | Stores metric records for dashboard analytics |
| `conversation_context` | Stores cached conversation context by phone number |
| `conversation_turns` | Stores turn-by-turn interaction logs |
| `whatsapp_sessions` | Stores active WhatsApp dialog session state |
| `user_profile_data` | Stores personalization and behavioral data |
| `solution_attempts` | Stores each Knowledge Base solution attempt |
| `solution_effectiveness` | Stores aggregate effectiveness data per solution |

### A.2.3 Conversation and Messaging System

The conversation and messaging system consists of `users`, `conversations`, `message_history`, `conversation_turns`, `conversation_context`, and `whatsapp_sessions`.

The relationship is designed to support:

1. Multiple conversations per WhatsApp user.
2. Multiple message history records per conversation.
3. Turn-by-turn chatbot tracking.
4. Session restoration after backend restart.
5. Context caching for faster response generation.

Important model implementation:

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    current_state = Column(String(50), default=ConversationState.NEW_ISSUE.value)
    category = Column(String(50))
    intent = Column(String(50))
    issue_description = Column(Text)
    ticket_id = Column(Integer, ForeignKey('tickets.id', use_alter=True), nullable=True)
```

### A.2.4 AI Processing and Solution Tracking

The AI processing and solution tracking design is implemented using `solution_attempts`, `solution_effectiveness`, `user_profile_data`, and `analytics_data`.

The table `solution_attempts` records each suggested solution and its result:

```python
class SolutionAttempt(Base):
    __tablename__ = "solution_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    solution_id = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    problem_description = Column(Text, nullable=False)
    solution_steps = Column(JSON)
    kb_match_score = Column(Float)
    outcome = Column(String(20))
    escalation_needed = Column(Boolean, default=False)
```

The table `solution_effectiveness` aggregates outcomes:

```python
class SolutionEffectiveness(Base):
    __tablename__ = "solution_effectiveness"

    solution_id = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    total_attempts = Column(Integer, default=0)
    worked_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    escalated_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    escalation_rate = Column(Float, default=0.0)
```

This is used to measure how effective each Knowledge Base solution is in reducing escalation.

### A.2.5 Ticketing System

Ticketing is implemented through the `tickets` and `resolutions` tables. The `tickets` table stores the internal record of a ticket created from WhatsApp and linked to the external osTicket ID.

```python
class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = Column(String(20), nullable=False)
    osticket_id = Column(Integer, unique=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default=TicketStatus.OPEN.value, nullable=False)
    priority = Column(String(20), default=TicketPriority.MEDIUM.value)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
```

The `resolutions` table stores how the issue was resolved:

```python
class Resolution(Base):
    __tablename__ = "resolutions"

    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False, unique=True)
    resolution_type = Column(String(20), default=ResolutionType.OPERATOR_RESOLVED.value)
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime, default=datetime.utcnow)
    ai_attempted = Column(Boolean, default=False)
    ai_successful = Column(Boolean, default=False)
```

### A.2.6 Analytics and Dashboard System

Analytics data is generated from `whatsapp_sessions`, `tickets`, `resolutions`, `conversation_turns`, and `analytics_data`. The backend provides endpoints that calculate:

1. Total conversations
2. Total tickets
3. Active sessions
4. Total messages
5. Success rate
6. Average messages per session
7. Category distribution
8. Severity distribution
9. Session quality
10. Recent sessions
11. ML insights
12. Activity log

The analytics implementation makes the system useful not only as a chatbot, but also as a management monitoring tool.

## A.3 User Interface Implementation

The TRAMOS user interface is directly implemented as a working React frontend, instead of only using a static prototype. This approach allows the interface to interact directly with the backend API, authentication service, analytics module, and database records.

The frontend implementation is located under `dashboard/src`. It uses React, Vite, Axios, Chart.js, and CSS modules/files for styling.

### A.3.1 Login and Registration Interface

The login interface is implemented in `dashboard/src/Login.jsx`. It supports:

1. Email or phone login
2. Password input with show/hide toggle
3. Google SSO login
4. User registration
5. OTP verification
6. OTP resend
7. Error and success messages

The login interface calls backend authentication APIs through `authService` in `dashboard/src/api.js`.

```javascript
login: async (username, password) => {
  const response = await api.post('/auth/login', { username, password });
  return response.data;
}
```

After successful login, the frontend stores the access token and user information:

```javascript
localStorage.setItem('access_token', response.access_token);
localStorage.setItem('user_name', response.user?.name || email);
localStorage.setItem('user_email', response.user?.email || email);
localStorage.setItem('user_role', response.user?.role || 'user');
```

### A.3.2 Layout and Navigation Interface

The main dashboard layout is implemented in `dashboard/src/components/Layout.jsx`. It contains:

1. TRAMOS dashboard branding
2. Sidebar navigation
3. Page switching
4. User profile display
5. Logout button

Navigation items:

| Navigation | Page |
|---|---|
| Ringkasan | Overview page |
| Performa AI | Performance page |
| Laporan & Notifikasi | Insights page |

### A.3.3 Overview Dashboard Interface

The overview page is implemented in `dashboard/src/pages/OverviewPage.jsx`. It displays key operational metrics:

1. Total conversations
2. Success rate
3. Tickets created
4. Total messages
5. Problem category chart
6. Severity chart
7. Session quality
8. Ticket summary
9. Recent sessions
10. Date filtering

The page automatically fetches dashboard data and refreshes it periodically:

```javascript
useEffect(() => {
  fetchData();
  const interval = setInterval(fetchData, 20000);
  return () => clearInterval(interval);
}, [dateRange]);
```

### A.3.4 AI Performance Interface

The performance page is implemented in `dashboard/src/pages/PerformancePage.jsx`. It displays:

1. AI performance score
2. Resolution distribution
3. AI solved count
4. Ticket escalation count
5. Abandoned sessions
6. Average messages
7. Severity distribution
8. Recommended improvement actions

This page helps analysts evaluate whether the chatbot is reducing manual ticket escalation.

### A.3.5 Reports and Notifications Interface

The insights page is implemented in `dashboard/src/pages/InsightsPage.jsx`. It displays:

1. System health status
2. Active alerts
3. AI recommendations
4. Weekly trend analysis
5. Knowledge Base effectiveness
6. Top escalated categories
7. Peak hours
8. Activity log

This page helps management monitor system health and identify operational issues.

### A.3.6 Date Filter Component

The date filter is implemented in `dashboard/src/components/DateFilter.jsx`. It allows users to filter dashboard data by date range. The filter is used in Overview, Performance, and Insights pages.

### A.3.7 Ticket Monitoring Interface

Ticket monitoring is handled through the osTicket platform. The TRAMOS backend creates tickets automatically using the osTicket API, while support operators can monitor and resolve tickets through osTicket's helpdesk interface.

The created ticket contains:

1. Reporter name
2. WhatsApp phone number
3. Problem description
4. Problem category
5. Urgency level
6. Vehicle unit
7. Location
8. Issue time
9. AI analysis status
10. Recent conversation history

## A.4 Integration Module

TRAMOS uses a modular service-oriented architecture. Each component has a specific responsibility and communicates using REST APIs, database transactions, and JSON payloads.

### A.4.1 WhatsApp Integration

The integration starts when a driver or user sends a message to the WhatsApp Business number. Meta sends the message to the backend webhook endpoint:

```text
POST /webhook/whatsapp
```

The backend parses the message, creates or retrieves a session, processes the message through dialog flow, and sends a response through the WhatsApp Cloud API if configured.

### A.4.2 AI and Knowledge Base Integration

The AI module integrates:

1. Gemini API for intent and solution support when configured.
2. Rule-based fallback for reliability.
3. TRAMOS Knowledge Base for structured troubleshooting.
4. User profile and solution effectiveness tracking.

This ensures that the chatbot can still operate even if the AI provider is unavailable.

### A.4.3 osTicket Integration

When an issue cannot be resolved by the chatbot, the backend sends a ticket creation request to osTicket:

```text
POST {OSTICKET_BASE_URL}/tickets.json
```

The API request includes structured ticket data, and the response returns the ticket ID. The ticket ID is then sent back to the WhatsApp user and stored in the TRAMOS database.

### A.4.4 Dashboard and Analytics Integration

The dashboard uses API calls from `dashboard/src/api.js` to retrieve analytics data from the backend. The backend queries PostgreSQL and returns summarized data in JSON format.

```text
React Dashboard -> Axios -> FastAPI Analytics API -> PostgreSQL
```

This integration enables management users to monitor operational data in near real time.

---

# B. Product Display

## B.1 Software Product Display

This project produces a software system consisting of a WhatsApp chatbot backend, an analytics dashboard, and an osTicket integration. The software product display should include screenshots from each implemented interface.

### B.1.1 Login Interface

The login page is the first page shown to dashboard users. It allows users to sign in using email/phone and password or through Google SSO. It also provides registration and OTP verification for new users.

Components displayed:

| Component | Description |
|---|---|
| TRAMOS branding | Shows the identity of the dashboard |
| Email or phone field | Used to input account identifier |
| Password field | Used to input account password |
| Show/hide password icon | Improves usability |
| Google sign-in button | Allows Google OAuth login |
| Sign in button | Sends login request to backend |
| Sign up form | Allows user registration |
| OTP input | Allows verification of registered email |
| Error alert | Displays login or validation errors |
| Success alert | Displays successful registration or OTP verification |

Screenshot to insert:

```text
Figure B.1 - Login Interface
Recommended screenshot source: dashboard login page from `dashboard/src/Login.jsx`
```

Possible scenarios to screenshot:

1. Normal login form
2. Invalid login error
3. Registration form
4. OTP verification form
5. Successful verification message

### B.1.2 Main Dashboard Layout

After authentication, users are directed to the main dashboard layout. The layout contains sidebar navigation, user profile display, logout button, and the selected dashboard content.

Components displayed:

| Component | Description |
|---|---|
| Sidebar | Navigation menu for Ringkasan, Performa AI, and Laporan & Notifikasi |
| Main content area | Displays selected dashboard page |
| User profile area | Shows logged-in user name and role |
| Logout button | Opens logout confirmation modal |
| Logout modal | Confirms whether user wants to exit |

Screenshot to insert:

```text
Figure B.2 - Dashboard Layout and Sidebar Navigation
Recommended screenshot source: authenticated dashboard from `dashboard/src/components/Layout.jsx`
```

### B.1.3 Overview Dashboard Interface

The Overview interface displays the main operational metrics of the TRAMOS support system.

Displayed metrics:

| Metric | Description |
|---|---|
| Total Percakapan | Total recorded WhatsApp sessions |
| Tingkat Keberhasilan | Percentage of sessions handled without escalation |
| Tiket Dibuat | Total tickets created from unresolved issues |
| Total Pesan | Total messages exchanged in sessions |
| Kategori Masalah | Distribution of issue categories |
| Tingkat Urgensi | Distribution of severity levels |
| Kualitas Sesi | Completion rate, average duration, average messages, abandoned sessions |
| Tiket per Kategori | Tickets grouped by issue category |
| Recent Sessions | Latest user sessions with category, severity, state, and ticket ID |

Screenshot to insert:

```text
Figure B.3 - Overview Dashboard
Recommended screenshot source: `dashboard/src/pages/OverviewPage.jsx`
```

Possible scenarios to screenshot:

1. Dashboard with data
2. Empty state when no data exists
3. Error state when backend is unavailable
4. Date filter active

### B.1.4 AI Performance Interface

The AI Performance interface displays chatbot effectiveness in handling user reports.

Displayed components:

| Component | Description |
|---|---|
| Skor Performa | AI performance score |
| Hasil Penanganan | Donut chart for AI resolved, ticket created, and abandoned sessions |
| Tingkat Penyelesaian | Completion percentage |
| Sesi Dieskalasi | Number of sessions escalated into tickets |
| Rata-rata Pesan | Average messages per session |
| Sesi Dibatalkan | Number of abandoned sessions |
| Distribusi Urgensi | Severity distribution chart |
| Saran Perbaikan | Recommended improvement actions |

Screenshot to insert:

```text
Figure B.4 - AI Performance Dashboard
Recommended screenshot source: `dashboard/src/pages/PerformancePage.jsx`
```

### B.1.5 Reports and Notifications Interface

The Reports and Notifications interface displays system health, alerts, AI recommendations, weekly analysis, and activity logs.

Displayed components:

| Component | Description |
|---|---|
| Status Sistem | Shows database, AI engine, WhatsApp API, osTicket, and KB status |
| Notifikasi | Displays active alerts |
| Rekomendasi AI | Provides operational recommendations |
| Analisis Mingguan | Shows weekly session trends |
| Efektivitas AI | Shows AI resolution rate and escalation count |
| Kategori Sering Dieskalasi | Shows top issue categories escalated to tickets |
| Jam Sibuk | Shows peak reporting hours |
| Activity Log | Shows recent session and ticket events |

Screenshot to insert:

```text
Figure B.5 - Reports and Notifications Dashboard
Recommended screenshot source: `dashboard/src/pages/InsightsPage.jsx`
```

### B.1.6 WhatsApp Chatbot Display

The WhatsApp chatbot display is shown through the user's WhatsApp application. The chatbot guides the user from greeting to troubleshooting and ticket creation.

Expected chatbot scenarios:

| Scenario | Example Display |
|---|---|
| Greeting | Bot greets user and asks for name |
| Problem collection | Bot asks user to describe the issue |
| KB troubleshooting | Bot sends troubleshooting steps for GPS, connectivity, camera, device, or account issue |
| Solution confirmation | Bot asks whether the solution worked |
| Escalation data collection | Bot asks for unit, location, and issue time |
| Ticket confirmation | Bot shows summary and asks for confirmation |
| Ticket created | Bot sends generated ticket ID |
| Error handling | Bot sends safe error message if ticket creation fails |

Screenshot to insert:

```text
Figure B.6 - WhatsApp Chatbot Conversation
Recommended screenshot source: WhatsApp conversation with TRAMOS Business number
```

### B.1.7 osTicket Interface

The osTicket interface is used by support operators to manage tickets created from unresolved WhatsApp conversations.

Displayed ticket information:

1. Ticket ID
2. Subject
3. Reporter name
4. Reporter contact
5. Issue category
6. Priority level
7. Problem description
8. Vehicle unit
9. Location
10. Issue time
11. Conversation context
12. Ticket status

Screenshot to insert:

```text
Figure B.7 - osTicket Ticket Detail
Recommended screenshot source: osTicket dashboard after ticket creation
```

## B.2 Hardware Product Display

This project does not produce a physical hardware product or IoT circuit. Therefore, no circuit design is required.

However, the system requires several hardware and infrastructure components to run:

| Component | Description |
|---|---|
| Development laptop | Used by developers to build and test backend and frontend |
| Server / VPS | Used to host backend, dashboard, database, and reverse proxy in production |
| Smartphone | Used by drivers or testers to interact with the WhatsApp chatbot |
| Internet connection | Required for WhatsApp API, Gemini API, osTicket API, and dashboard access |

---

# C. Component Cost Analysis

This section estimates the cost required to operate the TRAMOS system. The cost is divided into development/demo cost and production deployment cost. The actual cost depends on traffic volume, server provider, WhatsApp message volume, AI usage, and whether existing infrastructure from PT Andakara Informatika Nusantara is used.

Currency assumption for estimation: 1 USD = Rp16,000.

## C.1 Development / Capstone Demo Cost

| No. | Item | Unit | Price per Unit | Total | Note |
|---|---|---:|---:|---:|---|
| 1 | Development laptop | 2 units | Rp0 | Rp0 | Existing student devices |
| 2 | Smartphone for WhatsApp testing | 1 unit | Rp0 | Rp0 | Existing device |
| 3 | Python, FastAPI, SQLAlchemy, React, Vite | 1 package | Rp0 | Rp0 | Open-source software |
| 4 | PostgreSQL local database | 1 installation | Rp0 | Rp0 | Open-source database |
| 5 | osTicket software | 1 installation | Rp0 | Rp0 | Open-source helpdesk software |
| 6 | ngrok free plan for development tunnel | 1 account | Rp0 | Rp0 | Suitable for development/demo only |
| 7 | Google Gemini API free tier / low demo usage | 1 account | Rp0 | Rp0 | Depends on usage and billing setup |
| 8 | WhatsApp Cloud API development/testing | 1 account | Rp0-Rp100,000 | Rp0-Rp100,000 | Depends on message/template usage |
| 9 | Internet connection | 1 month | Rp0 | Rp0 | Existing personal/campus internet |
| 10 | Domain for demo | Optional | Rp0 | Rp0 | Not required if using ngrok |
|  | Estimated Development Total |  |  | Rp0-Rp100,000 | Demo-level estimation |

## C.2 Production Deployment Cost Estimation

| No. | Item | Unit | Price per Unit | Total per Month | Note |
|---|---|---:|---:|---:|---|
| 1 | VPS / cloud server, 1 vCPU 1GB RAM | 1 server | USD 6/month | Rp96,000 | Example: DigitalOcean Basic Droplet 1GB |
| 2 | Larger VPS option, 2 vCPU 2GB RAM | Optional | USD 18/month | Rp288,000 | Recommended if traffic increases |
| 3 | Domain name | 1 domain/year | Rp200,000/year | Rp16,700/month | Approximate `.com`/`.id` style domain budget |
| 4 | SSL certificate | 1 certificate | Rp0 | Rp0 | Can use Let's Encrypt |
| 5 | PostgreSQL database | 1 instance | Rp0-Rp240,000 | Rp0-Rp240,000 | Local PostgreSQL on VPS is free; managed database costs extra |
| 6 | osTicket software | 1 installation | Rp0 | Rp0 | Open-source self-hosted |
| 7 | WhatsApp Cloud API | Usage-based | Per message/template | Variable | Depends on Meta pricing and message category |
| 8 | Gemini API | Usage-based | USD per 1M tokens | Variable | Gemini 2.0 Flash pricing is token-based |
| 9 | Email SMTP service | 1 service | Rp0-Rp150,000 | Rp0-Rp150,000 | For OTP and notification email |
| 10 | Monitoring/logging service | Optional | Rp0-Rp150,000 | Rp0-Rp150,000 | Can use server logs for capstone |
| 11 | Backup storage | Optional | Rp0-Rp100,000 | Rp0-Rp100,000 | For PostgreSQL backup files |
|  | Estimated Minimal Monthly Cost |  |  | Rp112,700 + usage-based fees | VPS + domain monthly equivalent |
|  | Estimated Moderate Monthly Cost |  |  | Rp528,000 + usage-based fees | Larger VPS + DB/SMTP/backup allowance |

## C.3 Usage-Based Cost Notes

1. WhatsApp Cloud API cost depends on message category, recipient country, and Meta's active rate card. Development/testing may be low cost, but production traffic should be calculated from actual monthly volume.
2. Gemini API cost depends on input tokens and output tokens. The current project config uses Gemini model configuration through `GEMINI_MODEL` in `app/config.py`.
3. osTicket is open-source if self-hosted, but it still requires server resources.
4. PostgreSQL is free if self-hosted, but backup and managed database services may add cost.
5. ngrok free plan is useful for development, but production should use a stable domain and HTTPS setup.

---

# D. Functional Testing

Functional testing is grouped by feature. Each feature is placed in a separate table with possible inputs, expected output, and current output result. The current repository has already passed Python syntax compilation and frontend production build testing.

## D.1 Backend Startup and Health Check Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Start backend server | `uvicorn main:app --reload --host 0.0.0.0 --port 9999` | Backend starts and routes are available | Passed by source inspection; runnable command available |
| 2 | Root endpoint | `GET /` | Returns app name, version, status, docs, health, config paths | Implemented in `main.py` |
| 3 | Health endpoint | `GET /health` | Returns database, AI engine, WhatsApp API, osTicket, and KB status | Implemented in `main.py` |
| 4 | Config status endpoint | `GET /config/status` | Returns debug status, service configuration status, and webhook path | Implemented in `main.py` |
| 5 | Internal exception handling | Unexpected backend exception | Returns safe `internal_server_error` JSON response | Implemented in global exception handler |

## D.2 WhatsApp Webhook Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Webhook verification success | Correct `hub.mode=subscribe`, correct `hub.verify_token`, valid `hub.challenge` | Backend returns challenge as plain text | Implemented in `verify_webhook()` |
| 2 | Webhook verification wrong token | Wrong `hub.verify_token` | Backend returns 403 invalid token | Implemented |
| 3 | Webhook verification wrong mode | `hub.mode` not equal to `subscribe` | Backend returns 400 invalid mode | Implemented |
| 4 | Ignore non-WhatsApp object | JSON object not equal to `whatsapp_business_account` | Backend returns ignored status | Implemented |
| 5 | Empty messages | Payload without `messages` array | Backend returns OK without processing | Implemented |
| 6 | Non-text message | Image, document, audio, video, location | Backend ignores safely and returns OK | Implemented |
| 7 | Empty text message | Text message with empty body | Backend returns OK without processing | Implemented |
| 8 | Duplicate WhatsApp message ID | Same `message.id` sent twice | First message processed, duplicate skipped | Implemented through `_is_duplicate_message()` |
| 9 | Valid text message | User sends normal text report | Backend processes with AI dialog flow | Implemented |
| 10 | Invalid JSON | Malformed JSON body | Backend returns 400 `invalid_json` | Implemented |

## D.3 Chatbot Dialog Flow Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | New conversation | First message from phone number | Session created and greeting flow begins | Implemented |
| 2 | Greeting state | "halo", "pagi", first user message | Bot asks for user/driver name | Implemented |
| 3 | Name input valid | "Budi Santoso" | Name stored and bot asks problem description | Implemented |
| 4 | Name input invalid | Empty text, one character, numeric-only input | Bot asks user to re-enter proper name | Implemented in `smart_dialog_flow.py` |
| 5 | Problem input valid | "GPS tidak update" | Problem description stored and category analyzed | Implemented |
| 6 | Problem input too short | Empty or very short text | Bot asks user to explain problem | Implemented |
| 7 | GPS category | "gps tidak akurat", "lokasi tidak update" | Category identified as GPS or related KB category | Implemented |
| 8 | Connectivity category | "internet putus", "koneksi offline" | Category identified as Connectivity | Implemented |
| 9 | Camera category | "kamera error", "video hitam" | Category identified as Camera | Implemented |
| 10 | Device/Battery category | "device mati", "baterai habis" | Category identified as Device/Battery-related issue | Implemented |
| 11 | KB solution found | Category exists in Knowledge Base | Bot sends troubleshooting steps | Implemented |
| 12 | KB solution not found | Unknown issue category | Bot continues to escalation collection | Implemented fallback behavior |
| 13 | Solution worked | User replies "ya", "berhasil", "sudah" | Session marked resolved and outcome tracked | Implemented |
| 14 | Solution failed | User replies "tidak", "belum", "masih error" | Bot collects unit, location, and time | Implemented |
| 15 | Session timeout | User inactive beyond configured timeout | Session considered expired and can be closed/recreated | Implemented in `SessionManager` |

## D.4 Ticket Creation Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Collect vehicle unit | "TRAM-001", "Unit 5", "B 7821" | Unit stored and bot asks location | Implemented |
| 2 | Invalid unit input | "ok", empty, unrelated answer | Bot asks for valid unit information | Implemented through smart input handling |
| 3 | Collect location | "Jakarta", "Tol Cikampek KM 45" | Location stored and bot asks issue time | Implemented |
| 4 | Collect time | "14:30", "jam 3 sore", "tadi pagi" | Time stored and bot shows confirmation | Implemented |
| 5 | Confirmation yes | "ya", "benar", "confirm" | System creates ticket through osTicket service | Implemented |
| 6 | Confirmation no/change | "tidak", "ubah" | Bot returns to data collection | Implemented |
| 7 | osTicket configured | Valid `OSTICKET_BASE_URL` and API key | Ticket created and ticket ID returned | Implemented |
| 8 | osTicket not configured | Empty API key/base URL | Ticket route returns error or service unavailable | Implemented through service config check |
| 9 | osTicket API timeout | External service timeout | Safe error response and error log | Implemented |
| 10 | Ticket notification to user | Ticket creation success | User receives ticket number | Implemented |
| 11 | Ticket database record | Ticket creation success | Ticket, resolution, analytics, and conversation link are stored | Implemented through `db_tracker` |

## D.5 Authentication Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Register new user | Full name, email, password, optional phone | Account created and OTP generated | Implemented |
| 2 | Register existing verified email | Email already verified | Backend returns email already registered error | Implemented |
| 3 | Register existing unverified email | Email exists but not verified | OTP resent and account updated | Implemented |
| 4 | Verify correct OTP | Valid email and correct OTP | Account becomes verified | Implemented |
| 5 | Verify wrong OTP | Valid email and incorrect OTP | Backend returns OTP incorrect | Implemented |
| 6 | Verify expired OTP | OTP after expiration time | Backend returns OTP expired | Implemented |
| 7 | Resend OTP | Valid unverified email | New OTP generated and sent | Implemented |
| 8 | Login valid account | Correct email/phone and password | JWT access token returned | Implemented |
| 9 | Login unverified account | Correct credential but not verified | Backend returns verification required | Implemented |
| 10 | Login wrong password | Incorrect password | Backend returns password error | Implemented |
| 11 | Google login configured | Valid Google ID token | User logged in or auto-registered | Implemented |
| 12 | Token verification | Valid JWT token | Backend returns valid user information | Implemented |
| 13 | Logout | Logout request | Backend returns logout success | Implemented |

## D.6 Analytics Dashboard Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Load overview dashboard | Date range empty or selected | KPI cards, charts, and recent sessions displayed | Implemented |
| 2 | Filter by date | Start date and end date | Dashboard data filtered by selected range | Implemented |
| 3 | No data available | Empty database/session data | Empty state displayed | Implemented in UI |
| 4 | Backend unavailable | API request fails | Error message displayed | Implemented |
| 5 | Category statistics | Sessions with categories | Category distribution returned and chart displayed | Implemented |
| 6 | Severity statistics | Sessions with severity values | Severity chart displayed | Implemented |
| 7 | Quality metrics | Session lifecycle data | Completion rate, duration, average messages, abandoned sessions displayed | Implemented |
| 8 | Recent sessions | Session records exist | Recent sessions table/list displayed | Implemented |
| 9 | Performance page | Dashboard and performance APIs available | AI score and resolution charts displayed | Implemented |
| 10 | Insights page | Alerts, health, ML insight APIs available | Health, alerts, recommendations, activity log displayed | Implemented |
| 11 | Activity log | Recent WhatsApp sessions exist | Recent event list returned | Implemented |
| 12 | Export JSON | Report type input | JSON report returned | Implemented |
| 13 | Export CSV | Number of days | CSV report returned | Implemented |
| 14 | Export HTML | Report type input | HTML report returned | Implemented |

## D.7 Frontend Build Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Install dependencies | `npm install` | Node dependencies installed | Supported by package files |
| 2 | Run development server | `npm run dev` | Vite dev server starts | Implemented script |
| 3 | Production build | `npm run build` | Vite build completes and creates `dist` | Passed in current repository check |
| 4 | API proxy | Frontend requests `/api/*` | Request proxied to backend on port 9999 | Implemented in `vite.config.js` |
| 5 | Auto logout on 401 | Backend returns 401 | Token removed and page reloads | Implemented in Axios interceptor |

## D.8 Database Testing

| No. | Scenario | Every Possible Input | Expected Output | Output Result |
|---|---|---|---|---|
| 1 | Initialize database | Valid PostgreSQL `DATABASE_URL` | Tables created by SQLAlchemy | Implemented |
| 2 | Create user record | New WhatsApp phone number | New `users` record created | Implemented |
| 3 | Reuse existing user | Existing phone number | Existing user updated, not duplicated | Implemented |
| 4 | Create conversation | User ID and phone number | New conversation row created | Implemented |
| 5 | Log conversation turn | User message and bot response | `message_history` and `conversation_turns` updated | Implemented |
| 6 | Store WhatsApp session | Session state changes | `whatsapp_sessions` row updated | Implemented |
| 7 | Create ticket record | Ticket data from osTicket | `tickets` row created and linked | Implemented |
| 8 | Create resolution record | Ticket is resolved or escalated | `resolutions` row created | Implemented |
| 9 | Log analytics | Metric type, value, category | `analytics_data` row created | Implemented |
| 10 | Update solution effectiveness | Solution outcome recorded | `solution_effectiveness` aggregation updated | Implemented |

## D.9 Current Verification Result

The following checks were executed on the repository:

| No. | Test | Command | Result |
|---|---|---|---|
| 1 | Python syntax compilation | `python3 -m compileall -q main.py app scripts init_db.py audit_columns.py query_db.py test_db_integration.py` | Passed |
| 2 | Dashboard production build | `npm run build` from `dashboard` directory | Passed |

---

# E. Manual Guide

## E.1 System Build Documentation from the Source

This section explains how developers can build and run the TRAMOS system from the source code.

### E.1.1 Prerequisites

Required software:

| Software | Purpose |
|---|---|
| Python 3.10+ | Backend runtime |
| pip / venv | Python dependency management |
| PostgreSQL | Main relational database |
| Node.js 16+ | Dashboard frontend runtime |
| npm | Frontend dependency management |
| ngrok | Development webhook tunnel |
| osTicket | External helpdesk ticketing system |
| Meta WhatsApp Business account | WhatsApp webhook and messaging |
| Gemini API key | AI-supported intent/solution processing |

### E.1.2 Backend Installation

Open a terminal and run:

```bash
cd /Users/vdr/Documents/TRAMOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create environment file:

```bash
cp .env.example .env
```

Configure at minimum:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tramos_db

OSTICKET_BASE_URL=http://your-osticket-domain/api
OSTICKET_API_KEY=your-osticket-api-key

WHATSAPP_API_URL=https://graph.facebook.com/v19.0
WHATSAPP_API_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-number-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token

GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash

JWT_SECRET_KEY=your-strong-jwt-secret
CORS_ORIGINS=http://localhost:3000
```

### E.1.3 Database Setup

Start PostgreSQL and create database:

```bash
createdb tramos_db
```

Initialize database:

```bash
python init_db.py
```

Alternative: the backend also calls `DatabaseManager.init_db()` during startup.

### E.1.4 Run Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 9999
```

Access:

| Service | URL |
|---|---|
| API root | `http://localhost:9999/` |
| Health check | `http://localhost:9999/health` |
| Swagger docs | `http://localhost:9999/api/docs` |
| ReDoc | `http://localhost:9999/api/redoc` |
| WhatsApp webhook | `http://localhost:9999/webhook/whatsapp` |

### E.1.5 Frontend Installation

Open another terminal:

```bash
cd /Users/vdr/Documents/TRAMOS/dashboard
npm install
```

Run development server:

```bash
npm run dev
```

Access dashboard:

```text
http://localhost:3000
```

Build production frontend:

```bash
npm run build
```

### E.1.6 ngrok Setup for WhatsApp Webhook

Run ngrok:

```bash
cd /Users/vdr/Documents/TRAMOS
ngrok start --config ngrok.yml
```

Use the generated HTTPS URL as the webhook callback URL in Meta Developer settings:

```text
https://your-ngrok-url.ngrok-free.app/webhook/whatsapp
```

Important security note: the ngrok authtoken should not be committed into a public repository. Store it locally or configure it through the ngrok CLI.

### E.1.7 osTicket Setup

1. Install or access osTicket.
2. Create an API key from the osTicket admin panel.
3. Configure allowed IP if required by osTicket.
4. Put the osTicket base URL and API key into `.env`.
5. Test ticket service:

```bash
curl http://localhost:9999/tickets/health
```

### E.1.8 WhatsApp Webhook Setup

In Meta Developer / WhatsApp Business Platform:

1. Open WhatsApp app settings.
2. Go to Webhooks.
3. Enter callback URL:

```text
https://your-domain-or-ngrok-url/webhook/whatsapp
```

4. Enter verify token matching:

```env
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token
```

5. Subscribe to message events.
6. Send a test WhatsApp message to the business number.

### E.1.9 Recommended Production Deployment

For production, the recommended setup is:

```text
Nginx / HTTPS
    |
    v
Gunicorn + Uvicorn Workers
    |
    v
FastAPI Backend
    |
    +-- PostgreSQL
    +-- osTicket API
    +-- WhatsApp Cloud API
    +-- Gemini API
```

Run production backend:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:9999
```

## E.2 End-User System Installation

The end user does not need to install the backend system manually. The system is accessed through WhatsApp and a web browser.

### E.2.1 Driver / Field User

Required:

| Requirement | Description |
|---|---|
| Smartphone | Android or iOS device |
| WhatsApp application | Used to chat with TRAMOS support bot |
| Internet connection | Required to send and receive WhatsApp messages |
| TRAMOS WhatsApp number | Business number connected to the backend webhook |

Installation steps:

1. Save the TRAMOS WhatsApp support number.
2. Open WhatsApp.
3. Send a message such as "Halo" or describe the issue directly.
4. Follow chatbot instructions.

### E.2.2 Dashboard User

Required:

| Requirement | Description |
|---|---|
| Laptop or desktop browser | Chrome, Edge, Firefox, or Safari |
| Internet connection | Required to access dashboard |
| Dashboard account | Registered email/password or Google account |
| Dashboard URL | URL provided by administrator |

Installation steps:

1. Open the dashboard URL.
2. Login using email/password or Google.
3. If registering, verify OTP sent to email.
4. Access dashboard menus based on role.

### E.2.3 Support Operator

Required:

| Requirement | Description |
|---|---|
| osTicket account | Used to manage support tickets |
| Dashboard account | Used to monitor analytics |
| Browser | Used to access osTicket and TRAMOS dashboard |

Installation steps:

1. Open osTicket URL.
2. Login using operator account.
3. Monitor incoming tickets created by TRAMOS.
4. Update ticket status after handling the issue.

## E.3 User Guide per User Role

### E.3.1 Driver / Field User Guide

| Step | User Action | System Response |
|---|---|---|
| 1 | Open WhatsApp and send message to TRAMOS support number | Bot starts conversation |
| 2 | Send name when asked | Bot stores name and asks issue description |
| 3 | Describe issue, for example "GPS tidak update" | Bot classifies issue and searches KB solution |
| 4 | Follow troubleshooting steps | Bot waits for confirmation |
| 5 | Reply "berhasil" if issue is solved | Bot closes session as resolved |
| 6 | Reply "belum" if issue still happens | Bot starts escalation data collection |
| 7 | Provide unit, location, and issue time | Bot summarizes report details |
| 8 | Confirm details | System creates ticket and returns ticket ID |

### E.3.2 Dashboard User / Analyst Guide

| Step | User Action | System Response |
|---|---|---|
| 1 | Open dashboard URL | Login page displayed |
| 2 | Enter email/phone and password | System validates account |
| 3 | Open Ringkasan page | System displays operational overview |
| 4 | Use date filter | Metrics update based on selected range |
| 5 | Open Performa AI page | System displays AI performance and resolution distribution |
| 6 | Open Laporan & Notifikasi page | System displays alerts, health, recommendations, and activity log |
| 7 | Click refresh | Dashboard reloads latest analytics data |
| 8 | Click logout | System displays logout confirmation and ends session |

### E.3.3 Support Operator Guide

| Step | User Action | System Response |
|---|---|---|
| 1 | Open osTicket dashboard | Ticket list displayed |
| 2 | Select newly created TRAMOS ticket | Ticket detail displayed |
| 3 | Review issue category, priority, unit, location, and conversation history | Operator understands issue context |
| 4 | Handle issue according to support procedure | Ticket status can be updated |
| 5 | Mark ticket resolved when issue is fixed | Resolution data can be used for analytics |

### E.3.4 Administrator Guide

| Step | Admin Action | System Response |
|---|---|---|
| 1 | Configure `.env` values | Backend reads correct service credentials |
| 2 | Start PostgreSQL | Database becomes available |
| 3 | Run backend server | API and webhook become available |
| 4 | Run dashboard server or deploy build | Dashboard becomes available |
| 5 | Configure WhatsApp webhook callback URL | Meta can send messages to backend |
| 6 | Configure osTicket API key | Ticket creation becomes available |
| 7 | Check `/health` endpoint | System component statuses are displayed |
| 8 | Monitor logs | Errors and service issues can be detected |

---

# References

1. FastAPI Documentation. "Features." https://fastapi.tiangolo.com/features/
2. Google AI for Developers. "Gemini Developer API Pricing." https://ai.google.dev/gemini-api/docs/pricing
3. Google AI for Developers. "Gemini API: Generate Content." https://ai.google.dev/api/generate-content
4. DigitalOcean Documentation. "Droplet Pricing." https://docs.digitalocean.com/products/droplets/details/pricing/
5. DigitalOcean. "Droplets." https://www.digitalocean.com/products/droplets
6. ngrok. "Pricing." https://ngrok.com/pricing
7. PostgreSQL Documentation. "Constraints." https://www.postgresql.org/docs/current/ddl-constraints.html
8. RFC Editor. "RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format." https://www.rfc-editor.org/rfc/rfc8259
9. RFC Editor. "RFC 7519: JSON Web Token (JWT)." https://www.rfc-editor.org/rfc/rfc7519.html
10. Meta for Developers. "WhatsApp Business Platform Pricing." https://developers.facebook.com/docs/whatsapp/pricing/
11. osTicket. "Open Source Support Ticket System." https://osticket.com/

