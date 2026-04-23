# Entity Tables & Relationships with Cardinality

**TRAMOS Database** - Complete Entity-Relationship Documentation  
**Generated**: February 26, 2026

---

## Figure: Entity Tables

```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│       USERS             │    CONVERSATIONS        │    MESSAGE_HISTORY      │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ PK id                   │ PK id                   │ PK id                   │
│    phone_number(U)      │ FK user_id              │ FK conversation_id      │
│    user_name            │    phone_number         │    phone_number         │
│    role(enum)           │    current_state(enum)  │    sender(enum)         │
│    department           │    category             │    message_text         │
│    language             │    intent               │    message_type(enum)   │
│    preferred_language   │    issue_description    │    language             │
│    is_active            │    issue_start_time     │    intent               │
│    first_contact_at     │ FK ticket_id            │    category             │
│    last_contact_at      │    context_data(JSON)   │    confidence(0-100)    │
│    total_messages       │    meta_data(JSON)      │    message_id(U)        │
│    total_tickets        │    created_at, updated  │    meta_data(JSON)      │
│    resolved_tickets     │    last_message_at      │    created_at           │
│    created_at, updated  │                         │                         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
          │                         │                         │
          │1:N                    1:N│                       N:1│
          │                         │                         │
          └─────────────┬───────────┴──────────────┬──────────┘
                        │                          │
        ┌───────────────┴──────────────┐           │
        │                              │           │
┌───────┴─────────────────────────────┴────────────────────────┐
│                      TICKETS                                 │
├──────────────────────────────────────────────────────────────┤
│ PK id                                                        │
│ FK user_id, conversation_id                                  │
│    phone_number                                              │
│    osticket_id (U, Integer)                                  │
│    osticket_url                                              │
│    subject                                                   │
│    description                                               │
│    status (enum)                                             │
│    priority (enum)                                           │
│    category                                                  │
│    user_satisfaction (1-5 rating)                            │
│    feedback_text                                             │
│    created_at, updated_at                                    │
└──────────────────────────────────────────────────────────────┘
    │                 │
    │ 1:1             │
    │              (conversation)
    │                 │
    │        ┌────────────────────────────┐
    │        │  RESOLUTIONS               │
    │        ├────────────────────────────┤
    │        │ PK id                      │
    │        │ FK ticket_id (U)           │
    │        │ FK resolved_by_user_id     │
    │        │    resolution_type(enum)   │
    │        │    resolution_notes        │
    │        │    resolved_at             │
    │        │    resolution_time_minutes │
    │        │    ai_attempted            │
    │        │    ai_successful           │
    │        │    ai_confidence           │
    │        │    meta_data (JSONB)       │
    │        │    created_at, updated_at  │
    │        └────────────────────────────┘

┌────────────────────────────────────────────────────┐
│       CONVERSATION_TURNS                           │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│ FK conversation_id                                 │
│    phone_number                                    │
│    turn_number                                     │
│    user_message                                    │
│    user_intent (VARCHAR 50)                        │
│    user_category (VARCHAR 50)                      │
│    user_confidence                                 │
│    bot_response                                    │
│    bot_state (VARCHAR 50)                          │
│    processing_time_ms                              │
│    turn_type (VARCHAR 50)                          │
│    created_at                                      │
└────────────────────────────────────────────────────┘
              │N:1 (conversation)

┌────────────────────────────────────────────────────┐
│      ANALYTICS_DATA                                │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│ FK conversation_id, ticket_id, operator_id         │
│    metric_type (VARCHAR 50)                        │
│    metric_value (Float)                            │
│    category (VARCHAR 50)                           │
│    date_recorded (Date)                            │
│    hour_recorded (Integer 0-23)                    │
│    meta_data (JSONB)                               │
│    created_at                                      │
└────────────────────────────────────────────────────┘
         │N:1 (to: conversations, tickets, users)

┌────────────────────────────────────────────────────┐
│       SOLUTION_ATTEMPTS                            │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│ FK conversation_id                                 │
│    phone_number (VARCHAR 20)                       │
│    solution_id (VARCHAR 100)                       │
│    category (VARCHAR 50)                           │
│    problem_description (Text)                      │
│    solution_steps (JSON)                           │
│    kb_match_score (Float)                          │
│    outcome (varchar:worked|partially_worked|...)   │
│    user_feedback (Text)                            │
│    time_to_implement_minutes (Float)               │
│    follow_up_attempts (Integer)                    │
│    escalation_needed (Boolean)                     │
│    ai_confidence (Float)                           │
│    user_skill_level (VARCHAR 20)                   │
│    user_frustration (Float 0-1)                    │
│    meta_data (JSON)                                │
│    created_at, updated_at                          │
│    outcome_recorded_at (Timestamp)                 │
└────────────────────────────────────────────────────┘
         │N:1 (conversation)

---

### Standalone Entities (No Foreign Key)

┌────────────────────────────────────────────────────┐
│      CONVERSATION_CONTEXT  [Standalone]            │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│    phone_number (U, VARCHAR 20)                    │
│    context_data (JSON)                             │
│    current_state (VARCHAR 50)                      │
│    category (VARCHAR 50)                           │
│    issue_description                               │
│    last_intent (VARCHAR 50)                        │
│    created_at, updated_at, last_accessed_at        │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│       WHATSAPP_SESSIONS  [Standalone]              │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│    session_id (U, VARCHAR 100)                     │
│    phone_number (VARCHAR 20)                       │
│    current_state (VARCHAR 50)                      │
│    is_active (Boolean)                             │
│    driver_name (VARCHAR 100)                       │
│    problem_description (Text)                      │
│    problem_category (VARCHAR 50)                   │
│    problem_severity (VARCHAR 20)                   │
│    vehicle_unit (VARCHAR 50)                       │
│    location (VARCHAR 200)                          │
│    issue_time (VARCHAR 20)                         │
│    ticket_created (Boolean, default false)         │
│    ticket_id (VARCHAR 50), osticket_id (Integer)   │
│    message_count (Integer, default 0)              │
│    conversation_history (JSON, default [])         │
│    created_at, updated_at                          │
│    last_activity, expires_at, closed_at            │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│       USER_PROFILE_DATA  [Standalone]              │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│    phone_number (U, VARCHAR 20)                    │
│    skill_level (enum:newbie|intermediate|...|expert)│
│    device_type (VARCHAR 100)                       │
│    device_specs (JSON)                             │
│    time_availability (enum:urgent|short|flexible)  │
│    preferred_language (VARCHAR 10)                 │
│    communication_style (JSON)                      │
│    total_interactions (Integer)                    │
│    completed_issues, failed_issues (Integer)       │
│    success_rate (Float)                            │
│    avg_satisfaction (Float)                        │
│    is_frustrated (Boolean)                         │
│    frustration_level (Float 0-1)                   │
│    frustration_keywords_count (Integer)            │
│    full_profile (JSON)                             │
│    created_at, updated_at                          │
│    last_interaction (Timestamp)                    │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│     SOLUTION_EFFECTIVENESS  [Standalone]           │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│    solution_id (U with category, VARCHAR 100)      │
│    category (VARCHAR 50)                           │
│    total_attempts (Integer)                        │
│    worked_count, partially_worked_count (Integer)  │
│    failed_count, abandoned_count (Integer)         │
│    escalated_count (Integer)                       │
│    success_rate, pure_success_rate (Float)         │
│    escalation_rate (Float)                         │
│    avg_implementation_time (Float)                 │
│    avg_ai_confidence (Float)                       │
│    avg_user_satisfaction (Float)                   │
│    health_score (Float)                            │
│    recommendation (VARCHAR 20)                     │
│    last_30_days_attempts (Integer)                 │
│    last_30_days_success_rate (Float)               │
│    trending (VARCHAR 20)                           │
│    meta_data (JSON)                                │
│    created_at, updated_at                          │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  DASHBOARD_ANALYTICS_SUMMARY  [Standalone]         │
├────────────────────────────────────────────────────┤
│ PK id                                              │
│    summary_date (Date, U)                          │
│    total_conversations (Integer, default 0)        │
│    total_tickets_created (Integer, default 0)      │
│    avg_resolution_time (Integer)                   │
│    ai_success_rate (Float)                         │
│    operator_count (Integer)                        │
│    most_common_category (VARCHAR 50)               │
│    avg_user_satisfaction (Float)                   │
│    created_at                                      │
└────────────────────────────────────────────────────┘
```

