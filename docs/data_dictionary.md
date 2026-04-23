# C.3.b Data Dictionary

The Data Dictionary provides detailed metadata for all database entities in the TRAMOS WhatsApp-Based Issue Reporting System. Each table lists all fields with their data types, constraints, descriptions, and example values.

---

## Table 1: users

**Description:** Stores registered WhatsApp user profiles with role-based access control (RBAC). Each user is identified by their unique phone number and can have roles such as user (driver/field staff), operator (support team), analyst (management), or admin (system administrator).

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each user | 1 |
| 2 | phone_number | VARCHAR | 20 | UNIQUE, NOT NULL | WhatsApp phone number (e.g., 6281234567890) | 6281234567890 |
| 3 | user_name | VARCHAR | 100 | NULL | Display name of the user (driver name) | Budi Santoso |
| 4 | role | VARCHAR | 20 | NOT NULL, DEFAULT 'user' | User role: 'user', 'operator', 'analyst', 'admin' | user |
| 5 | department | VARCHAR | 100 | NULL | Department or team assignment within the organization | Fleet Operations |
| 6 | language | VARCHAR | 10 | NULL, DEFAULT 'id' | Detected language of the user | id |
| 7 | preferred_language | VARCHAR | 10 | NULL, DEFAULT 'id' | User's preferred language for communication | id |
| 8 | is_active | BOOLEAN | - | NULL, DEFAULT TRUE | Whether the user account is currently active | true |
| 9 | first_contact_at | TIMESTAMP | - | NULL | Timestamp of the user's first interaction with the system | 2026-01-15 08:30:00 |
| 10 | last_contact_at | TIMESTAMP | - | NULL | Timestamp of the user's most recent interaction | 2026-02-20 14:22:00 |
| 11 | total_messages | INTEGER | - | NULL, DEFAULT 0 | Total number of messages sent by this user | 47 |
| 12 | total_tickets | INTEGER | - | NULL, DEFAULT 0 | Total number of support tickets created by this user | 5 |
| 13 | resolved_tickets | INTEGER | - | NULL, DEFAULT 0 | Number of tickets that have been resolved for this user | 4 |
| 14 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record creation timestamp | 2026-01-15 08:30:00 |
| 15 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record last update timestamp | 2026-02-20 14:22:00 |

---

## Table 2: conversations

**Description:** Tracks active and completed WhatsApp conversations between users and the chatbot. Each conversation belongs to a specific user and progresses through various states (new_issue, analyzing, collecting_details, offering_solutions, resolved, closed, etc.).

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each conversation | 101 |
| 2 | user_id | INTEGER | - | FK → users.id, NOT NULL | Reference to the user who owns this conversation | 1 |
| 3 | phone_number | VARCHAR | 20 | NOT NULL, INDEX | WhatsApp phone number of the user | 6281234567890 |
| 4 | current_state | VARCHAR | 50 | NULL, DEFAULT 'new_issue' | Current state of the conversation (e.g., new_issue, analyzing, resolved, closed) | collecting_details |
| 5 | category | VARCHAR | 50 | NULL | Issue category (e.g., GPS, Camera, Battery, Network) | GPS |
| 6 | intent | VARCHAR | 50 | NULL | Detected user intent (e.g., troubleshooting, escalate, resolved) | troubleshooting |
| 7 | issue_description | TEXT | - | NULL | Full description of the reported issue | GPS tidak bisa connect di unit B 7821 |
| 8 | issue_start_time | TIMESTAMP | - | NULL | When the issue was first reported by the user | 2026-02-20 09:15:00 |
| 9 | ticket_id | INTEGER | - | FK → tickets.id, NULL | Reference to the associated support ticket (set after ticket creation) | 201 |
| 10 | context_data | JSON | - | NULL, DEFAULT '{}' | Flexible JSON storage for conversation context data | {"step": 3, "retries": 0} |
| 11 | meta_data | JSON | - | NULL, DEFAULT '{}' | Additional metadata in JSON format | {"source": "whatsapp"} |
| 12 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW(), INDEX | Conversation creation timestamp | 2026-02-20 09:15:00 |
| 13 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Last update timestamp | 2026-02-20 09:32:00 |
| 14 | last_message_at | TIMESTAMP | - | NULL | Timestamp of the last message in this conversation | 2026-02-20 09:32:00 |

