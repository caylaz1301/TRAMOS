# Form 3 - Sections B, C, and D

Project Title: Design and Development of a WhatsApp-Based Issue Reporting and Analytics Dashboard System for TRAMOS Web at PT Andakara Informatika Nusantara

This document is prepared based on the current TRAMOS project repository, especially `main.py`, `app/routes`, `app/services`, `app/utils`, `app/database_models.py`, `dashboard/src`, and the database documentation under `docs/`.

---

## B. DESIGN OF PROPOSED SOLUTION

### B.1 Proposed Solution Overview

The proposed solution is a WhatsApp-based issue reporting and analytics system for TRAMOS support operations. The system enables drivers or field users to report operational issues through WhatsApp, receive automated troubleshooting guidance from an AI-assisted chatbot, and escalate unresolved cases into osTicket support tickets. All conversations, solution attempts, ticket records, and performance metrics are stored in PostgreSQL and presented through a React-based analytics dashboard.

The system is designed to solve the following operational problems:

1. Issue reports from drivers are often unstructured and require repeated manual clarification by support staff.
2. Common problems such as GPS, connectivity, camera, battery/device, and account issues can be handled faster with guided troubleshooting.
3. Support teams need historical records and analytics to understand recurring issue patterns, escalation rates, AI effectiveness, and system health.
4. Ticket creation should be automated when chatbot troubleshooting does not resolve the issue.

The solution combines four main subsystems:

| Subsystem | Purpose | Existing Project Implementation |
|---|---|---|
| WhatsApp Webhook Backend | Receives and verifies incoming WhatsApp messages | `app/routes/whatsapp.py` |
| AI Chatbot and Dialog Flow | Collects issue data, searches KB solutions, and decides whether to escalate | `app/services/chatbot/*`, `app/utils/ai_logic.py`, `app/utils/kb_troubleshooting.py` |
| Ticketing Integration | Creates support tickets in osTicket when issues are unresolved | `app/services/osticket_service.py`, `app/routes/tickets.py` |
| Analytics Dashboard | Displays conversation, ticket, issue category, quality, performance, and alert data | `dashboard/src/pages/*`, `app/routes/analytics.py` |

### B.2 System Architecture

The system uses a client-server architecture. WhatsApp users interact with the system through Meta WhatsApp Business Platform. The backend service is built with FastAPI and receives webhook events, processes chatbot logic, stores records in PostgreSQL, integrates with Gemini AI and osTicket, and exposes analytics APIs to the dashboard.

```text
WhatsApp User
    |
    | Message
    v
Meta WhatsApp Business Platform
    |
    | Webhook POST /webhook/whatsapp
    v
FastAPI Backend
    |
    |-- Webhook Verification and Message Parsing
    |-- Dialog Flow and Session Management
    |-- Knowledge Base / Gemini AI Assistance
    |-- Database Tracking
    |-- osTicket Ticket Creation
    |
    +--> PostgreSQL Database
    |
    +--> osTicket API
    |
    +--> Analytics API /api/analytics/*
             |
             v
       React Dashboard
```

### B.3 Main User Roles

| Role | Description | Main Interaction |
|---|---|---|
| Driver / Field User | Reports operational issues through WhatsApp | Sends issue report, follows troubleshooting steps, confirms whether solution works |
| Support Operator | Handles unresolved cases through osTicket | Receives created ticket with structured issue details |
| Analyst / Management | Monitors support performance through dashboard | Reviews issue category, ticket volume, AI performance, trends, and alerts |
| Administrator | Configures system credentials and monitors service readiness | Manages environment variables, database, API keys, deployment, and dashboard access |

### B.4 Functional Requirements