---

## Relations with Cardinality of Each Relation

> **Total: 12 Foreign Key constraints** verified directly from PostgreSQL database.  
> 11 distinct relationships (Conversation ↔ Ticket is bidirectional with 2 FK constraints).  
> 5 standalone entities have no foreign key constraints.

---

### A. FK-Based Relationships (11 Relationships, 12 FK Constraints)

---

### i. User → Conversation (1:N)

- **FK Constraint**: `conversations.user_id` → `users.id`
- **Cardinality**: One-to-Many (1:N) — One user can have many conversations
- **Nullable**: No (mandatory)
- **Explanation**: One user can initiate and participate in many conversations with the support system. Each conversation belongs to exactly one user, established through the `user_id` foreign key.
- **Example**: User "Budi Santoso" (+6281234567890) has 3 conversations:
  - Conversation #101: "GPS tidak bisa connect" (2026-02-20)
  - Conversation #102: "Kamera mati total" (2026-02-22)
  - Conversation #103: "Baterai device habis terus" (2026-02-25)
- **Database Implementation**: 
  - `conversations.user_id (FK NOT NULL)` → `users.id (PK)`
  - Index: `idx_conversation_phone_state` (phone_number, current_state)
  - Constraint: `conversations_user_id_fkey`

---

### ii. User → Ticket (1:N)