---

## Table 3: message_history

**Description:** Stores every individual message exchanged within conversations. This includes user messages, bot responses, and system notifications. Each message is linked to its parent conversation and includes AI analysis metadata such as detected intent, category, and confidence score.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each message | 1001 |
| 2 | conversation_id | INTEGER | - | FK → conversations.id, NOT NULL | Reference to the parent conversation | 101 |
| 3 | phone_number | VARCHAR | 20 | NOT NULL | WhatsApp phone number of the sender/receiver | 6281234567890 |
| 4 | sender | VARCHAR | 10 | NULL, DEFAULT 'user' | Who sent the message: 'user', 'bot', or 'system' | user |
| 5 | message_text | TEXT | - | NOT NULL | The actual text content of the message | GPS saya tidak bisa connect |
| 6 | message_type | VARCHAR | 20 | NULL, DEFAULT 'text' | Type of message content: 'text', 'image', 'document', 'location', 'audio', 'video' | text |
| 7 | language | VARCHAR | 10 | NULL, DEFAULT 'id' | Detected language of the message | id |
| 8 | intent | VARCHAR | 50 | NULL | AI-detected intent of the message | troubleshooting |
| 9 | category | VARCHAR | 50 | NULL | AI-detected issue category | GPS |
| 10 | confidence | INTEGER | - | NULL, DEFAULT 0 | AI confidence score (0–100) | 85 |
| 11 | message_id | VARCHAR | 100 | UNIQUE, NULL | WhatsApp message ID for deduplication | wamid.HBgNNjI4MTIzNDU2Nzg5 |
| 12 | meta_data | JSON | - | NULL, DEFAULT '{}' | Additional metadata in JSON format | {"processed": true} |
| 13 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Message timestamp | 2026-02-20 09:16:30 |

---

## Table 4: tickets

**Description:** Manages support tickets created through the WhatsApp chatbot and synchronized with the osTicket helpdesk system. Each ticket is linked to a user and optionally to a conversation. Tracks ticket lifecycle from creation through resolution.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each ticket | 201 |
| 2 | user_id | INTEGER | - | FK → users.id, NOT NULL | Reference to the user who created the ticket | 1 |
| 3 | phone_number | VARCHAR | 20 | NOT NULL | WhatsApp phone number of the ticket creator | 6281234567890 |
| 4 | osticket_id | INTEGER | - | UNIQUE, NULL | External osTicket system ticket ID | 45823 |
| 5 | osticket_url | VARCHAR | 500 | NULL | URL to the ticket in the osTicket web interface | https://support.andakara.com/scp/tickets.php?id=45823 |
| 6 | subject | VARCHAR | 200 | NOT NULL | Ticket subject/title | [GPS] GPS tidak bisa connect - B 7821 |
| 7 | description | TEXT | - | NULL | Detailed description of the issue | Driver Budi melaporkan GPS tidak connect sejak pagi di unit B 7821, lokasi Tol Cikampek KM 45 |
| 8 | category | VARCHAR | 50 | NULL | Issue category (e.g., GPS, Camera, Battery) | GPS |
| 9 | status | VARCHAR | 20 | NULL, DEFAULT 'open' | Ticket status: 'open', 'in_progress', 'on_hold', 'resolved', 'closed', 'pending' | open |
| 10 | priority | VARCHAR | 20 | NULL, DEFAULT 'medium' | Priority level: 'low', 'medium', 'high', 'critical' | high |
| 11 | conversation_id | INTEGER | - | FK → conversations.id, NULL | Reference to the originating conversation | 101 |
| 12 | resolution_notes | TEXT | - | NULL | Notes about how the ticket was resolved | GPS module di-restart oleh teknisi lapangan |
| 13 | resolved_at | TIMESTAMP | - | NULL | Timestamp when the ticket was resolved | 2026-02-20 11:45:00 |
| 14 | resolution_time_minutes | INTEGER | - | NULL | Total time from creation to resolution in minutes | 150 |
| 15 | user_satisfaction | INTEGER | - | NULL | User satisfaction rating (1–5 scale) | 4 |
| 16 | feedback_text | TEXT | - | NULL | User's textual feedback about the resolution | Terima kasih, GPS sudah normal kembali |
| 17 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Ticket creation timestamp | 2026-02-20 09:30:00 |
| 18 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Last update timestamp | 2026-02-20 11:45:00 |