| No | Functional Requirement | Project Evidence |
|---|---|---|
| FR-01 | The system shall verify WhatsApp webhook requests using a configured verify token. | `verify_webhook()` in `app/routes/whatsapp.py` |
| FR-02 | The system shall receive incoming WhatsApp text messages and ignore unsupported non-text messages safely. | `handle_incoming_message()` in `app/routes/whatsapp.py` |
| FR-03 | The system shall prevent duplicate processing of the same webhook message ID. | `_is_duplicate_message()` in `app/routes/whatsapp.py` |
| FR-04 | The system shall maintain a multi-turn dialog session per WhatsApp phone number. | `SessionManager` and `ConversationSession` in `app/services/chatbot/session_manager.py` |
| FR-05 | The system shall collect user name, problem description, vehicle unit, location, time, and confirmation before ticket creation. | Dialog states in `DialogState` and handlers in `smart_dialog_flow.py` |
| FR-06 | The system shall classify issue categories such as GPS, connectivity, camera, device, vehicle, account, billing, and maintenance. | `PROBLEM_KEYWORDS` in `app/services/chatbot/smart_dialog_flow.py`; `KB_TROUBLESHOOTING` in `app/utils/kb_troubleshooting.py` |
| FR-07 | The system shall search troubleshooting solutions from a Knowledge Base before escalation. | `solution_searcher.py` and `kb_troubleshooting.py` |
| FR-08 | The system shall ask whether the provided solution worked. | `DialogState.ASKING_SOLUTION_WORKED` and `_handle_solution_feedback()` |
| FR-09 | The system shall create an osTicket ticket if the solution fails or escalation is required. | `_create_ticket_from_session()` in `app/routes/whatsapp.py`; `osTicketService.create_ticket()` |
| FR-10 | The system shall store users, conversations, messages, tickets, resolutions, analytics, session state, and solution attempts. | SQLAlchemy models in `app/database_models.py` |
| FR-11 | The system shall provide dashboard authentication through email/password, OTP, Google SSO, and JWT token. | `app/routes/auth.py`, `dashboard/src/Login.jsx` |
| FR-12 | The system shall expose analytics APIs for overview statistics, categories, severity, quality, insights, alerts, reports, and visualizations. | `app/routes/analytics.py` |
| FR-13 | The dashboard shall display overview, AI performance, and reporting/notification pages. | `dashboard/src/pages/OverviewPage.jsx`, `PerformancePage.jsx`, `InsightsPage.jsx` |

### B.5 Non-Functional Requirements

| No | Requirement | Description | Current Implementation |
|---|---|---|---|
| NFR-01 | Availability | Backend should keep running and provide health status for monitoring. | `/health`, `/tickets/health`, `/api/analytics/alerts/health-check` |
| NFR-02 | Reliability | Duplicate webhook events should not create duplicate responses or tickets. | In-memory message ID deduplication in `whatsapp.py` |
| NFR-03 | Maintainability | The system should separate routing, business logic, service integration, models, and UI. | `app/routes`, `app/services`, `app/utils`, `app/schemas`, `dashboard/src` |
| NFR-04 | Scalability | Database-backed sessions and indexed tables should support historical analytics. | SQLAlchemy models with indexes in `database_models.py` |
| NFR-05 | Security | Secrets should be configured through environment variables and dashboard access should use authentication. | `.env`, `app/config.py`, JWT auth in `auth.py` |
| NFR-06 | Usability | WhatsApp replies should be short, clear, and step-by-step for drivers. | `smart_response_system.py`, `smart_dialog_flow.py`, KB response formatting |
| NFR-07 | Observability | Logs and analytics records should support debugging and performance tracking. | Python logging, `DatabaseTracker`, analytics endpoints |

### B.6 Main Conversation Flow

```text
Start
  |
  v
User sends WhatsApp message
  |
  v
Backend verifies payload and message type
  |
  v
Check duplicate message ID
  |
  v
Get or create user session
  |
  v
Greeting -> Collect Name -> Collect Problem
  |
  v
Analyze issue category and severity
  |
  v
Search Knowledge Base solution
  |
  v
Send troubleshooting steps
  |
  v
Ask whether solution worked
  |
  +-- If worked --> Mark resolved, save analytics, close session
  |
  +-- If not worked --> Collect unit, location, time
                         |
                         v
                       Confirm details
                         |
                         v
                       Create osTicket ticket
                         |
                         v
                       Notify user and close session
```

### B.7 Database Design Summary

