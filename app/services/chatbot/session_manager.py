"""
Session Management for WhatsApp Conversations
Handles dialog flow state, timeout logic, and session lifecycle with PostgreSQL persistence
"""

import logging
import time
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database_models import WhatsAppSession, Base

logger = logging.getLogger(__name__)

# Session timeout: 5 minutes (300 seconds)
SESSION_TIMEOUT = 300


class DialogState(Enum):
    """Conversation flow states"""
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


class ConversationSession:
    """Represents a single conversation session"""
    
    def __init__(self, phone_number: str, session_id: str):
        self.phone_number = phone_number
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # Dialog state
        self.current_state = DialogState.GREETING
        self.message_count = 0
        
        # Collected data
        self.driver_name: Optional[str] = None
        self.problem_description: Optional[str] = None
        self.problem_category: Optional[str] = None
        self.problem_severity: str = "medium"  # Default severity
        self.vehicle_unit: Optional[str] = None
        self.location: Optional[str] = None
        self.issue_time: Optional[str] = None
        
        # KB Solution tracking
        self.kb_solution: Optional[dict] = None
        self.solution_step_current = 0
        self.solution_worked = False  # True = user solved it, False = need ticket
        self.tried_kb_solution = False  # Whether user was offered KB solution
        
        # Metadata
        self.conversation_history: list = []
        self.ticket_created = False
        self.ticket_id: Optional[str] = None
        self.ticket_retry_count: int = 0  # Track retry attempts untuk escape hatch
        
        # Database tracking IDs (recovered via get_or_create on cache miss)
        self._db_conversation_id: Optional[int] = None
        self._db_solution_attempt_id: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if session has exceeded timeout"""
        time_diff = (datetime.now() - self.last_activity).total_seconds()
        return time_diff > SESSION_TIMEOUT
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_message(self, sender: str, message: str, intent: str = None, category: str = None):
        """Log message to conversation history"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "sender": sender,  # "user" or "bot"
            "message": message,
            "intent": intent,
            "category": category
        })
        self.message_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "phone_number": self.phone_number,
            "current_state": self.current_state.value,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "driver_name": self.driver_name,
            "problem_description": self.problem_description,
            "problem_category": self.problem_category,
            "vehicle_unit": self.vehicle_unit,
            "location": self.location,
            "issue_time": self.issue_time,
            "ticket_created": self.ticket_created,
            "ticket_id": self.ticket_id,
            "conversation_history": self.conversation_history
        }