- **FK Constraint**: `tickets.user_id` → `users.id`
- **Cardinality**: One-to-Many (1:N) — One user can create many tickets
- **Nullable**: No (mandatory)
- **Explanation**: One user can create and submit many support tickets, but each ticket is created by exactly one user. This tracks the original reporter of the issue.
- **Example**: User "Budi Santoso" created:
  - Ticket #201: "[GPS] GPS tidak bisa connect - B 7821"
  - Ticket #202: "[Camera] Kamera mati total - B 7821"
  - Ticket #203: "[Battery] Baterai device habis terus - B 7821"
- **Database Implementation**:
  - `tickets.user_id (FK NOT NULL)` → `users.id (PK)`
  - Index: `idx_ticket_phone_status` (phone_number, status)
  - Index: `idx_ticket_user_status` (user_id, status)
  - Constraint: `tickets_user_id_fkey`

---

### iii. User → Resolution (1:N)

- **FK Constraint**: `resolutions.resolved_by_user_id` → `users.id`
- **Cardinality**: One-to-Many (1:N) — One operator can resolve many tickets
- **Nullable**: Yes (NULL when resolved by AI or user themselves)
- **Explanation**: One user with role='operator' can resolve many tickets. Each resolution is optionally handled by one operator. The `resolved_by_user_id` is NULL when the issue is resolved by the AI chatbot or the user themselves.
- **Example**: Operator "Ahmad Maulana" (user_id=5) resolved:
  - Ticket #201: resolution_type="ai_solution", resolved_by_user_id=NULL → AI solved it
  - Ticket #202: resolution_type="operator_resolved", resolved_by_user_id=5 → Operator handled
  - Ticket #203: resolution_type="escalated", resolved_by_user_id=5 → Escalated and resolved