The database is designed to support both operational workflow and analytics. Operational records are stored in users, conversations, message history, WhatsApp sessions, tickets, and resolutions. Analytical and improvement-related records are stored in analytics data, conversation turns, user profile data, solution attempts, solution effectiveness, and dashboard summaries.

| Entity | Purpose |
|---|---|
| `dashboard_users` | Stores dashboard login accounts, email/password users, Google users, OTP verification, and role data |
| `users` | Stores WhatsApp user/driver profiles identified by phone number |
| `conversations` | Stores active or completed support conversations |
| `message_history` | Stores individual user, bot, and system messages |
| `tickets` | Stores support ticket records linked to WhatsApp users and osTicket IDs |
| `resolutions` | Stores resolution type, timing, AI attempt status, and resolution notes |
| `analytics_data` | Stores metric values for reporting and trend analysis |
| `conversation_context` | Stores cached context by phone number |
| `conversation_turns` | Stores turn-by-turn user and bot interactions |
| `whatsapp_sessions` | Stores current state of guided WhatsApp dialog sessions |
| `user_profile_data` | Stores personalization and behavioral profile data |
| `solution_attempts` | Tracks each KB solution attempt and its outcome |
| `solution_effectiveness` | Aggregates solution success and escalation metrics |

Detailed table definitions and relationships are documented in `docs/data_dictionary.md` and `docs/entity_tables_and_relations.md`.

### B.8 User Interface Design

The dashboard uses React and Vite. It contains login/registration and three main dashboard pages.

| Page | Function |
|---|---|
| Login / Register | Provides email-password login, registration, OTP verification, and Google login |
| Overview | Displays total conversations, success rate, ticket count, total messages, category distribution, severity distribution, session quality, and recent sessions |
| Performance | Displays AI performance score, resolution distribution, escalation count, average messages, abandoned sessions, severity, and improvement suggestions |
| Insights | Displays system health, alerts, AI recommendations, weekly analytics, KB effectiveness, peak hours, and activity log |

### B.9 Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend API | Python, FastAPI, Uvicorn | Supports async API development, automatic OpenAPI docs, and clean router structure |
| Database | PostgreSQL, SQLAlchemy | Relational data model, foreign keys, indexes, ORM-based access |
| AI / LLM | Google Gemini API with rule-based fallback | Used for intent detection and context-aware AI support when API key is configured |
| Messaging | Meta WhatsApp Business Platform / Cloud API | Receives WhatsApp reports and sends responses |
| Ticketing | osTicket API | Creates support tickets for unresolved issues |
| Frontend | React, Vite, Axios, Chart.js | Dashboard UI, API calls, and data visualizations |
| Authentication | JWT, bcrypt, OTP email, Google OAuth | Dashboard access control and user verification |
| Deployment Support | `.env`, ngrok for local webhook tunneling | Environment-based configuration and public callback URL during development |

### B.10 Project Constraints and Assumptions

| Constraint / Assumption | Explanation |
|---|---|
| WhatsApp webhook requires a public HTTPS URL | During development this can be provided using ngrok; production should use a real HTTPS domain |
| osTicket must be configured with a valid base URL and API key | Ticket creation depends on `OSTICKET_BASE_URL` and `OSTICKET_API_KEY` |
| Gemini requires a valid API key | AI features fall back to keyword/KB matching if Gemini is not configured |
| PostgreSQL must be running | Database-backed sessions and dashboard analytics depend on PostgreSQL |
| Current system mainly handles text messages | Non-text WhatsApp messages are ignored safely in the webhook handler |
| Dashboard data depends on recorded conversation sessions | Analytics pages require historical session/ticket data to show meaningful charts |

---

## C. STANDARDS USED

The following standards and technical specifications are used or referenced in this project. The implementation mapping is based on the existing project code.