---

## Table 5: resolutions

**Description:** Records detailed resolution information for each ticket. Each ticket can have at most one resolution record (1:1 relationship enforced by UNIQUE constraint). Tracks how the issue was resolved (AI, operator, user, or escalation), timing, and AI performance metrics.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each resolution | 301 |
| 2 | ticket_id | INTEGER | - | FK → tickets.id, NOT NULL, UNIQUE | Reference to the resolved ticket (one resolution per ticket) | 201 |
| 3 | resolution_type | VARCHAR | 20 | NULL, DEFAULT 'operator_resolved' | How the issue was resolved: 'ai_solution', 'operator_resolved', 'user_resolved', 'escalated' | ai_solution |
| 4 | resolution_notes | TEXT | - | NULL | Detailed notes about the resolution process | AI menyarankan restart GPS module, user konfirmasi berhasil |
| 5 | resolved_by_user_id | INTEGER | - | FK → users.id, NULL | Reference to the operator who resolved the ticket | NULL |
| 6 | resolved_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Timestamp of the resolution | 2026-02-20 09:28:00 |
| 7 | resolution_time_minutes | INTEGER | - | NULL | Total resolution time in minutes | 13 |
| 8 | ai_attempted | BOOLEAN | - | NULL, DEFAULT FALSE | Whether the AI chatbot attempted to resolve the issue | true |
| 9 | ai_successful | BOOLEAN | - | NULL, DEFAULT FALSE | Whether the AI chatbot successfully resolved the issue | true |
| 10 | ai_confidence | DOUBLE PRECISION | - | NULL | AI's confidence score in the solution provided | 0.87 |
| 11 | meta_data | JSONB | - | NULL, DEFAULT '{}' | Additional metadata in JSON format | {"solution_id": "gps_restart_01"} |
| 12 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record creation timestamp | 2026-02-20 09:28:00 |
| 13 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record last update timestamp | 2026-02-20 09:28:00 |

---

## Table 6: analytics_data

**Description:** Stores system-wide analytics metrics for reporting and dashboard purposes. Each record represents a single metric measurement (e.g., resolution time, AI success rate, ticket volume) linked to a specific date, category, and optionally to a conversation, ticket, or operator.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each analytics record | 501 |
| 2 | conversation_id | INTEGER | - | FK → conversations.id, NULL | Reference to the related conversation (if applicable) | 101 |
| 3 | ticket_id | INTEGER | - | FK → tickets.id, NULL | Reference to the related ticket (if applicable) | 201 |
| 4 | metric_type | VARCHAR | 50 | NOT NULL | Type of metric: 'resolution_time', 'ai_success_rate', 'ticket_volume', 'category_count', 'operator_performance', 'user_satisfaction' | resolution_time |
| 5 | metric_value | DOUBLE PRECISION | - | NOT NULL | Numeric value of the metric | 13.0 |
| 6 | category | VARCHAR | 50 | NOT NULL | Issue category this metric belongs to | GPS |
| 7 | date_recorded | DATE | - | NOT NULL | Date when the metric was recorded | 2026-02-20 |
| 8 | hour_recorded | INTEGER | - | NULL | Hour of the day (0–23) for hourly tracking | 9 |
| 9 | operator_id | INTEGER | - | FK → users.id, NULL | Reference to the operator for performance tracking | 5 |
| 10 | meta_data | JSONB | - | NULL, DEFAULT '{}' | Additional context data in JSON format | {"unit": "minutes"} |
| 11 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record creation timestamp | 2026-02-20 09:28:00 |

---

## Table 7: conversation_context