- **Database Implementation**:
  - `resolutions.resolved_by_user_id (FK, NULLABLE)` → `users.id (PK)`
  - Index: `idx_resolved_by` (resolved_by_user_id)
  - Constraint: `resolutions_resolved_by_user_id_fkey`

---

### iv. User → Analytics_Data (1:N) via operator_id

- **FK Constraint**: `analytics_data.operator_id` → `users.id`
- **Cardinality**: One-to-Many (1:N) — One user (operator) can have many analytics records
- **Nullable**: Yes (NULL when metric is not operator-specific)
- **Explanation**: The `analytics_data` table has an `operator_id` foreign key that references `users.id`. This is used when `metric_type='operator_performance'` to track which operator (user with role='operator') is associated with the analytics record. The FK points to the `users` table — there is no separate "operators" table. When the metric is system-wide (e.g., category_count, ticket_volume), `operator_id` is NULL.
- **Example**: User "Ahmad Maulana" (user_id=5, role='operator') has analytics:
  - Metric: metric_type="operator_performance", metric_value=45, operator_id=5, category="GPS"
  - Metric: metric_type="user_satisfaction", metric_value=4.7, operator_id=5, date_recorded=2026-02-20
  - Metric: metric_type="ticket_volume", metric_value=3.0, operator_id=NULL → system-wide, not operator-specific
- **Database Implementation**:
  - `analytics_data.operator_id (FK, NULLABLE)` → `users.id (PK)`
  - Column name is `operator_id` but references the `users` table
  - Constraint: `analytics_data_operator_id_fkey`

---

### v. Conversation → Message_History (1:N)

- **FK Constraint**: `message_history.conversation_id` → `conversations.id`
- **Cardinality**: One-to-Many (1:N) — One conversation has many messages
- **Nullable**: No (mandatory)
- **Explanation**: One conversation consists of many messages exchanged between the user and the AI bot. Each message belongs to exactly one conversation. Messages are the atomic units of conversation activity, ordered chronologically by `created_at`.
- **Example**: Conversation #101 "GPS tidak bisa connect" contains:
  - Message #1001 (user): "Halo, GPS saya tidak bisa connect"
  - Message #1002 (bot): "Selamat datang di TRAMOS! Siapa nama Anda?"
  - Message #1003 (user): "Budi Santoso"
  - Message #1004 (bot): "Terima kasih Budi. Apa masalah yang Anda alami?"
  - Message #1005 (user): "GPS di unit B 7821 tidak connect sejak pagi"
  - Message #1006 (bot): "Baik, coba restart GPS module..."
- **Database Implementation**:
  - `message_history.conversation_id (FK NOT NULL)` → `conversations.id (PK)`
  - Index: `idx_conversation_created` (conversation_id, created_at)
  - Index: `idx_phone_created` (phone_number, created_at)
  - Constraint: `message_history_conversation_id_fkey`

---

### vi. Conversation ↔ Ticket (1:1, Bidirectional)

- **FK Constraints**: 
  - `tickets.conversation_id` → `conversations.id`
  - `conversations.ticket_id` → `tickets.id`
- **Cardinality**: One-to-One (1:1) — Bidirectional with 2 FK constraints
- **Nullable**: Yes (not all conversations result in tickets)
- **Explanation**: One conversation can result in at most one support ticket, and each ticket originates from exactly one conversation. Not all conversations create tickets — only those where the AI chatbot cannot resolve the issue and escalation is required. This bidirectional relationship uses 2 FK constraints: `tickets.conversation_id` links from ticket to conversation, and `conversations.ticket_id` links back from conversation to ticket (set after ticket creation).
- **Example**: 
  - Conversation #101 escalates → Ticket #201 (osticket_id: 45823)
  - Conversation #102 escalates → Ticket #202 (osticket_id: 45824)
  - Conversation #103 resolved by AI → No ticket (ticket_id=NULL)