| No | Area | Standard / Specification | Implementation in TRAMOS |
|---|---|---|---|
| 1 | API Architecture | RESTful API principles | FastAPI exposes HTTP endpoints for webhook, tickets, auth, health, and analytics using `GET` and `POST`. |
| 2 | API Documentation | OpenAPI 3.x / Swagger UI / ReDoc | FastAPI automatically exposes `/api/docs`, `/api/redoc`, and `/api/openapi.json`. |
| 3 | Data Exchange | JSON - RFC 8259 | WhatsApp payloads, backend API requests/responses, dashboard API responses, and osTicket integration use JSON. |
| 4 | Authentication Token | JSON Web Token - RFC 7519 | Dashboard authentication issues JWT access tokens through `app/routes/auth.py`. |
| 5 | Password Storage | bcrypt password hashing | Email/password dashboard accounts are hashed using bcrypt before being stored. |
| 6 | Transport Security | HTTPS / TLS for public webhook | WhatsApp webhook callback must be reachable through HTTPS, typically via ngrok in development and a proper domain in production. |
| 7 | Webhook Verification | Meta webhook challenge-response pattern | `GET /webhook/whatsapp` validates `hub.verify_token` and returns `hub.challenge`. |
| 8 | WhatsApp Messaging | Meta WhatsApp Cloud API message format | Outbound messages are sent to `/{phone_id}/messages` using bearer token authorization in `whatsapp_service.py`. |
| 9 | AI Content Generation | Gemini API `generateContent` method | `ai_logic.py` and `solution_searcher.py` configure Gemini and call content generation for AI-assisted intent/solution logic. |
| 10 | Backend Runtime | ASGI | FastAPI is served through Uvicorn/Gunicorn ASGI workers. |
| 11 | Database | PostgreSQL relational database | Conversation, ticket, dashboard user, analytics, and solution records are stored in PostgreSQL tables. |
| 12 | ORM | SQLAlchemy ORM | Models, relationships, indexes, and sessions are defined in `app/database_models.py`. |
| 13 | Schema Validation | Pydantic models | Request/response schemas are defined in `app/schemas`, and auth route requests use Pydantic `BaseModel`. |
| 14 | Date-Time Format | ISO 8601 / RFC 3339-compatible timestamps | API responses such as health checks and dashboard analytics return ISO-formatted timestamps. |
| 15 | Frontend Build | Vite React build standard | Dashboard is built with Vite and React components under `dashboard/src`. |
| 16 | HTTP Client | Async HTTP via httpx | osTicket and WhatsApp service calls use `httpx.AsyncClient`. |
| 17 | Configuration | Environment-based configuration | `app/config.py` loads `.env` using `python-dotenv`; external credentials are expected from environment variables. |
| 18 | Modeling | UML-style system modeling | The project can be represented with use case, activity, sequence, class, and ER diagrams based on the implemented modules and database entities. |
| 19 | Logging | Python logging | Backend startup, webhook processing, database tracking, and service integrations are logged through Python logging. |
| 20 | Testing Practice | Unit, integration, and end-to-end scenario testing | Existing tests/scripts include `test_db_integration.py`, `init_db.py`, and manual webhook/ticket testing scenarios. |

### C.1 Standards Mapping to Current Source Code

| Standard Area | Source Code / File |
|---|---|
| FastAPI application and OpenAPI docs | `main.py` |
| WhatsApp webhook verification and event processing | `app/routes/whatsapp.py` |
| JWT authentication | `app/routes/auth.py` |
| Pydantic ticket schema | `app/schemas/ticket.py` |
| PostgreSQL ORM models | `app/database_models.py` |
| Gemini AI logic | `app/utils/ai_logic.py`, `app/services/chatbot/solution_searcher.py` |
| osTicket integration | `app/services/osticket_service.py` |
| WhatsApp outbound API | `app/services/chatbot/whatsapp_service.py` |
| Dashboard API calls | `dashboard/src/api.js` |
| Dashboard pages | `dashboard/src/pages/*` |

---

## D. IMPLEMENTATION AND TESTING SCENARIO

### D.1 Implementation Plan