**Description:** Provides fast retrieval of the current conversation context for each phone number. Stores a cached copy of the active conversation state, category, and issue description to avoid repeated full conversation lookups. One record per phone number.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each context record | 601 |
| 2 | phone_number | VARCHAR | 20 | UNIQUE, NOT NULL, INDEX | WhatsApp phone number (one context per phone number) | 6281234567890 |
| 3 | context_data | JSON | - | NULL, DEFAULT '{}' | Full conversation context stored as JSON | {"driver_name": "Budi", "unit": "B 7821"} |
| 4 | current_state | VARCHAR | 50 | NULL | Cached current conversation state | collecting_details |
| 5 | category | VARCHAR | 50 | NULL | Cached issue category | GPS |
| 6 | issue_description | TEXT | - | NULL | Cached issue description | GPS tidak bisa connect |
| 7 | last_intent | VARCHAR | 50 | NULL | Most recently detected user intent | troubleshooting |
| 8 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record creation timestamp | 2026-02-20 09:15:00 |
| 9 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record last update timestamp | 2026-02-20 09:20:00 |
| 10 | last_accessed_at | TIMESTAMP | - | NULL | Last time this context was accessed | 2026-02-20 09:22:00 |

---

## Table 8: conversation_turns

**Description:** Records detailed turn-by-turn interaction logs within each conversation. Each turn captures the user's message, the bot's response, AI analysis results, and processing performance metrics. Enables granular analysis of conversation quality and AI performance.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each turn | 701 |
| 2 | conversation_id | INTEGER | - | FK → conversations.id, NOT NULL | Reference to the parent conversation | 101 |
| 3 | phone_number | VARCHAR | 20 | NOT NULL, INDEX | WhatsApp phone number | 6281234567890 |
| 4 | turn_number | INTEGER | - | NULL | Sequential number of the turn in the conversation (1st, 2nd, etc.) | 3 |
| 5 | user_message | TEXT | - | NULL | The user's message in this turn | GPS saya tidak bisa connect |
| 6 | user_intent | VARCHAR | 50 | NULL | AI-detected intent from the user's message | troubleshooting |
| 7 | user_category | VARCHAR | 50 | NULL | AI-detected issue category from the user's message | GPS |
| 8 | user_confidence | INTEGER | - | NULL | AI confidence in intent/category detection (0–100) | 85 |
| 9 | bot_response | TEXT | - | NULL | The chatbot's response in this turn | Baik, coba restart GPS module di unit Anda... |
| 10 | bot_state | VARCHAR | 50 | NULL | Conversation state after this turn was processed | offering_solutions |
| 11 | processing_time_ms | INTEGER | - | NULL | Time taken to process this turn in milliseconds | 1250 |
| 12 | turn_type | VARCHAR | 50 | NULL | Classification of the turn: 'greeting', 'troubleshooting_step', 'escalation', etc. | troubleshooting_step |
| 13 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Turn timestamp | 2026-02-20 09:18:00 |

---

## Table 9: whatsapp_sessions