- **Database Implementation**:
  - `tickets.conversation_id (FK, NULLABLE)` → `conversations.id (PK)` — Constraint: `tickets_conversation_id_fkey`
  - `conversations.ticket_id (FK, NULLABLE)` → `tickets.id (PK)` — Constraint: `conversations_ticket_id_fkey`
  - UniqueConstraint on `tickets.osticket_id`

---

### vii. Conversation → Conversation_Turn (1:N)

- **FK Constraint**: `conversation_turns.conversation_id` → `conversations.id`
- **Cardinality**: One-to-Many (1:N) — One conversation has many turns
- **Nullable**: No (mandatory)
- **Explanation**: One conversation consists of many turns where each turn is one exchange (user message → bot response). Each turn belongs to exactly one conversation. Turns preserve sequential order (`turn_number`), intents, categories, processing time, and bot state for detailed conversation analytics.
- **Example**: Conversation #101 has 4 turns:
  - Turn #1: user_message="Halo", bot_state="GREETING", turn_type="greeting", processing_time_ms=120
  - Turn #2: user_message="Budi Santoso", bot_state="COLLECTING_NAME", user_intent="provide_name", processing_time_ms=85
  - Turn #3: user_message="GPS tidak connect", bot_state="COLLECTING_PROBLEM", user_category="GPS", processing_time_ms=1250
  - Turn #4: user_message="Ya, sudah berhasil", bot_state="CLOSED", turn_type="resolution", processing_time_ms=95
- **Database Implementation**:
  - `conversation_turns.conversation_id (FK NOT NULL)` → `conversations.id (PK)`
  - Constraint: `conversation_turns_conversation_id_fkey`

---

### viii. Conversation → Solution_Attempt (1:N)

- **FK Constraint**: `solution_attempts.conversation_id` → `conversations.id`
- **Cardinality**: One-to-Many (1:N) — One conversation can have many solution attempts
- **Nullable**: No (mandatory)
- **Explanation**: One conversation can have many solution attempts as the bot suggests multiple solutions to resolve the issue. Each solution attempt tracks the solution_id, KB match score, user's skill level, frustration, outcome, and implementation time. Results are saved for learning and effectiveness analysis.
- **Example**: Conversation #101 attempted 2 solutions:
  - Attempt #401: solution_id="gps_restart_01", kb_match_score=0.92, outcome="failed", time_to_implement_minutes=5.5
  - Attempt #402: solution_id="gps_firmware_update_01", kb_match_score=0.78, outcome="worked", time_to_implement_minutes=12.0, ai_confidence=0.87
- **Database Implementation**:
  - `solution_attempts.conversation_id (FK NOT NULL)` → `conversations.id (PK)`
  - Index: `idx_solution_phone_created` (phone_number, created_at)
  - Constraint: `solution_attempts_conversation_id_fkey`

---

### ix. Conversation → Analytics_Data (1:N)

- **FK Constraint**: `analytics_data.conversation_id` → `conversations.id`
- **Cardinality**: One-to-Many (1:N) — One conversation generates many analytics records
- **Nullable**: Yes (some analytics are not conversation-specific)
- **Explanation**: One conversation generates multiple analytics data points tracking conversation-level metrics such as message count, bot performance, user satisfaction, resolution times, and category-based metrics. Analytics are recorded with date and hour granularity for trend analysis.
- **Example**: Conversation #101 generates:
  - Metric: metric_type="resolution_time", metric_value=13.0, category="GPS", hour_recorded=9
  - Metric: metric_type="ai_success_rate", metric_value=1.0, category="GPS", date_recorded=2026-02-20
  - Metric: metric_type="category_count", metric_value=1.0, category="GPS", date_recorded=2026-02-20
- **Database Implementation**:
  - `analytics_data.conversation_id (FK, NULLABLE)` → `conversations.id (PK)`
  - Index: `idx_analytics_metric_composite` (metric_type, date_recorded)
  - Constraint: `analytics_data_conversation_id_fkey`

---