| Phase | Activity | Technical Detail | Output |
|---|---|---|---|
| 1 | Environment setup | Prepare Python virtual environment, install `requirements.txt`, install dashboard dependencies, configure `.env`, PostgreSQL, WhatsApp, Gemini, osTicket | Development environment is ready |
| 2 | Database initialization | Run database table creation through `DatabaseManager.init_db()` or `init_db.py` | PostgreSQL schema is created |
| 3 | Backend API setup | Configure FastAPI app, routers, CORS, health endpoints, and lifespan startup | Backend runs on port 9999 |
| 4 | WhatsApp webhook setup | Implement verification endpoint and incoming message endpoint | Meta can verify webhook and send messages |
| 5 | Chatbot dialog flow | Implement session state machine: greeting, name, problem, KB solution, solution feedback, unit, location, time, confirmation, ticket creation | Multi-turn conversation works |
| 6 | Knowledge Base and AI matching | Use KB categories and Gemini-supported intent/solution logic with fallback matching | Bot can classify and suggest solutions |
| 7 | osTicket integration | Build ticket payload and send it to osTicket API | Unresolved issues become support tickets |
| 8 | Database tracking | Store users, conversations, turns, messages, tickets, resolutions, analytics, and solution attempts | Historical and analytical data are available |
| 9 | Dashboard authentication | Implement register, OTP verification, login, Google login, JWT token creation, logout | Dashboard access is controlled |
| 10 | Dashboard analytics pages | Build overview, performance, insights, notifications, and report views | Management can monitor support performance |
| 11 | Integration testing | Test webhook, session flow, ticket creation, database persistence, and dashboard data | End-to-end system is verified |
| 12 | Deployment preparation | Prepare `.env`, production CORS, HTTPS domain/ngrok, database credentials, API keys, and service startup commands | System is ready for demo or production deployment |

### D.2 Module Implementation Details

| Module | Implementation Description |
|---|---|
| `main.py` | Creates FastAPI app, configures CORS, registers routers, initializes database, session manager, and tracker on startup |
| `app/config.py` | Loads environment variables such as database URL, WhatsApp token, osTicket API key, Gemini key, SMTP, Google OAuth, and CORS |
| `app/routes/whatsapp.py` | Handles Meta webhook verification, incoming messages, message deduplication, chatbot processing, and ticket creation from session data |
| `app/services/chatbot/session_manager.py` | Maintains session state by phone number and persists session data to `whatsapp_sessions` |
| `app/services/chatbot/smart_dialog_flow.py` | Validates user inputs, analyzes problem category/severity, handles solution feedback, and guides data collection |
| `app/services/chatbot/solution_searcher.py` | Searches KB solutions using Gemini when configured, with keyword fallback |
| `app/utils/kb_troubleshooting.py` | Stores structured troubleshooting categories and step-by-step solutions |
| `app/services/osticket_service.py` | Sends ticket creation requests to osTicket API using async HTTP client |
| `app/services/database_tracker.py` | Centralizes writes for user, conversation, message, ticket, resolution, analytics, profile, solution attempts, and summary data |
| `app/routes/analytics.py` | Provides dashboard endpoints for overview stats, categories, severity, quality, recent sessions, insights, reports, visualizations, predictions, alerts, and benchmarks |
| `app/routes/auth.py` | Provides dashboard registration, OTP verification, login, Google login, JWT verification, and logout |
| `dashboard/src/api.js` | Centralizes Axios calls to backend `/api` endpoints |
| `dashboard/src/pages/OverviewPage.jsx` | Displays core support metrics and charts |
| `dashboard/src/pages/PerformancePage.jsx` | Displays AI performance score, resolution distribution, escalation metrics, and improvement actions |
| `dashboard/src/pages/InsightsPage.jsx` | Displays system status, notifications, AI recommendations, weekly trends, KB effectiveness, and activity logs |

### D.3 Testing Strategy

Testing is divided into five levels:

1. Syntax/build verification
2. Backend API testing
3. Database integration testing
4. WhatsApp-to-ticket end-to-end testing
5. Dashboard functional testing

### D.4 Detailed Testing Scenarios