**Description:** Persists the state of active WhatsApp dialog flow sessions. Stores all collected data during the guided issue reporting process (driver name, problem description, vehicle unit, location, time). Manages session lifecycle including creation, timeout, and closure.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each session record | 801 |
| 2 | session_id | VARCHAR | 100 | UNIQUE, NOT NULL, INDEX | Unique session identifier string | session_6281234567890_1708412100 |
| 3 | phone_number | VARCHAR | 20 | NOT NULL, INDEX | WhatsApp phone number | 6281234567890 |
| 4 | current_state | VARCHAR | 50 | NOT NULL | Current dialog flow state (e.g., GREETING, COLLECTING_NAME, COLLECTING_PROBLEM, CONFIRMING_DETAILS, CLOSED) | COLLECTING_PROBLEM |
| 5 | is_active | BOOLEAN | - | NULL, DEFAULT TRUE | Whether the session is currently active | true |
| 6 | driver_name | VARCHAR | 100 | NULL | Name of the driver/user collected during the dialog | Budi Santoso |
| 7 | problem_description | TEXT | - | NULL | Description of the problem reported by the user | GPS tidak bisa connect sejak pagi |
| 8 | problem_category | VARCHAR | 50 | NULL | AI-detected category of the problem | GPS |
| 9 | problem_severity | VARCHAR | 20 | NULL | Severity level of the problem: 'critical', 'high', 'medium', 'low' | high |
| 10 | vehicle_unit | VARCHAR | 50 | NULL | Vehicle unit/fleet number reported by the user | B 7821 |
| 11 | location | VARCHAR | 200 | NULL | Location where the issue occurred | Tol Cikampek KM 45 |
| 12 | issue_time | VARCHAR | 20 | NULL | Time when the issue occurred (as reported by user) | 08:00 |
| 13 | ticket_created | BOOLEAN | - | NULL, DEFAULT FALSE | Whether a support ticket has been created for this session | false |
| 14 | ticket_id | VARCHAR | 50 | NULL | Internal ticket ID reference | 201 |
| 15 | osticket_id | INTEGER | - | NULL | External osTicket system ticket ID | 45823 |
| 16 | message_count | INTEGER | - | NULL, DEFAULT 0 | Total number of messages exchanged in this session | 6 |
| 17 | conversation_history | JSON | - | NULL, DEFAULT '[]' | Full conversation history stored as JSON array | [{"sender": "user", "text": "Halo"}, ...] |
| 18 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW(), INDEX | Session creation timestamp | 2026-02-20 09:15:00 |
| 19 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Last update timestamp | 2026-02-20 09:25:00 |
| 20 | last_activity | TIMESTAMP | - | NULL, DEFAULT NOW() | Timestamp of the last user activity | 2026-02-20 09:25:00 |
| 21 | expires_at | TIMESTAMP | - | NULL | When the session will automatically expire (300s timeout) | 2026-02-20 09:30:00 |
| 22 | closed_at | TIMESTAMP | - | NULL | Timestamp when the session was closed | NULL |

---

## Table 10: user_profile_data

**Description:** Stores personalization and behavioral profiling data for each user. Tracks skill level, interaction history, success rates, and frustration indicators to enable adaptive chatbot responses. One profile per phone number.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each profile | 901 |
| 2 | phone_number | VARCHAR | 20 | UNIQUE, NOT NULL, INDEX | WhatsApp phone number (one profile per user) | 6281234567890 |
| 3 | skill_level | VARCHAR | 20 | NULL, DEFAULT 'newbie' | User's technical skill level: 'newbie', 'intermediate', 'advanced', 'expert' | intermediate |
| 4 | device_type | VARCHAR | 100 | NULL | Type of device used by the user | Samsung Galaxy A14 |
| 5 | device_specs | JSON | - | NULL, DEFAULT '{}' | Detailed device specifications in JSON format | {"os": "Android 13", "ram": "4GB"} |
| 6 | time_availability | VARCHAR | 20 | NULL, DEFAULT 'flexible' | User's time availability: 'urgent', 'short', 'flexible' | flexible |
| 7 | preferred_language | VARCHAR | 10 | NULL, DEFAULT 'id' | Preferred language for communication | id |
| 8 | communication_style | JSON | - | NULL, DEFAULT '{}' | Communication preferences (explanation depth, technical terms, detail level) | {"detail_level": "simple"} |
| 9 | total_interactions | INTEGER | - | NULL, DEFAULT 0 | Total number of interactions/sessions | 12 |
| 10 | completed_issues | INTEGER | - | NULL, DEFAULT 0 | Number of successfully resolved issues | 9 |
| 11 | failed_issues | INTEGER | - | NULL, DEFAULT 0 | Number of issues that failed to resolve | 2 |
| 12 | success_rate | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Ratio of completed to total issues | 0.75 |
| 13 | avg_satisfaction | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Average satisfaction rating across all interactions | 4.2 |
| 14 | is_frustrated | BOOLEAN | - | NULL, DEFAULT FALSE | Whether the user is currently flagged as frustrated | false |
| 15 | frustration_level | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Frustration level on a 0–1 scale | 0.15 |
| 16 | frustration_keywords_count | INTEGER | - | NULL, DEFAULT 0 | Number of frustration-indicating keywords detected | 1 |
| 17 | full_profile | JSON | - | NULL, DEFAULT '{}' | Complete serialized user profile in JSON format | {"skill": "intermediate", "interactions": 12, ...} |
| 18 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Profile creation timestamp | 2026-01-15 08:30:00 |
| 19 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Profile last update timestamp | 2026-02-20 09:30:00 |
| 20 | last_interaction | TIMESTAMP | - | NULL | Timestamp of the user's most recent interaction | 2026-02-20 09:30:00 |