### x. Ticket → Resolution (1:1)

- **FK Constraint**: `resolutions.ticket_id` → `tickets.id` (UNIQUE)
- **Cardinality**: One-to-One (1:1) — One ticket has exactly one resolution
- **Nullable**: No (mandatory)
- **Explanation**: One ticket has exactly one resolution record that tracks how the issue was resolved, who resolved it, resolution type, resolution time, and AI involvement metrics. Each resolution corresponds to exactly one ticket. The UNIQUE constraint on `ticket_id` enforces this 1:1 relationship.
- **Example**:
  - Ticket #201 → Resolution: resolution_type="ai_solution", ai_attempted=true, ai_successful=true, ai_confidence=0.87, resolution_time_minutes=13
  - Ticket #202 → Resolution: resolution_type="operator_resolved", ai_attempted=true, ai_successful=false, resolved_by_user_id=5, resolution_time_minutes=150
- **Database Implementation**:
  - `resolutions.ticket_id (FK NOT NULL, UNIQUE)` → `tickets.id (PK)`
  - UniqueConstraint: `uq_ticket_resolution` — enforces 1:1
  - Constraint: `resolutions_ticket_id_fkey`

---

### xi. Ticket → Analytics_Data (1:N)

- **FK Constraint**: `analytics_data.ticket_id` → `tickets.id`
- **Cardinality**: One-to-Many (1:N) — One ticket generates many analytics records
- **Nullable**: Yes (some analytics are not ticket-specific)
- **Explanation**: One ticket generates multiple analytics data points tracked across different metric types, categories, dates, and hours. Analytics aggregates metrics for reporting and dashboard purposes including resolution time, AI success rate, and ticket volume.
- **Example**: Ticket #201 contributes to analytics:
  - Metric: metric_type="resolution_time", metric_value=13.0, date_recorded=2026-02-20, category="GPS"
  - Metric: metric_type="ai_success_rate", metric_value=1.0, category="GPS", date_recorded=2026-02-20
  - Metric: metric_type="ticket_volume", metric_value=1.0, category="GPS", date_recorded=2026-02-20
- **Database Implementation**:
  - `analytics_data.ticket_id (FK, NULLABLE)` → `tickets.id (PK)`
  - Constraint: `analytics_data_ticket_id_fkey`

---

### B. Standalone Entities — No Foreign Key Constraints (5 Tables)

> These tables have **no FK constraints** in the database.  
> They are linked to other tables via `phone_number` matching or application logic only.

---

### xii. Conversation_Context (Standalone — phone_number lookup)

- **FK Constraint**: None
- **Logical Link**: Linked to `users` and `conversations` via `phone_number` (no FK)
- **Explanation**: Each phone number has one context record that maintains the current conversation state, category, issue description, and recent intent for continuity. The `context_data` (JSON) stores full conversation metadata. This is a denormalized cache entity with indexed `phone_number` for fast retrieval and state management during active conversations.
- **Example**: Context for phone +6281234567890:
  - phone_number: "6281234567890", current_state: "offering_solutions"
  - category: "GPS", issue_description: "GPS tidak bisa connect sejak pagi"
  - last_intent: "troubleshooting"
  - context_data: {"driver_name": "Budi Santoso", "vehicle_unit": "B 7821", "location": "Tol Cikampek KM 45"}
- **Database Implementation**:
  - `conversation_context.phone_number` (UNIQUE) — lookup key, no FK to users
  - Index: `idx_user_profile_phone` on phone_number

---

### xiii. WhatsApp_Sessions (Standalone — phone_number lookup)

