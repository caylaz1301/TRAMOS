"""
PostgreSQL Database Models for TRAMOS WhatsApp Bot
Production-ready schema with proper normalization, relationships, and analytics tracking
Implements multi-turn conversation persistence, ticket history, context tracking, and analytics
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, Index, Float, Date, Numeric, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import json

Base = declarative_base()
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS - Production-Ready
# ============================================================================

class UserRole(str, Enum):
    """User roles for access control (RBAC)"""
    USER = "user"                    # Field staff/driver
    SUPPORT_OPERATOR = "operator"    # Support team
    ANALYST = "analyst"              # Management/Analytics
    ADMIN = "admin"                  # System administrator


class ConversationState(str, Enum):
    """Possible conversation states"""
    NEW_ISSUE = "new_issue"
    ANALYZING = "analyzing"
    COLLECTING_DETAILS = "collecting_details"
    OFFERING_SOLUTIONS = "offering_solutions"
    USER_TRYING = "user_trying"
    ESCALATING = "escalating"
    HUMAN_SUPPORT = "human_support"
    RESOLVED = "resolved"
    CLOSED = "closed"
    IDLE = "idle"


class MessageSender(str, Enum):
    """Who sent the message"""
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Message content types"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    LOCATION = "location"
    AUDIO = "audio"
    VIDEO = "video"


class TicketStatus(str, Enum):
    """osTicket ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"
    PENDING = "pending"