---

## Table 11: solution_attempts

**Description:** Tracks every solution attempt made during troubleshooting conversations. Records the solution offered, problem context, knowledge base match score, user feedback, and outcome (worked, partially worked, failed, abandoned, escalated). Enables analysis of solution effectiveness.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each solution attempt | 401 |
| 2 | conversation_id | INTEGER | - | FK → conversations.id, NOT NULL | Reference to the parent conversation | 101 |
| 3 | phone_number | VARCHAR | 20 | NOT NULL, INDEX | WhatsApp phone number | 6281234567890 |
| 4 | solution_id | VARCHAR | 100 | NOT NULL | Unique identifier for the solution from the knowledge base | gps_restart_01 |
| 5 | category | VARCHAR | 50 | NOT NULL | Issue category (e.g., GPS, Camera, Battery) | GPS |
| 6 | problem_description | TEXT | - | NOT NULL | Description of the problem being solved | GPS tidak bisa connect sejak pagi |
| 7 | solution_steps | JSON | - | NULL | JSON array of step-by-step solution instructions | ["Buka Settings", "Tap GPS", "Turn off lalu on"] |
| 8 | kb_match_score | DOUBLE PRECISION | - | NULL | Similarity score between the problem and the KB solution (0–1) | 0.92 |
| 9 | outcome | VARCHAR | 20 | NULL | Result of the attempt: 'worked', 'partially_worked', 'failed', 'abandoned', 'escalated' | worked |
| 10 | user_feedback | TEXT | - | NULL | User's textual feedback about the solution | Ya, GPS sudah normal sekarang |
| 11 | time_to_implement_minutes | DOUBLE PRECISION | - | NULL | Time taken by the user to implement the solution in minutes | 5.5 |
| 12 | follow_up_attempts | INTEGER | - | NULL, DEFAULT 0 | Number of follow-up questions asked by the user | 1 |
| 13 | escalation_needed | BOOLEAN | - | NULL, DEFAULT FALSE | Whether the issue required escalation to human support | false |
| 14 | ai_confidence | DOUBLE PRECISION | - | NULL | AI's confidence in the provided solution (0–1) | 0.87 |
| 15 | user_skill_level | VARCHAR | 20 | NULL | User's skill level at the time the solution was offered | intermediate |
| 16 | user_frustration | DOUBLE PRECISION | - | NULL | User's frustration level at the time (0–1) | 0.20 |
| 17 | meta_data | JSON | - | NULL, DEFAULT '{}' | Additional metadata in JSON format | {"kb_version": "2.1"} |
| 18 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Solution attempt creation timestamp | 2026-02-20 09:20:00 |
| 19 | updated_at | TIMESTAMP | - | NULL | Timestamp when the outcome was updated | 2026-02-20 09:27:00 |
| 20 | outcome_recorded_at | TIMESTAMP | - | NULL | Timestamp when the outcome was specifically recorded | 2026-02-20 09:27:00 |

---

## Table 12: solution_effectiveness