| No | Scenario | Preconditions | Test Steps | Expected Result |
|---|---|---|---|---|
| 1 | Backend startup | `.env` exists, dependencies installed | Run `uvicorn main:app --reload --host 0.0.0.0 --port 9999` | Backend starts and logs app name, database status, WhatsApp status, osTicket status, and AI status |
| 2 | API root endpoint | Backend running | Open `GET /` | API returns app name, version, status, docs path, health path |
| 3 | Health check | Backend running | Open `GET /health` | Response includes database, AI engine, WhatsApp API, osTicket, and KB status |
| 4 | Webhook verification success | Backend running, verify token matches `.env` | Send `GET /webhook/whatsapp?hub.mode=subscribe&hub.challenge=TEST&hub.verify_token=<token>` | Backend returns `TEST` as plain text |
| 5 | Webhook verification failure | Backend running | Send verification request with wrong token | Backend rejects request with error status |
| 6 | Incoming text message | Webhook configured, valid WhatsApp payload | Send POST payload with `object=whatsapp_business_account` and text message | Backend extracts sender, message, session, and response |
| 7 | Non-text message handling | Webhook configured | Send image/document/audio/video payload | Backend ignores safely and returns OK |
| 8 | Duplicate webhook event | Same WhatsApp message ID sent twice within dedup window | Send identical payload twice | First payload is processed, second returns duplicate OK without reprocessing |
| 9 | New session creation | No active session for phone number | User sends first message | System creates `ConversationSession` and `whatsapp_sessions` record |
| 10 | Name collection | Session state is `collecting_name` | User sends name | System stores `driver_name` and asks for problem description |
| 11 | Problem classification | Session state is `collecting_problem` | User sends "GPS tidak update di unit saya" | System classifies category as GPS or related KB category and searches solution |
| 12 | KB solution delivery | KB has matching category | User reports common GPS/connectivity/camera/device issue | Bot sends troubleshooting steps and asks if solution worked |
| 13 | Solution success | State is `asking_solution_worked` | User replies "sudah berhasil" | Session is marked resolved and solution outcome is tracked |
| 14 | Solution failure | State is `asking_solution_worked` | User replies "belum" or "masih error" | System starts escalation data collection |
| 15 | Unit validation | State is `collecting_unit` | User sends vehicle/unit number | System stores `vehicle_unit` and asks location |
| 16 | Location validation | State is `collecting_location` | User sends location | System stores `location` and asks issue time |
| 17 | Time input | State is `collecting_time` | User sends `14:30`, `jam 3 sore`, or similar | System stores normalized or accepted issue time and shows confirmation |
| 18 | Ticket confirmation | State is `confirming_details` | User confirms details | System calls osTicket service and closes session if successful |
| 19 | Ticket creation failure | osTicket URL/key invalid or unavailable | User confirms ticket creation | System returns safe failure message and logs error |
| 20 | Database persistence | PostgreSQL running | Complete a chat flow | Records are stored in `users`, `conversations`, `conversation_turns`, `whatsapp_sessions`, and possibly `tickets` |
| 21 | Dashboard login | Backend and dashboard running | Login through dashboard | User receives access token and enters dashboard |
| 22 | OTP registration | SMTP configured | Register new email account | OTP is generated, sent, and account can be verified |
| 23 | Analytics dashboard data | Database contains sessions | Open Overview page | KPI cards, category chart, severity chart, quality metrics, and recent sessions load |
| 24 | Performance page | Database contains sessions/tickets | Open Performance page | AI score, resolution chart, escalation metrics, and suggestions are shown |
| 25 | Insights page | Backend analytics running | Open Insights page | System health, alerts, recommendations, and weekly analysis are shown |
| 26 | Frontend production build | Node dependencies installed | Run `npm run build` in `dashboard` | Vite build succeeds and produces `dist` assets |
| 27 | Python syntax verification | Python installed | Run `python3 -m compileall -q main.py app scripts init_db.py audit_columns.py query_db.py test_db_integration.py` | Python files compile without syntax errors |

### D.5 Acceptance Criteria

The project is considered successful when the following criteria are met:

