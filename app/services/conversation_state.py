"""Conversation state management for WhatsApp users"""
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Stores state of a conversation with a user"""
    phone_number: str
    last_message: Optional[str] = None
    last_interaction: datetime = field(default_factory=datetime.utcnow)
    issue_status: str = "initial"  # initial, troubleshooting, awaiting_details, resolved, escalated
    issue_category: Optional[str] = None
    collected_details: Dict[str, Any] = field(default_factory=dict)
    ticket_id: Optional[str] = None
    messages_count: int = 0
    
    def update(self, message: str) -> None:
        """Update conversation state with new message"""
        self.last_message = message
        self.last_interaction = datetime.utcnow()
        self.messages_count += 1
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if conversation has expired"""
        elapsed = datetime.utcnow() - self.last_interaction
        return elapsed > timedelta(minutes=timeout_minutes)


class ConversationStateManager:
    """Manages conversation states for all active WhatsApp users"""
    
    def __init__(self, timeout_minutes: int = 60):
        self.conversations: Dict[str, ConversationState] = {}
        self.timeout_minutes = timeout_minutes
    
    def get_or_create(self, phone_number: str) -> ConversationState:
        """Get existing conversation or create new one"""
        if phone_number not in self.conversations:
            logger.info(f"Creating new conversation state for {phone_number}")
            self.conversations[phone_number] = ConversationState(phone_number=phone_number)
        else:
            # Check if expired
            conv = self.conversations[phone_number]
            if conv.is_expired(self.timeout_minutes):
                logger.info(f"Conversation expired for {phone_number}, creating new one")
                self.conversations[phone_number] = ConversationState(phone_number=phone_number)
        
        return self.conversations[phone_number]
    
    def get(self, phone_number: str) -> Optional[ConversationState]:
        """Get conversation state without creating"""
        return self.conversations.get(phone_number)
    
    def update_conversation(
        self,
        phone_number: str,
        message: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ConversationState:
        """Update conversation state with new information"""
        conv = self.get_or_create(phone_number)
        conv.update(message)
        
        if status:
            conv.issue_status = status
        if category:
            conv.issue_category = category
        if details:
            conv.collected_details.update(details)
        
        return conv
    
    def set_ticket(self, phone_number: str, ticket_id: str) -> ConversationState:
        """Associate a ticket with a conversation"""
        conv = self.get_or_create(phone_number)
        conv.ticket_id = ticket_id
        conv.issue_status = "escalated"
        logger.info(f"Ticket {ticket_id} associated with conversation {phone_number}")
        return conv
    
    def close_conversation(self, phone_number: str) -> None:
        """Close and remove conversation"""
        if phone_number in self.conversations:
            logger.info(f"Closing conversation for {phone_number}")
            del self.conversations[phone_number]
    
    def cleanup_expired(self) -> int:
        """Remove expired conversations and return count of cleaned conversations"""
        expired_phones = [
            phone for phone, conv in self.conversations.items()
            if conv.is_expired(self.timeout_minutes)
        ]
        
        for phone in expired_phones:
            del self.conversations[phone]
        
        if expired_phones:
            logger.info(f"Cleaned up {len(expired_phones)} expired conversations")
        
        return len(expired_phones)


# Singleton instance
conversation_manager = ConversationStateManager(timeout_minutes=60)