**Description:** Aggregated metrics table that tracks the overall effectiveness of each solution across all attempts. Provides success rates, escalation rates, health scores, and trend analysis. Used for knowledge base optimization and dashboard reporting. One record per unique (solution_id, category) pair.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each effectiveness record | 1101 |
| 2 | solution_id | VARCHAR | 100 | NOT NULL | Unique identifier of the solution | gps_restart_01 |
| 3 | category | VARCHAR | 50 | NOT NULL | Issue category for this solution | GPS |
| 4 | total_attempts | INTEGER | - | NULL, DEFAULT 0 | Total number of times this solution was attempted | 48 |
| 5 | worked_count | INTEGER | - | NULL, DEFAULT 0 | Number of attempts where the solution fully worked | 35 |
| 6 | partially_worked_count | INTEGER | - | NULL, DEFAULT 0 | Number of attempts where the solution partially worked | 5 |
| 7 | failed_count | INTEGER | - | NULL, DEFAULT 0 | Number of attempts where the solution failed | 4 |
| 8 | abandoned_count | INTEGER | - | NULL, DEFAULT 0 | Number of attempts that were abandoned by the user | 2 |
| 9 | escalated_count | INTEGER | - | NULL, DEFAULT 0 | Number of attempts that required escalation | 2 |
| 10 | success_rate | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Combined success rate: (worked + partially_worked) / total | 0.83 |
| 11 | pure_success_rate | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Pure success rate: worked / total | 0.73 |
| 12 | escalation_rate | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Rate of escalation: escalated / total | 0.04 |
| 13 | avg_implementation_time | DOUBLE PRECISION | - | NULL | Average time to implement the solution in minutes | 6.2 |
| 14 | avg_ai_confidence | DOUBLE PRECISION | - | NULL | Average AI confidence when providing this solution | 0.85 |
| 15 | avg_user_satisfaction | DOUBLE PRECISION | - | NULL | Average user satisfaction rating (1–5) | 4.1 |
| 16 | health_score | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Composite health score (0–1) based on all metrics | 0.82 |
| 17 | recommendation | VARCHAR | 20 | NULL | Solution recommendation status: 'excellent', 'good', 'okay', 'needs_review', 'broken' | good |
| 18 | last_30_days_attempts | INTEGER | - | NULL, DEFAULT 0 | Number of attempts in the last 30 days | 12 |
| 19 | last_30_days_success_rate | DOUBLE PRECISION | - | NULL, DEFAULT 0.0 | Success rate in the last 30 days | 0.90 |
| 20 | trending | VARCHAR | 20 | NULL | Trend direction: 'up', 'stable', 'down' | up |
| 21 | meta_data | JSON | - | NULL, DEFAULT '{}' | Additional metadata in JSON format | {"last_review": "2026-02-15"} |
| 22 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record creation timestamp | 2026-01-20 00:00:00 |
| 23 | updated_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record last update timestamp | 2026-02-20 09:28:00 |

**Unique Constraint:** (solution_id, category) — ensures one effectiveness record per solution per category.

---

## Table 13: dashboard_analytics_summary

**Description:** Pre-aggregated daily summary table used to power the analytics dashboard. Each record represents one day of system-wide metrics including total conversations, tickets created, average resolution time, AI success rate, and the most common issue category. Avoids expensive real-time aggregation queries.

| No | Field Name | Data Type | Size | Constraint | Description | Example |
|----|-----------|-----------|------|------------|-------------|---------|
| 1 | id | INTEGER | - | PK, NOT NULL, AUTO INCREMENT | Unique identifier for each summary record | 1201 |
| 2 | summary_date | DATE | - | NOT NULL, UNIQUE | The date this summary represents (one record per day) | 2026-02-20 |
| 3 | total_conversations | INTEGER | - | NULL, DEFAULT 0 | Total number of conversations on this date | 23 |
| 4 | total_tickets_created | INTEGER | - | NULL, DEFAULT 0 | Total number of tickets created on this date | 8 |
| 5 | avg_resolution_time | INTEGER | - | NULL | Average ticket resolution time in minutes | 18 |
| 6 | ai_success_rate | DOUBLE PRECISION | - | NULL | AI chatbot success rate for the day (0–1) | 0.72 |
| 7 | operator_count | INTEGER | - | NULL | Number of active support operators on this date | 3 |
| 8 | most_common_category | VARCHAR | 50 | NULL | The most frequently reported issue category | GPS |
| 9 | avg_user_satisfaction | DOUBLE PRECISION | - | NULL | Average user satisfaction rating for the day | 4.0 |
| 10 | created_at | TIMESTAMP | - | NULL, DEFAULT NOW() | Record creation timestamp | 2026-02-20 23:59:00 |