class SessionManager:
    """Manage conversation sessions with PostgreSQL persistence"""
    
    def __init__(self, db_session_maker=None):
        """Initialize with database session factory"""
        self.db_session = db_session_maker
        self.sessions: Dict[str, ConversationSession] = {}  # In-memory cache
    
    def create_session(self, phone_number: str) -> ConversationSession:
        """Create new conversation session"""
        session_id = f"{phone_number}_{time.time_ns()}"
        session = ConversationSession(phone_number, session_id)
        
        # Save to database
        if self.db_session:
            db = None
            try:
                db = self.db_session()
                expires_at = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
                
                db_session = WhatsAppSession(
                    session_id=session_id,
                    phone_number=phone_number,
                    current_state=session.current_state.value,
                    is_active=True,
                    expires_at=expires_at
                )
                db.add(db_session)
                db.commit()
            except Exception as e:
                logger.error(f"❌ Error creating session in DB: {e}")
            finally:
                if db:
                    db.close()
        
        # Cache in memory
        self.sessions[phone_number] = session
        logger.info(f"📱 Session created: {session_id} for {phone_number}")
        
        return session
    
    def get_session(self, phone_number: str) -> Optional[ConversationSession]:
        """Get existing session from memory or DB"""
        
        # Check memory cache first
        session = self.sessions.get(phone_number)
        
        if session and session.is_expired():
            logger.info(f"⏰ Session expired: {session.session_id}")
            self.close_session(phone_number)
            return None
        
        if session:
            return session
        
        # Try to load from database
        if self.db_session:
            db = None
            try:
                db = self.db_session()
                db_session = db.query(WhatsAppSession).filter(
                    WhatsAppSession.phone_number == phone_number,
                    WhatsAppSession.is_active == True
                ).order_by(WhatsAppSession.created_at.desc()).first()
                
                if db_session and not self._is_db_session_expired(db_session):
                    session = self._restore_session_from_db(db_session)
                    self.sessions[phone_number] = session
                    return session
            except Exception as e:
                logger.error(f"❌ Error loading session from DB: {e}")
            finally:
                if db:
                    db.close()
        
        return None
    
    def get_or_create_session(self, phone_number: str) -> ConversationSession:
        """Get existing session or create new one - optimized"""
        session = self.get_session(phone_number)
        if session is None:
            session = self.create_session(phone_number)
        else:
            session.update_activity()
        
        return session
    
    def close_session(self, phone_number: str):
        """Close and remove session"""
        session = self.sessions.pop(phone_number, None)
        
        # Mark as inactive in DB
        if self.db_session:
            db = None
            try:
                db = self.db_session()
                db_session = db.query(WhatsAppSession).filter_by(
                    phone_number=phone_number
                ).first()
                if db_session:
                    db_session.is_active = False
                    db_session.closed_at = datetime.now()
                    db.commit()
            except Exception as e:
                logger.error(f"❌ Error closing session in DB: {e}")
            finally:
                if db:
                    db.close()
        
        if session:
            logger.info(f"❌ Session closed: {session.session_id}")
            return session
        return None
    
    def save_session(self, session: ConversationSession):
        """Save session data to database"""
        if not self.db_session:
            return
        
        db = None
        try:
            db = self.db_session()
            db_session = db.query(WhatsAppSession).filter_by(
                session_id=session.session_id
            ).first()
            
            if db_session:
                db_session.current_state = session.current_state.value
                db_session.driver_name = session.driver_name
                db_session.problem_description = session.problem_description
                db_session.problem_category = session.problem_category
                db_session.problem_severity = getattr(session, 'problem_severity', None)
                db_session.vehicle_unit = session.vehicle_unit
                db_session.location = session.location
                db_session.issue_time = session.issue_time
                db_session.message_count = session.message_count
                db_session.conversation_history = session.conversation_history
                db_session.ticket_created = session.ticket_created
                db_session.ticket_id = session.ticket_id
                if session.ticket_id:
                    try:
                        db_session.osticket_id = int(session.ticket_id)
                    except (ValueError, TypeError):
                        pass
                db_session.last_activity = datetime.now()
                db_session.expires_at = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
                
                db.commit()
        except Exception as e:
            logger.error(f"❌ Error saving session to DB: {e}")
        finally:
            if db:
                db.close()
    
    def _update_session_in_db(self, session: ConversationSession):
        """Update only activity timestamp in DB"""
        if not self.db_session:
            return
        
        try:
            db = self.db_session()
            db_session = db.query(WhatsAppSession).filter_by(
                session_id=session.session_id
            ).first()
            
            if db_session:
                db_session.last_activity = datetime.now()
                db_session.expires_at = datetime.now() + timedelta(seconds=SESSION_TIMEOUT)
                db.commit()
            
            db.close()
        except Exception as e:
            logger.error(f"❌ Error updating session activity in DB: {e}")
    
    def _is_db_session_expired(self, db_session) -> bool:
        """Check if database session has expired"""
        if db_session.expires_at:
            return datetime.now() > db_session.expires_at
        return False
    
    def _restore_session_from_db(self, db_session) -> Optional[ConversationSession]:
        """Rekonstruksi ConversationSession dari database model"""
        try:
            session = ConversationSession(db_session.phone_number, db_session.session_id)
            session.current_state = DialogState(db_session.current_state)
            session.driver_name = db_session.driver_name
            session.problem_description = db_session.problem_description
            session.problem_category = db_session.problem_category
            # FIX: problem_severity tidak pernah di-restore dari DB
            # Menyebabkan session continuity bermasalah setelah server restart
            session.problem_severity = db_session.problem_severity or "medium"
            session.vehicle_unit = db_session.vehicle_unit
            session.location = db_session.location
            session.issue_time = db_session.issue_time
            session.message_count = db_session.message_count
            session.conversation_history = db_session.conversation_history or []
            session.ticket_created = db_session.ticket_created
            session.ticket_id = db_session.ticket_id
            session.last_activity = db_session.last_activity or datetime.now()

            return session
        except Exception as e:
            logger.error(f"Error restoring session from DB: {e}")
            return None
    
    def get_session_stats(self, phone_number: str) -> Dict[str, Any]:
        """Get session statistics"""
        session = self.sessions.get(phone_number)
        if not session:
            return {}
        
        duration = (session.last_activity - session.created_at).total_seconds()
        
        return {
            "session_id": session.session_id,
            "duration_seconds": duration,
            "message_count": session.message_count,
            "current_state": session.current_state.value,
            "data_collected": {
                "name": bool(session.driver_name),
                "problem": bool(session.problem_description),
                "unit": bool(session.vehicle_unit),
                "location": bool(session.location),
            }
        }


# Global session manager instance (initialized in main.py)
session_manager: Optional[SessionManager] = None


def init_session_manager(db_session_maker):
    """Initialize global session manager with database"""
    global session_manager
    session_manager = SessionManager(db_session_maker)
    logger.info("✅ Session Manager initialized with database persistence")
    return session_manager