class TicketPriority(str, Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ResolutionType(str, Enum):
    """How issue was resolved"""
    AI_SOLUTION = "ai_solution"           # Resolved by AI chatbot
    OPERATOR_RESOLVED = "operator_resolved"  # Resolved by support operator
    USER_RESOLVED = "user_resolved"       # User resolved on their own
    ESCALATED = "escalated"               # Escalated to higher support


class MetricType(str, Enum):
    """Type of analytics metrics"""
    RESOLUTION_TIME = "resolution_time"
    AI_SUCCESS_RATE = "ai_success_rate"
    TICKET_VOLUME = "ticket_volume"
    CATEGORY_COUNT = "category_count"
    OPERATOR_PERFORMANCE = "operator_performance"
    USER_SATISFACTION = "user_satisfaction"


# ============================================================================
# DATABASE MODELS - Production Schema
# ============================================================================


class DashboardUser(Base):
    """Dashboard user accounts - for login/registration (separate from WhatsApp users)"""
    __tablename__ = "dashboard_users"
    __table_args__ = (
        Index('idx_dash_users_email', 'email'),
        Index('idx_dash_users_google_id', 'google_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Null for Google-only users
    
    # Auth provider
    auth_provider = Column(String(20), default="email")  # email, google
    google_id = Column(String(255), unique=True, nullable=True)
    
    # OTP verification
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    # Role & status
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<DashboardUser email={self.email} verified={self.is_verified}>"


class User(Base):
    """WhatsApp user profile - Core user entity"""
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_users_phone', 'phone_number'),
        Index('idx_users_role', 'role'),
        Index('idx_users_active', 'is_active'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    user_name = Column(String(100))
    role = Column(String(20), default=UserRole.USER.value, nullable=False)  # NEW: user, operator, analyst, admin
    department = Column(String(100))  # NEW: Department/team assignment
    language = Column(String(10), default="id")  # Bahasa Indonesia default
    preferred_language = Column(String(10), default="id")
    is_active = Column(Boolean, default=True)
    
    # Metadata
    first_contact_at = Column(DateTime, default=datetime.utcnow)
    last_contact_at = Column(DateTime)
    total_messages = Column(Integer, default=0)
    total_tickets = Column(Integer, default=0)
    resolved_tickets = Column(Integer, default=0)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")
    resolutions_handled = relationship("Resolution", back_populates="resolved_by_user")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User phone={self.phone_number} role={self.role}>"


class Conversation(Base):
    """Active or completed conversations with users"""
    __tablename__ = "conversations"
    __table_args__ = (
        Index('idx_conversation_phone_state', 'phone_number', 'current_state'),
        Index('idx_conversation_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Conversation state
    current_state = Column(String(50), default=ConversationState.NEW_ISSUE.value)
    category = Column(String(50))  # GPS, Camera, Battery, etc.
    intent = Column(String(50))  # troubleshooting, escalate, resolved, etc.
    
    # Issue details
    issue_description = Column(Text)
    issue_start_time = Column(DateTime)
    
    # Ticket link (set after ticket creation)
    ticket_id = Column(Integer, ForeignKey('tickets.id', use_alter=True), nullable=True)
    
    # Context storage (JSON for flexibility)
    context_data = Column(JSON, default={})
    meta_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("MessageHistory", back_populates="conversation", cascade="all, delete-orphan")
    ticket = relationship("Ticket", back_populates="conversation", foreign_keys="Ticket.conversation_id", uselist=False)

    def __repr__(self):
        return f"<Conversation id={self.id} phone={self.phone_number} state={self.current_state}>"
    
    def get_context(self) -> Dict[str, Any]:
        """Get full context as dict"""
        return self.context_data or {}
    
    def set_context(self, key: str, value: Any):
        """Update specific context field"""
        if self.context_data is None:
            self.context_data = {}
        self.context_data[key] = value
        self.updated_at = datetime.utcnow()


class MessageHistory(Base):
    """All messages in a conversation - Message persistence"""
    __tablename__ = "message_history"
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_phone_created', 'phone_number', 'created_at'),
        Index('idx_message_sender', 'sender'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    # Message content
    sender = Column(String(10), default=MessageSender.USER.value)  # user, bot, system
    message_text = Column(Text, nullable=False)
    message_type = Column(String(20), default=MessageType.TEXT.value)  # NEW: text, image, document, etc
    language = Column(String(10), default="id")
    
    # AI analysis
    intent = Column(String(50))
    category = Column(String(50))
    confidence = Column(Integer, default=0)  # 0-100
    
    # Message metadata
    message_id = Column(String(100), unique=True)  # WhatsApp message ID
    meta_data = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message id={self.id} type={self.message_type} sender={self.sender}>"


class Ticket(Base):
    """osTicket integration - Support ticket tracking"""
    __tablename__ = "tickets"
    __table_args__ = (
        Index('idx_ticket_phone_status', 'phone_number', 'status'),
        Index('idx_ticket_ostid', 'osticket_id'),
        Index('idx_ticket_user_status', 'user_id', 'status'),
        Index('idx_ticket_created_at', 'created_at'),
        UniqueConstraint('osticket_id', name='uq_osticket_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    # osTicket integration
    osticket_id = Column(Integer, unique=True)  # osTicket ticket ID
    osticket_url = Column(String(500))
    
    # Ticket details
    subject = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default=TicketStatus.OPEN.value, nullable=False)
    priority = Column(String(20), default=TicketPriority.MEDIUM.value)
    
    # Conversation link
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    
    # Feedback
    user_satisfaction = Column(Integer)  # 1-5 rating
    feedback_text = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tickets")
    conversation = relationship("Conversation", back_populates="ticket", foreign_keys=[conversation_id], uselist=False)
    resolution = relationship("Resolution", back_populates="ticket", uselist=False)

    def __repr__(self):
        return f"<Ticket id={self.id} osid={self.osticket_id} status={self.status}>"


class Resolution(Base):
    """Ticket resolution tracking - How & when tickets were resolved"""
    __tablename__ = "resolutions"
    __table_args__ = (
        Index('idx_ticket_id', 'ticket_id'),
        Index('idx_resolved_by', 'resolved_by_user_id'),
        Index('idx_resolution_type', 'resolution_type'),
        Index('idx_resolved_at', 'resolved_at'),
        UniqueConstraint('ticket_id', name='uq_ticket_resolution'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False, unique=True)
    
    # Resolution details
    resolution_type = Column(String(20), default=ResolutionType.OPERATOR_RESOLVED.value)
    resolution_notes = Column(Text)
    resolved_by_user_id = Column(Integer, ForeignKey('users.id'))  # Who resolved it (support_operator)
    resolved_at = Column(DateTime, default=datetime.utcnow)
    resolution_time_minutes = Column(Integer)  # Minutes from ticket creation to resolution
    
    # AI tracking
    ai_attempted = Column(Boolean, default=False)  # Whether AI tried to solve
    ai_successful = Column(Boolean, default=False)  # Whether AI solved without escalation
    ai_confidence = Column(Float)  # Final AI confidence score
    
    # Metadata
    meta_data = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="resolution")
    resolved_by_user = relationship("User", back_populates="resolutions_handled", foreign_keys=[resolved_by_user_id])

    def __repr__(self):
        return f"<Resolution ticket_id={self.ticket_id} type={self.resolution_type}>"


class AnalyticsData(Base):
    """Analytics and metrics tracking - System-wide analytics and insights"""
    __tablename__ = "analytics_data"
    __table_args__ = (
        Index('idx_analytics_metric_type', 'metric_type'),
        Index('idx_analytics_category', 'category'),
        Index('idx_analytics_date_recorded', 'date_recorded'),
        Index('idx_analytics_metric_composite', 'metric_type', 'date_recorded'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    ticket_id = Column(Integer, ForeignKey('tickets.id'))
    
    # Metric definition
    metric_type = Column(String(50), nullable=False)  # resolution_time, ai_success_rate, etc
    metric_value = Column(Float, nullable=False)  # Numeric value of metric
    category = Column(String(50), nullable=False)  # Issue category for categorized analytics
    
    # Aggregation fields
    date_recorded = Column(Date, nullable=False)  # Date when metric recorded
    hour_recorded = Column(Integer)  # 0-23, for hourly tracking
    operator_id = Column(Integer, ForeignKey('users.id'))  # For operator performance tracking
    
    # Metadata
    meta_data = Column(JSON, default={})  # Additional context (e.g., comparison_value)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    ticket = relationship("Ticket", foreign_keys=[ticket_id])
    operator = relationship("User", foreign_keys=[operator_id])

    def __repr__(self):
        return f"<Analytic type={self.metric_type} value={self.metric_value} date={self.date_recorded}>"


class ConversationContext(Base):
    """Persist full conversation context for fast retrieval"""
    __tablename__ = "conversation_context"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Full context JSON
    context_data = Column(JSON, default={})
    
    # Cached frequently used fields
    current_state = Column(String(50))
    category = Column(String(50))
    issue_description = Column(Text)
    last_intent = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime)

    def __repr__(self):
        return f"<Context phone={self.phone_number}>"


class ConversationTurn(Base):
    """Detailed turn-by-turn conversation log"""
    __tablename__ = "conversation_turns"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Turn sequence
    turn_number = Column(Integer)  # 1st turn, 2nd turn, etc.
    
    # User input
    user_message = Column(Text)
    user_intent = Column(String(50))
    user_category = Column(String(50))
    user_confidence = Column(Integer)
    
    # Bot response
    bot_response = Column(Text)
    bot_state = Column(String(50))  # State after this turn
    
    # Turn metadata
    processing_time_ms = Column(Integer)  # LLM processing time
    turn_type = Column(String(50))  # greeting, troubleshooting_step, escalation, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Turn id={self.id} num={self.turn_number}>"


class WhatsAppSession(Base):
    """Persist WhatsApp conversation sessions with dialog state"""
    __tablename__ = "whatsapp_sessions"
    __table_args__ = (
        Index('idx_whatsapp_phone_active', 'phone_number', 'is_active'),
        Index('idx_whatsapp_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Dialog Flow State
    current_state = Column(String(50), nullable=False)  # GREETING, COLLECTING_NAME, etc.
    is_active = Column(Boolean, default=True)
    
    # Collected Data
    driver_name = Column(String(100))
    problem_description = Column(Text)
    problem_category = Column(String(50))
    problem_severity = Column(String(20))  # critical, high, medium, low
    vehicle_unit = Column(String(50))
    location = Column(String(200))
    issue_time = Column(String(20))
    
    # Ticket Reference
    ticket_created = Column(Boolean, default=False)
    ticket_id = Column(String(50))
    osticket_id = Column(Integer)
    
    # Conversation Metadata
    message_count = Column(Integer, default=0)
    conversation_history = Column(JSON, default=[])  # Full conversation log
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Session lifecycle
    expires_at = Column(DateTime)  # When session will auto-close (300s timeout)
    closed_at = Column(DateTime)

    def __repr__(self):
        return f"<Session id={self.session_id} phone={self.phone_number} state={self.current_state}>"
    
    def is_expired(self) -> bool:
        """Check if session has exceeded timeout"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for transport"""
        return {
            "session_id": self.session_id,
            "phone_number": self.phone_number,
            "current_state": self.current_state,
            "is_active": self.is_active,
            "driver_name": self.driver_name,
            "problem_description": self.problem_description,
            "problem_category": self.problem_category,
            "problem_severity": self.problem_severity,
            "vehicle_unit": self.vehicle_unit,
            "location": self.location,
            "issue_time": self.issue_time,
            "ticket_created": self.ticket_created,
            "ticket_id": self.ticket_id,
            "osticket_id": self.osticket_id,
            "message_count": self.message_count,
            "conversation_history": self.conversation_history,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class UserProfileData(Base):
    """Persist user profile data for personalization - NEW"""
    __tablename__ = "user_profile_data"
    __table_args__ = (
        Index('idx_user_profile_phone', 'phone_number'),
        Index('idx_profile_updated_at', 'updated_at'),
        UniqueConstraint('phone_number', name='uq_profile_phone'),
    )

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False, unique=True, index=True)
    
    # Skill Level Tracking
    skill_level = Column(String(20), default='newbie')  # newbie, intermediate, advanced, expert
    
    # Device Tracking
    device_type = Column(String(100))  # iPhone, Samsung, etc
    device_specs = Column(JSON, default={})
    
    # Communication Preferences
    time_availability = Column(String(20), default='flexible')  # urgent, short, flexible
    preferred_language = Column(String(10), default='id')
    communication_style = Column(JSON, default={})  # {explanation_depth, technical_terms, detail_level, etc}
    
    # Interaction History
    total_interactions = Column(Integer, default=0)
    completed_issues = Column(Integer, default=0)
    failed_issues = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    avg_satisfaction = Column(Float, default=0.0)
    
    # Frustration Tracking
    is_frustrated = Column(Boolean, default=False)
    frustration_level = Column(Float, default=0.0)  # 0-1 scale
    frustration_keywords_count = Column(Integer, default=0)
    
    # Full Profile JSON
    full_profile = Column(JSON, default={})  # Complete profile serialization
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime)

    def __repr__(self):
        return f"<UserProfile phone={self.phone_number} skill={self.skill_level}>"


class SolutionAttempt(Base):
    """Track every solution attempt with full context - NEW"""
    __tablename__ = "solution_attempts"
    __table_args__ = (
        Index('idx_solution_phone_created', 'phone_number', 'created_at'),
        Index('idx_solution_category', 'category'),
        Index('idx_solution_conversation_id', 'conversation_id'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Solution Identification
    solution_id = Column(String(100), nullable=False)  # Unique ID for the solution
    category = Column(String(50), nullable=False)  # GPS, Camera, Battery, etc
    
    # Solution Details
    problem_description = Column(Text, nullable=False)
    solution_steps = Column(JSON)  # JSON array of solution steps
    kb_match_score = Column(Float)  # Similarity to KB solution (0-1)
    
    # Outcome Tracking
    outcome = Column(String(20))  # worked, partially_worked, failed, abandoned, escalated
    user_feedback = Column(Text)  # User's feedback on solution
    
    # Metrics
    time_to_implement_minutes = Column(Float)  # How long user took to try
    follow_up_attempts = Column(Integer, default=0)  # How many times user asked follow-ups
    escalation_needed = Column(Boolean, default=False)
    
    # Contextual Data
    ai_confidence = Column(Float)  # AI's confidence in solution (0-1)
    user_skill_level = Column(String(20))  # User's skill level when solution was provided
    user_frustration = Column(Float)  # User's frustration level (0-1)
    
    # Metadata
    meta_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime)  # When outcome was recorded
    outcome_recorded_at = Column(DateTime)

    def __repr__(self):
        return f"<SolutionAttempt id={self.id} outcome={self.outcome}>"


class SolutionEffectiveness(Base):
    """Aggregate metrics for solution effectiveness - NEW"""
    __tablename__ = "solution_effectiveness"
    __table_args__ = (
        Index('idx_solution_id', 'solution_id'),
        Index('idx_effectiveness_category', 'category'),
        Index('idx_effectiveness_updated_at', 'updated_at'),
        UniqueConstraint('solution_id', 'category', name='uq_solution_category'),
    )

    id = Column(Integer, primary_key=True)
    solution_id = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    
    # Outcome Counts
    total_attempts = Column(Integer, default=0)
    worked_count = Column(Integer, default=0)
    partially_worked_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    abandoned_count = Column(Integer, default=0)
    escalated_count = Column(Integer, default=0)
    
    # Calculated Metrics
    success_rate = Column(Float, default=0.0)  # (worked + partially_worked) / total
    pure_success_rate = Column(Float, default=0.0)  # worked / total
    escalation_rate = Column(Float, default=0.0)  # escalated / total
    
    # Performance Metrics
    avg_implementation_time = Column(Float)  # Minutes
    avg_ai_confidence = Column(Float)  # When solutions provided
    avg_user_satisfaction = Column(Float)  # Rating 1-5
    
    # Health Scoring
    health_score = Column(Float, default=0.0)  # 0-1, composite of all metrics
    recommendation = Column(String(20))  # excellent, good, okay, needs_review, broken
    
    # Trends
    last_30_days_attempts = Column(Integer, default=0)
    last_30_days_success_rate = Column(Float, default=0.0)
    trending = Column(String(20))  # up, stable, down
    
    # Metadata
    meta_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SolutionEffectiveness id={self.solution_id} success_rate={self.success_rate:.1%}>"



# ============================================================================
# DATABASE INITIALIZATION & MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manages database connections, sessions, and migrations"""
    
    def __init__(self, database_url: str):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection string
                         postgresql://user:password@localhost:5432/tramos_db
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
    
    def init_db(self):
        """Create all tables in the correct order"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ Database tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def get_session(self):
        """Get new database session"""
        return self.SessionLocal()
    
    def drop_all(self):
        """Drop all tables (use with caution in production!)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("⚠️ All tables dropped")
            return True
        except Exception as e:
            logger.error(f"❌ Drop tables failed: {e}")
            return False
    
    def migrate(self, sql_script: str):
        """
        Execute raw SQL migration script
        
        Args:
            sql_script: Raw SQL statements to execute
        """
        from sqlalchemy import text
        with self.engine.connect() as conn:
            try:
                # Split by semicolon and execute each statement
                statements = sql_script.split(';')
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        conn.execute(text(statement))
                conn.commit()
                logger.info("✅ Migration executed successfully")
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Migration failed: {e}")
                return False
    
    def execute_query(self, query: str):
        """Execute raw SQL query"""
        from sqlalchemy import text
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text(query))
                conn.commit()
                return result
            except Exception as e:
                conn.rollback()
                logger.error(f"❌ Query execution failed: {e}")
                return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_or_create_user(session, phone_number: str, user_name: str = None, language: str = "id") -> User:
    """Get existing user or create new one"""
    user = session.query(User).filter_by(phone_number=phone_number).first()
    if not user:
        user = User(
            phone_number=phone_number,
            user_name=user_name,
            language=language,
            preferred_language=language
        )
        session.add(user)
        session.commit()
    return user


def get_active_conversation(session, phone_number: str) -> Optional[Conversation]:
    """Get active (non-closed) conversation for user"""
    return session.query(Conversation).filter(
        Conversation.phone_number == phone_number,
        Conversation.current_state != ConversationState.CLOSED.value
    ).order_by(Conversation.updated_at.desc()).first()


def get_conversation_history(session, phone_number: str, limit: int = 20) -> list:
    """Get recent messages in active conversation"""
    conversation = get_active_conversation(session, phone_number)
    if not conversation:
        return []
    
    return session.query(MessageHistory).filter_by(
        conversation_id=conversation.id
    ).order_by(MessageHistory.created_at.desc()).limit(limit).all()


# ============================================================================
# MIGRATION & SETUP SCRIPTS
# ============================================================================

MIGRATION_CREATE_TABLES = """
-- ============================================================================
-- PRODUCTION-READY SCHEMA FOR TRAMOS WhatsApp Bot
-- ============================================================================

-- Users table (with role-based access control)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    user_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' NOT NULL CHECK (role IN ('user', 'operator', 'analyst', 'admin')),
    department VARCHAR(100),
    language VARCHAR(10) DEFAULT 'id',
    preferred_language VARCHAR(10) DEFAULT 'id',
    is_active BOOLEAN DEFAULT TRUE,
    first_contact_at TIMESTAMP DEFAULT NOW(),
    last_contact_at TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_tickets INTEGER DEFAULT 0,
    resolved_tickets INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);


-- Conversations table (primary conversation history)
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    current_state VARCHAR(50) DEFAULT 'new_issue',
    category VARCHAR(50),
    intent VARCHAR(50),
    issue_description TEXT,
    issue_start_time TIMESTAMP,
    context_data JSONB DEFAULT '{}',
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_phone_state ON conversations(phone_number, current_state);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);


-- Message history table (all messages with type tracking)
CREATE TABLE IF NOT EXISTS message_history (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    sender VARCHAR(10) DEFAULT 'user' CHECK (sender IN ('user', 'bot', 'system')),
    message_text TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'document', 'location', 'audio', 'video')),
    language VARCHAR(10) DEFAULT 'id',
    intent VARCHAR(50),
    category VARCHAR(50),
    confidence INTEGER DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 100),
    message_id VARCHAR(100) UNIQUE,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_message_history_conversation ON message_history(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_message_history_phone ON message_history(phone_number, created_at);
CREATE INDEX IF NOT EXISTS idx_message_sender ON message_history(sender);


-- Tickets table (support ticket management)
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    osticket_id INTEGER UNIQUE,
    osticket_url VARCHAR(500),
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'on_hold', 'resolved', 'closed', 'pending')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
    user_satisfaction INTEGER CHECK (user_satisfaction >= 1 AND user_satisfaction <= 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_phone_status ON tickets(phone_number, status);
CREATE INDEX IF NOT EXISTS idx_tickets_osticket_id ON tickets(osticket_id);
CREATE INDEX IF NOT EXISTS idx_tickets_user_status ON tickets(user_id, status);
CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at);


-- Resolutions table (ticket resolution tracking - NEW)
CREATE TABLE IF NOT EXISTS resolutions (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL UNIQUE REFERENCES tickets(id) ON DELETE CASCADE,
    resolution_type VARCHAR(20) DEFAULT 'operator_resolved' CHECK (resolution_type IN ('ai_solution', 'operator_resolved', 'user_resolved', 'escalated')),
    resolution_notes TEXT,
    resolved_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP DEFAULT NOW(),
    resolution_time_minutes INTEGER,
    ai_attempted BOOLEAN DEFAULT FALSE,
    ai_successful BOOLEAN DEFAULT FALSE,
    ai_confidence FLOAT,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resolutions_ticket ON resolutions(ticket_id);
CREATE INDEX IF NOT EXISTS idx_resolutions_resolved_by ON resolutions(resolved_by_user_id);
CREATE INDEX IF NOT EXISTS idx_resolutions_type ON resolutions(resolution_type);
CREATE INDEX IF NOT EXISTS idx_resolutions_datetime ON resolutions(resolved_at);


-- Analytics data table (system-wide metrics - NEW)
CREATE TABLE IF NOT EXISTS analytics_data (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
    ticket_id INTEGER REFERENCES tickets(id) ON DELETE SET NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    category VARCHAR(50) NOT NULL,
    date_recorded DATE NOT NULL,
    hour_recorded INTEGER CHECK (hour_recorded >= 0 AND hour_recorded <= 23),
    operator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_metric_type ON analytics_data(metric_type);
CREATE INDEX IF NOT EXISTS idx_analytics_category ON analytics_data(category);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics_data(date_recorded);
CREATE INDEX IF NOT EXISTS idx_analytics_composite ON analytics_data(metric_type, date_recorded);


-- Conversation context table (fast context retrieval)
CREATE TABLE IF NOT EXISTS conversation_context (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    context_data JSONB DEFAULT '{}',
    current_state VARCHAR(50),
    category VARCHAR(50),
    issue_description TEXT,
    last_intent VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_accessed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_context_phone ON conversation_context(phone_number);


-- Conversation turns table (detailed turn-by-turn logging)
CREATE TABLE IF NOT EXISTS conversation_turns (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    turn_number INTEGER,
    user_message TEXT,
    user_intent VARCHAR(50),
    user_category VARCHAR(50),
    user_confidence INTEGER,
    bot_response TEXT,
    bot_state VARCHAR(50),
    processing_time_ms INTEGER,
    turn_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_turns_conversation ON conversation_turns(conversation_id);


-- WhatsApp sessions table (dialog state management)
CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    current_state VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    driver_name VARCHAR(100),
    problem_description TEXT,
    problem_category VARCHAR(50),
    problem_severity VARCHAR(20),
    vehicle_unit VARCHAR(50),
    location VARCHAR(200),
    issue_time VARCHAR(20),
    ticket_created BOOLEAN DEFAULT FALSE,
    ticket_id VARCHAR(50),
    osticket_id INTEGER,
    message_count INTEGER DEFAULT 0,
    conversation_history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_phone_active ON whatsapp_sessions(phone_number, is_active);
CREATE INDEX IF NOT EXISTS idx_whatsapp_created ON whatsapp_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_whatsapp_session_id ON whatsapp_sessions(session_id);


-- User profile data table (personalization tracking - NEW)
CREATE TABLE IF NOT EXISTS user_profile_data (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    skill_level VARCHAR(20) DEFAULT 'newbie' CHECK (skill_level IN ('newbie', 'intermediate', 'advanced', 'expert')),
    device_type VARCHAR(100),
    device_specs JSONB DEFAULT '{}',
    time_availability VARCHAR(20) DEFAULT 'flexible' CHECK (time_availability IN ('urgent', 'short', 'flexible')),
    preferred_language VARCHAR(10) DEFAULT 'id',
    communication_style JSONB DEFAULT '{}',
    total_interactions INTEGER DEFAULT 0,
    completed_issues INTEGER DEFAULT 0,
    failed_issues INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    avg_satisfaction FLOAT DEFAULT 0.0,
    is_frustrated BOOLEAN DEFAULT FALSE,
    frustration_level FLOAT DEFAULT 0.0 CHECK (frustration_level >= 0 AND frustration_level <= 1),
    frustration_keywords_count INTEGER DEFAULT 0,
    full_profile JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_interaction TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_profile_phone ON user_profile_data(phone_number);
CREATE INDEX IF NOT EXISTS idx_user_profile_updated ON user_profile_data(updated_at);


-- Solution attempts table (solution tracking - NEW)
CREATE TABLE IF NOT EXISTS solution_attempts (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    phone_number VARCHAR(20) NOT NULL,
    solution_id VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    problem_description TEXT NOT NULL,
    solution_steps JSONB,
    kb_match_score FLOAT CHECK (kb_match_score >= 0 AND kb_match_score <= 1),
    outcome VARCHAR(20) CHECK (outcome IN ('worked', 'partially_worked', 'failed', 'abandoned', 'escalated')),
    user_feedback TEXT,
    time_to_implement_minutes FLOAT,
    follow_up_attempts INTEGER DEFAULT 0,
    escalation_needed BOOLEAN DEFAULT FALSE,
    ai_confidence FLOAT CHECK (ai_confidence >= 0 AND ai_confidence <= 1),
    user_skill_level VARCHAR(20),
    user_frustration FLOAT CHECK (user_frustration >= 0 AND user_frustration <= 1),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    outcome_recorded_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_solution_phone_created ON solution_attempts(phone_number, created_at);
CREATE INDEX IF NOT EXISTS idx_solution_category ON solution_attempts(category);
CREATE INDEX IF NOT EXISTS idx_solution_conversation ON solution_attempts(conversation_id);


-- Solution effectiveness table (aggregated metrics - NEW)
CREATE TABLE IF NOT EXISTS solution_effectiveness (
    id SERIAL PRIMARY KEY,
    solution_id VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    total_attempts INTEGER DEFAULT 0,
    worked_count INTEGER DEFAULT 0,
    partially_worked_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    abandoned_count INTEGER DEFAULT 0,
    escalated_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0 CHECK (success_rate >= 0 AND success_rate <= 1),
    pure_success_rate FLOAT DEFAULT 0.0 CHECK (pure_success_rate >= 0 AND pure_success_rate <= 1),
    escalation_rate FLOAT DEFAULT 0.0 CHECK (escalation_rate >= 0 AND escalation_rate <= 1),
    avg_implementation_time FLOAT,
    avg_ai_confidence FLOAT,
    avg_user_satisfaction FLOAT,
    health_score FLOAT DEFAULT 0.0 CHECK (health_score >= 0 AND health_score <= 1),
    recommendation VARCHAR(20) CHECK (recommendation IN ('excellent', 'good', 'okay', 'needs_review', 'broken')),
    last_30_days_attempts INTEGER DEFAULT 0,
    last_30_days_success_rate FLOAT DEFAULT 0.0,
    trending VARCHAR(20) CHECK (trending IN ('up', 'stable', 'down')),
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(solution_id, category)
);

CREATE INDEX IF NOT EXISTS idx_solution_effectiveness_id ON solution_effectiveness(solution_id);
CREATE INDEX IF NOT EXISTS idx_solution_effectiveness_category ON solution_effectiveness(category);
CREATE INDEX IF NOT EXISTS idx_solution_effectiveness_updated ON solution_effectiveness(updated_at);


-- ============================================================================
-- MATERIALIZED VIEW FOR DASHBOARD ANALYTICS (Optional)
-- ============================================================================

CREATE TABLE IF NOT EXISTS dashboard_analytics_summary (
    id SERIAL PRIMARY KEY,
    summary_date DATE NOT NULL,
    total_conversations INTEGER DEFAULT 0,
    total_tickets_created INTEGER DEFAULT 0,
    avg_resolution_time INTEGER,
    ai_success_rate FLOAT,
    operator_count INTEGER,
    most_common_category VARCHAR(50),
    avg_user_satisfaction FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(summary_date)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_date ON dashboard_analytics_summary(summary_date);
"""

if __name__ == "__main__":
    # Example usage
    db = DatabaseManager("postgresql://user:password@localhost/tramos_db")
    db.init_db()
    print("✅ Database initialized!")