- **FK Constraint**: None
- **Logical Link**: Linked to users via `phone_number` (no FK). `ticket_id` is VARCHAR(50), not a FK.
- **Explanation**: WhatsApp sessions track active dialog flow sessions for guided issue reporting. Sessions are independent entities that reference `phone_number` for multi-session tracking. They store all collected data step-by-step (driver name, problem, vehicle unit, location, time) and manage session lifecycle with timeout (300s) and closure timestamps.
- **Example**: 
  - Session #801: Driver "Budi Santoso" vehicle "B 7821" reports "GPS tidak bisa connect" (severity: high, state: COLLECTING_PROBLEM) — active
  - Session #802: Driver "Edo Pratama" vehicle "B 3456" reports "Kamera depan mati" (severity: medium, state: CLOSED) — ticket_created=true, osticket_id=45824
- **Database Implementation**:
  - `whatsapp_sessions.session_id` (UNIQUE) — e.g., "session_6281234567890_1708412100"
  - `whatsapp_sessions.phone_number` — reference only, no FK to users
  - `whatsapp_sessions.ticket_id` — VARCHAR(50), not a FK to tickets table
  - Index: `idx_whatsapp_phone_active` (phone_number, is_active)

---

### xiv. User_Profile_Data (Standalone — phone_number lookup)

- **FK Constraint**: None
- **Logical Link**: Linked to `users` via `phone_number` (no FK)
- **Explanation**: One user has one extended profile record (matched by phone_number) containing advanced personalization and skill tracking data. Extends users with skill_level, device information, frustration metrics, communication preferences, and success tracking for AI adaptation.
- **Example**: User "Budi Santoso" (6281234567890) profile:
  - skill_level: "intermediate", device_type: "Samsung Galaxy A14"
  - time_availability: "flexible", total_interactions: 12
  - completed_issues: 9, failed_issues: 2, success_rate: 0.75
  - is_frustrated: false, frustration_level: 0.15
- **Database Implementation**:
  - `user_profile_data.phone_number` (UNIQUE) — matched to users.phone_number, no FK
  - UniqueConstraint: `uq_profile_phone`

---

### xv. Solution_Effectiveness (Standalone — aggregation entity)

- **FK Constraint**: None
- **Logical Link**: Aggregated from `solution_attempts` via application logic (matching `solution_id` + `category`), not via FK
- **Explanation**: Aggregate metrics for each solution per category. Tracks total attempts, outcome counts (worked/partially_worked/failed/abandoned/escalated), success rates, implementation times, health scoring, and trending. One record per unique (solution_id, category) combination. Updated by application code, not by database FK cascade.
- **Example**: Solution "Restart GPS Module" (gps_restart_01) for category="GPS":
  - total_attempts: 48, worked_count: 35, partially_worked_count: 5
  - failed_count: 4, abandoned_count: 2, escalated_count: 2
  - success_rate: 0.83, pure_success_rate: 0.73, health_score: 0.82
  - trending: "up" (last 30 days improving)
- **Database Implementation**:
  - UniqueConstraint on (`solution_id`, `category`) — `uq_solution_category`
  - No FK to solution_attempts — aggregation via application logic only
  - Index: `idx_solution_id`, `idx_effectiveness_category`

---

### xvi. Dashboard_Analytics_Summary (Standalone — daily aggregation)

- **FK Constraint**: None
- **Logical Link**: Pre-computed from conversations, tickets, resolutions, and analytics_data tables via application-level cron/batch job
- **Explanation**: Pre-computed daily summary of system-wide metrics. Each record aggregates one day of data including total conversations, tickets created, average resolution time, AI success rate, and the most common issue category. This denormalized table eliminates expensive real-time aggregation queries when rendering the analytics dashboard.
- **Example**: Summary for 2026-02-20:
  - total_conversations: 23, total_tickets_created: 8
  - avg_resolution_time: 18 minutes, ai_success_rate: 0.72
  - operator_count: 3, most_common_category: "GPS", avg_user_satisfaction: 4.0
- **Database Implementation**:
  - `dashboard_analytics_summary.summary_date` (UNIQUE) — one record per day
  - No FK to any other table

---

## Cardinality Summary Table

### A. FK-Based Relationships (Verified from PostgreSQL)

