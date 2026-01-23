"""
PostgreSQL Database Models for TRAMOS WhatsApp Bot
Implements multi-turn conversation persistence, ticket history, and context tracking
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import json

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

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


class TicketStatus(str, Enum):
    """osTicket ticket status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    PENDING = "pending"


# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(Base):
    """WhatsApp user profile"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    user_name = Column(String(100))
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User phone={self.phone_number} name={self.user_name}>"


class Conversation(Base):
    """Active or completed conversations with users"""
    __tablename__ = "conversations"
    __table_args__ = (
        Index('idx_phone_state', 'phone_number', 'current_state'),
        Index('idx_created_at', 'created_at'),
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
    
    # Ticket reference
    ticket_id = Column(Integer, ForeignKey('tickets.id'))
    
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
    ticket = relationship("Ticket", back_populates="conversation")

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
    """All messages in a conversation"""
    __tablename__ = "message_history"
    __table_args__ = (
        Index('idx_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_phone_created', 'phone_number', 'created_at'),
    )

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # Message content
    sender = Column(String(10), default=MessageSender.USER.value)  # user, bot, system
    message_text = Column(Text, nullable=False)
    language = Column(String(10), default="id")
    
    # AI analysis
    intent = Column(String(50))
    category = Column(String(50))
    confidence = Column(Integer, default=0)  # 0-100
    
    # Message metadata
    message_id = Column(String(100))  # WhatsApp message ID
    meta_data = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message id={self.id} from={self.sender} text={self.message_text[:50]}...>"


class Ticket(Base):
    """osTicket integration - track support tickets"""
    __tablename__ = "tickets"
    __table_args__ = (
        Index('idx_phone_status', 'phone_number', 'status'),
        Index('idx_ostid', 'osticket_id'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phone_number = Column(String(20), nullable=False, index=True)
    
    # osTicket integration
    osticket_id = Column(Integer, unique=True)  # osTicket ticket ID
    osticket_url = Column(String(500))
    
    # Ticket details
    subject = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    status = Column(String(20), default=TicketStatus.OPEN.value)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Conversation link
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    
    # Resolution tracking
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    resolution_time_minutes = Column(Integer)  # time from creation to resolution
    
    # Feedback
    user_satisfaction = Column(Integer)  # 1-5 rating
    feedback_text = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tickets")
    conversation = relationship("Conversation", back_populates="ticket", uselist=False)

    def __repr__(self):
        return f"<Ticket id={self.id} osid={self.osticket_id} status={self.status}>"


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


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection string
                         postgresql://user:password@localhost/tramos_db
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
    
    def init_db(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print("✅ Database tables initialized")
    
    def get_session(self):
        """Get new database session"""
        return self.SessionLocal()
    
    def drop_all(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
        print("⚠️  All tables dropped")


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
# MIGRATION HELPERS
# ============================================================================

MIGRATION_CREATE_TABLES = """
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    user_name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'id',
    preferred_language VARCHAR(10) DEFAULT 'id',
    is_active BOOLEAN DEFAULT TRUE,
    first_contact_at TIMESTAMP DEFAULT NOW(),
    last_contact_at TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_tickets INTEGER DEFAULT 0,
    resolved_tickets INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(phone_number)
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);


-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    phone_number VARCHAR(20) NOT NULL,
    current_state VARCHAR(50) DEFAULT 'new_issue',
    category VARCHAR(50),
    intent VARCHAR(50),
    issue_description TEXT,
    issue_start_time TIMESTAMP,
    ticket_id INTEGER,
    context_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_phone_state ON conversations(phone_number, current_state);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON conversations(created_at);


-- Message history table
CREATE TABLE IF NOT EXISTS message_history (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    phone_number VARCHAR(20) NOT NULL,
    sender VARCHAR(10) DEFAULT 'user',
    message_text TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'id',
    intent VARCHAR(50),
    category VARCHAR(50),
    confidence INTEGER DEFAULT 0,
    message_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_message_history_conversation ON message_history(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_message_history_phone ON message_history(phone_number, created_at);


-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    phone_number VARCHAR(20) NOT NULL,
    osticket_id INTEGER UNIQUE,
    osticket_url VARCHAR(500),
    subject VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'normal',
    conversation_id INTEGER REFERENCES conversations(id),
    resolution_notes TEXT,
    resolved_at TIMESTAMP,
    resolution_time_minutes INTEGER,
    user_satisfaction INTEGER,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tickets_phone_status ON tickets(phone_number, status);
CREATE INDEX IF NOT EXISTS idx_tickets_osticket_id ON tickets(osticket_id);


-- Conversation context table
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


-- Conversation turns table (detailed logs)
CREATE TABLE IF NOT EXISTS conversation_turns (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
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
"""

if __name__ == "__main__":
    # Example usage
    db = DatabaseManager("postgresql://user:password@localhost/tramos_db")
    db.init_db()
    print("✅ Database initialized!")