| No | Acceptance Criteria |
|---|---|
| 1 | Meta WhatsApp webhook can be verified successfully using the configured verify token |
| 2 | Incoming WhatsApp text messages are received and processed by the backend |
| 3 | The chatbot can guide users through a multi-turn support flow |
| 4 | The chatbot can classify common issue categories and provide KB troubleshooting steps |
| 5 | The system can detect whether a solution worked or should be escalated |
| 6 | The system can collect complete ticket data: driver name, problem, category, unit, location, and issue time |
| 7 | The system can create an osTicket ticket for unresolved issues |
| 8 | The system stores operational records in PostgreSQL |
| 9 | Dashboard users can authenticate and access analytics pages |
| 10 | Dashboard pages show meaningful metrics from backend analytics APIs |
| 11 | Backend syntax check and frontend production build pass |

### D.6 Test Results from Current Repository Inspection

The following checks were performed on the current repository state:

| Check | Command | Result |
|---|---|---|
| Python syntax compile | `python3 -m compileall -q main.py app scripts init_db.py audit_columns.py query_db.py test_db_integration.py` | Passed |
| Dashboard production build | `npm run build` in `dashboard` | Passed |

### D.7 Known Risks and Required Improvements Before Final Demonstration

These items are based on the current repository inspection and should be addressed before final demo or production deployment:

| No | Risk / Issue | Impact | Recommendation |
|---|---|---|---|
| 1 | `ngrok.yml` contains an exposed ngrok authtoken and invalid trailing text | Security risk and possible ngrok config failure | Rotate ngrok token, remove token from repository, store it locally, and clean the YAML file |
| 2 | Some documentation still mentions Ollama/Mistral although code has moved toward Gemini | Documentation inconsistency | Update README, `.env.example`, and setup guide to use Gemini configuration |
| 3 | `ai_logic.py` still checks `self.ollama_available` in one method | Runtime error if that method is called | Replace with Gemini availability check |
| 4 | Analytics health check still probes Ollama and legacy env names | Dashboard may show wrong AI/service status | Update health check to use Gemini and current env variables |
| 5 | JWT secret and legacy admin defaults are weak if not overridden | Security risk | Require strong `JWT_SECRET_KEY` and disable default admin credentials in production |
| 6 | Dashboard token is sent as query parameter | Token can appear in logs/history | Use `Authorization: Bearer <token>` header |
| 7 | `CORS_ORIGINS=*` with credentials is not recommended for production | Security and browser compatibility risk | Use explicit frontend origin/domain |
| 8 | Some JSON columns use mutable defaults | Potential ORM state risk | Use callable defaults or SQLAlchemy-safe default factories |

### D.8 Recommended Demonstration Script

The final demonstration can follow this sequence:

1. Start PostgreSQL and initialize the database.
2. Start backend with `uvicorn main:app --reload --host 0.0.0.0 --port 9999`.
3. Start frontend dashboard with `npm run dev` in the `dashboard` directory.
4. Start ngrok or use a production HTTPS domain for the WhatsApp webhook.
5. Verify webhook from Meta using `/webhook/whatsapp`.
6. Send a WhatsApp message such as: "Halo, GPS unit saya tidak update".
7. Show that the bot asks for name and problem details.
8. Show the bot sending KB troubleshooting steps.
9. Reply "belum berhasil" to trigger escalation.
10. Provide unit, location, and time.
11. Confirm ticket creation.
12. Show the created ticket ID from osTicket.
13. Open dashboard and show updated metrics in Overview, Performance, and Insights pages.

---

## References Used for Standards and Technical Alignment

1. RFC Editor. RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format. https://www.rfc-editor.org/rfc/rfc8259
2. RFC Editor. RFC 7519: JSON Web Token (JWT). https://www.rfc-editor.org/rfc/rfc7519.html
3. FastAPI Documentation. Features and automatic interactive API documentation. https://fastapi.tiangolo.com/features/
4. Google AI for Developers. Gemini API `models.generateContent`. https://ai.google.dev/api/generate-content
5. PostgreSQL Documentation. Constraints and relational integrity. https://www.postgresql.org/docs/current/ddl-constraints.html
6. Meta WhatsApp webhook behavior is mapped to the implemented `hub.mode`, `hub.verify_token`, and `hub.challenge` flow in `app/routes/whatsapp.py`, consistent with the WhatsApp Cloud API webhook verification pattern.