| # | Relationship | Cardinality | Nullable | FK Constraint Name | Key |
|---|---|---|---|---|---|
| 1 | User → Conversation | 1:N | No | `conversations_user_id_fkey` | conversations.user_id → users.id |
| 2 | User → Ticket | 1:N | No | `tickets_user_id_fkey` | tickets.user_id → users.id |
| 3 | User → Resolution | 1:N | Yes | `resolutions_resolved_by_user_id_fkey` | resolutions.resolved_by_user_id → users.id |
| 4 | User → Analytics_Data | 1:N | Yes | `analytics_data_operator_id_fkey` | analytics_data.operator_id → users.id |
| 5 | Conversation → Message_History | 1:N | No | `message_history_conversation_id_fkey` | message_history.conversation_id → conversations.id |
| 6a | Conversation → Ticket | 1:1 | Yes | `tickets_conversation_id_fkey` | tickets.conversation_id → conversations.id |
| 6b | Ticket → Conversation | 1:1 | Yes | `conversations_ticket_id_fkey` | conversations.ticket_id → tickets.id |
| 7 | Conversation → Turn | 1:N | No | `conversation_turns_conversation_id_fkey` | conversation_turns.conversation_id → conversations.id |
| 8 | Conversation → Solution_Attempt | 1:N | No | `solution_attempts_conversation_id_fkey` | solution_attempts.conversation_id → conversations.id |
| 9 | Conversation → Analytics_Data | 1:N | Yes | `analytics_data_conversation_id_fkey` | analytics_data.conversation_id → conversations.id |
| 10 | Ticket → Resolution | 1:1 | No | `resolutions_ticket_id_fkey` | resolutions.ticket_id (UNIQUE) → tickets.id |
| 11 | Ticket → Analytics_Data | 1:N | Yes | `analytics_data_ticket_id_fkey` | analytics_data.ticket_id → tickets.id |

### B. Standalone Entities (No FK)

| # | Entity | Link Method | Linked To |
|---|---|---|---|
| 12 | conversation_context | phone_number (UNIQUE) | users, conversations (app logic) |
| 13 | whatsapp_sessions | phone_number | users (app logic) |
| 14 | user_profile_data | phone_number (UNIQUE) | users (app logic) |
| 15 | solution_effectiveness | solution_id + category (UNIQUE) | solution_attempts (app logic) |
| 16 | dashboard_analytics_summary | summary_date (UNIQUE) | None (standalone aggregation) |

---

## Normalization Status

✅ **Database is in 3NF (Third Normal Form)**

- No transitive dependencies
- All non-key attributes depend entirely on primary key
- No partial dependencies
- 12 proper foreign key constraints for referential integrity
- Unique constraints on natural identifiers (phone_number, osticket_id, session_id, summary_date)

---

## Key Features

| Feature | Tables | Purpose |
|---------|--------|---------|
| **State Management** | conversations, tickets, whatsapp_sessions | Control workflow and process states via ENUM types |
| **Audit Trail** | All tables | created_at, updated_at timestamps on all entities |
| **Performance Cache** | conversation_context | Denormalized cache for fast retrieval during conversations |
| **Analytics Aggregation** | analytics_data, dashboard_analytics_summary | Time-series metrics by date, category, operator for reporting |
| **Knowledge Base** | solution_attempts, solution_effectiveness | Effectiveness tracking of all suggested solutions |
| **Extended Profiling** | user_profile_data | Personalization data for skill tracking, frustration detection |
| **AI Integration** | message_history, conversation_turns, solution_attempts, resolutions | Tracks all AI interactions, confidence scores, and results |
| **osTicket Integration** | tickets | Synchronized with external osTicket helpdesk via osticket_id |

---

**Last Updated**: February 26, 2026  
**Status**: Ready for Form 2 ✅  
**Verified**: 12 FK constraints queried directly from PostgreSQL database  
**Format**: Production-Ready Database Documentation
