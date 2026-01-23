"""
Enhanced Conversation Manager with Multi-Turn Support & PostgreSQL Persistence
Manages conversation state, context, and transitions for WhatsApp bot
"""

from typing import Optional, Dict, Tuple, List, Any
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.orm import Session
import json
import logging

from app.database_models import (
    Conversation, ConversationState, MessageHistory, User, MessageSender, Ticket,
    ConversationContext, ConversationTurn, get_or_create_user, get_active_conversation,
    get_conversation_history
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages multi-turn conversations with database persistence
    Handles state transitions, context management, and conversation flow
    """
    
    def __init__(self, session: Session):
        """Initialize with database session"""
        self.session = session
    
    # ========================================================================
    # CONVERSATION LIFECYCLE
    # ========================================================================
    
    def get_or_create_conversation(self, phone_number: str, user_name: str = None) -> Conversation:
        """
        Get active conversation or create new one
        
        Args:
            phone_number: User's WhatsApp number
            user_name: User's name (optional)
        
        Returns:
            Conversation object (new or existing)
        """
        # Get active conversation
        conversation = get_active_conversation(self.session, phone_number)
        
        if conversation:
            logger.info(f"📖 Loaded active conversation {conversation.id} for {phone_number}")
            return conversation
        
        # Create user if needed
        user = get_or_create_user(self.session, phone_number, user_name)
        
        # Create new conversation
        conversation = Conversation(
            user_id=user.id,
            phone_number=phone_number,
            current_state=ConversationState.NEW_ISSUE.value,
            context_data={
                'created_reason': 'new_contact',
                'language': user.language,
            }
        )
        self.session.add(conversation)
        self.session.commit()
        
        logger.info(f"✨ Created new conversation {conversation.id} for {phone_number}")
        return conversation
    
    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================
    
    def get_state(self, conversation: Conversation) -> ConversationState:
        """Get current conversation state"""
        return ConversationState(conversation.current_state)
    
    def set_state(self, conversation: Conversation, new_state: ConversationState):
        """
        Transition conversation to new state
        
        Args:
            conversation: Conversation object
            new_state: New ConversationState
        """
        old_state = conversation.current_state
        conversation.current_state = new_state.value
        conversation.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"🔄 State transition: {old_state} → {new_state.value}")
    
    def get_state_transitions(self, current_state: ConversationState) -> List[ConversationState]:
        """Get valid state transitions from current state"""
        transitions = {
            ConversationState.NEW_ISSUE: [
                ConversationState.ANALYZING,
                ConversationState.IDLE
            ],
            ConversationState.ANALYZING: [
                ConversationState.OFFERING_SOLUTIONS,
                ConversationState.ESCALATING,
                ConversationState.COLLECTING_DETAILS
            ],
            ConversationState.COLLECTING_DETAILS: [
                ConversationState.OFFERING_SOLUTIONS,
                ConversationState.ESCALATING
            ],
            ConversationState.OFFERING_SOLUTIONS: [
                ConversationState.USER_TRYING,
                ConversationState.ESCALATING
            ],
            ConversationState.USER_TRYING: [
                ConversationState.RESOLVED,
                ConversationState.ESCALATING
            ],
            ConversationState.ESCALATING: [
                ConversationState.HUMAN_SUPPORT
            ],
            ConversationState.HUMAN_SUPPORT: [
                ConversationState.RESOLVED,
                ConversationState.CLOSED
            ],
            ConversationState.RESOLVED: [
                ConversationState.NEW_ISSUE,  # ask if more help needed
                ConversationState.CLOSED
            ],
            ConversationState.CLOSED: [],
            ConversationState.IDLE: [
                ConversationState.NEW_ISSUE,
                ConversationState.CLOSED
            ]
        }
        return transitions.get(current_state, [])
    
    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================
    
    def get_context(self, conversation: Conversation) -> Dict[str, Any]:
        """Get full conversation context"""
        return conversation.context_data or {}
    
    def set_context(self, conversation: Conversation, key: str, value: Any):
        """
        Update conversation context
        
        Args:
            conversation: Conversation object
            key: Context field name
            value: Field value
        """
        if conversation.context_data is None:
            conversation.context_data = {}
        
        conversation.context_data[key] = value
        conversation.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.debug(f"📝 Context updated: {key} = {value}")
    
    def update_context(self, conversation: Conversation, updates: Dict[str, Any]):
        """Update multiple context fields at once"""
        if conversation.context_data is None:
            conversation.context_data = {}
        
        conversation.context_data.update(updates)
        conversation.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.debug(f"📝 Context updated with {len(updates)} fields")
    
    def get_full_context(self, conversation: Conversation) -> Dict[str, Any]:
        """
        Get complete conversation context including history
        
        Returns dict with:
        - current_state
        - context_data
        - recent_messages (last 5)
        - user_info
        - category
        - issue_description
        """
        recent_messages = self.session.query(MessageHistory).filter_by(
            conversation_id=conversation.id
        ).order_by(MessageHistory.created_at.desc()).limit(5).all()
        
        return {
            'conversation_id': conversation.id,
            'current_state': conversation.current_state,
            'category': conversation.category,
            'intent': conversation.intent,
            'issue_description': conversation.issue_description,
            'context_data': conversation.context_data or {},
            'recent_messages': [
                {
                    'sender': msg.sender,
                    'text': msg.message_text,
                    'timestamp': msg.created_at.isoformat()
                }
                for msg in reversed(recent_messages)
            ],
            'created_at': conversation.created_at.isoformat(),
            'last_message_at': conversation.last_message_at.isoformat() if conversation.last_message_at else None
        }
    
    # ========================================================================
    # MESSAGE TRACKING
    # ========================================================================
    
    def add_message(
        self,
        conversation: Conversation,
        phone_number: str,
        message_text: str,
        sender: str = MessageSender.USER.value,
        intent: str = None,
        category: str = None,
        confidence: int = 0,
        language: str = "id"
    ) -> MessageHistory:
        """
        Add message to conversation history
        
        Args:
            conversation: Conversation object
            phone_number: Sender's phone number
            message_text: Message content
            sender: 'user' or 'bot'
            intent: Detected intent
            category: Detected category
            confidence: Confidence score (0-100)
            language: Message language
        
        Returns:
            MessageHistory object
        """
        message = MessageHistory(
            conversation_id=conversation.id,
            phone_number=phone_number,
            sender=sender,
            message_text=message_text,
            intent=intent,
            category=category,
            confidence=confidence,
            language=language
        )
        
        self.session.add(message)
        
        # Update conversation timestamp
        conversation.last_message_at = datetime.utcnow()
        if sender == MessageSender.USER.value:
            conversation.intent = intent
            conversation.category = category
        
        self.session.commit()
        
        logger.debug(f"💬 Added {sender} message: {message_text[:50]}...")
        return message
    
    def get_conversation_history(self, conversation: Conversation, limit: int = 20) -> List[MessageHistory]:
        """Get message history for conversation"""
        return self.session.query(MessageHistory).filter_by(
            conversation_id=conversation.id
        ).order_by(MessageHistory.created_at.desc()).limit(limit).all()
    
    def get_last_message(self, conversation: Conversation, sender: str = None) -> Optional[MessageHistory]:
        """Get last message (optionally filtered by sender)"""
        query = self.session.query(MessageHistory).filter_by(conversation_id=conversation.id)
        
        if sender:
            query = query.filter_by(sender=sender)
        
        return query.order_by(MessageHistory.created_at.desc()).first()
    
    def get_messages_since(self, conversation: Conversation, minutes: int = 30) -> List[MessageHistory]:
        """Get messages from last N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return self.session.query(MessageHistory).filter(
            MessageHistory.conversation_id == conversation.id,
            MessageHistory.created_at >= cutoff
        ).order_by(MessageHistory.created_at).all()
    
    # ========================================================================
    # MULTI-TURN CONVERSATION LOGIC
    # ========================================================================
    
    def get_turn_count(self, conversation: Conversation) -> int:
        """Get number of turns in conversation"""
        return self.session.query(MessageHistory).filter_by(
            conversation_id=conversation.id,
            sender=MessageSender.USER.value
        ).count()
    
    def get_conversation_summary(self, conversation: Conversation) -> Dict[str, Any]:
        """
        Get summary of conversation for escalation/context
        
        Returns dict with:
        - turns_count
        - category
        - issue_description
        - failed_solutions (attempted solutions that didn't work)
        - user_frustration_level
        """
        messages = self.get_conversation_history(conversation, limit=50)
        user_messages = [m for m in messages if m.sender == MessageSender.USER.value]
        
        # Count failed attempts
        failed_attempts = len([
            m for m in messages
            if m.sender == MessageSender.BOT.value and "tidak bekerja" in m.message_text.lower()
        ])
        
        return {
            'turns_count': len(user_messages),
            'category': conversation.category,
            'issue_description': conversation.issue_description,
            'failed_attempts': failed_attempts,
            'first_message': messages[-1].message_text if messages else None,
            'last_message': messages[0].message_text if messages else None,
            'conversation_duration_minutes': int(
                (conversation.updated_at - conversation.created_at).total_seconds() / 60
            ) if conversation.created_at else 0
        }
    
    # ========================================================================
    # ESCALATION & TICKET MANAGEMENT
    # ========================================================================
    
    def should_escalate(self, conversation: Conversation) -> Tuple[bool, str]:
        """
        Determine if conversation should be escalated to human support
        
        Returns:
            (should_escalate: bool, reason: str)
        """
        summary = self.get_conversation_summary(conversation)
        
        # Escalate if multiple failed attempts
        if summary['failed_attempts'] >= 3:
            return True, "Multiple failed troubleshooting attempts"
        
        # Escalate if complex categories
        complex_categories = ['Engine', 'Hardware', 'Software']
        if summary['category'] in complex_categories:
            return True, f"Complex category: {summary['category']}"
        
        # Escalate if conversation too long
        if summary['turns_count'] >= 6:
            return True, "Long conversation without resolution"
        
        # Escalate if explicitly requested
        last_msg = self.get_last_message(conversation, MessageSender.USER.value)
        if last_msg and any(kw in last_msg.message_text.lower() for kw in ['operator', 'manusia', 'bantuan', 'support']):
            return True, "User requested human support"
        
        return False, "No escalation needed"
    
    def create_ticket_reference(self, conversation: Conversation, ticket_id: int, osticket_url: str = None):
        """Link osTicket to conversation"""
        conversation.ticket_id = ticket_id
        conversation.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"🎫 Ticket #{ticket_id} linked to conversation {conversation.id}")
    
    # ========================================================================
    # CONVERSATION CLEANUP & EXPIRY
    # ========================================================================
    
    def mark_resolved(self, conversation: Conversation, resolution_notes: str = None):
        """Mark conversation as resolved"""
        conversation.current_state = ConversationState.RESOLVED.value
        if resolution_notes:
            conversation.context_data['resolution_notes'] = resolution_notes
        conversation.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"✅ Conversation {conversation.id} marked as resolved")
    
    def close_conversation(self, conversation: Conversation):
        """Close conversation"""
        conversation.current_state = ConversationState.CLOSED.value
        conversation.updated_at = datetime.utcnow()
        self.session.commit()
        
        logger.info(f"🚪 Conversation {conversation.id} closed")
    
    def get_idle_conversations(self, minutes: int = 60) -> List[Conversation]:
        """Get conversations inactive for N minutes"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return self.session.query(Conversation).filter(
            Conversation.last_message_at < cutoff,
            Conversation.current_state != ConversationState.CLOSED.value
        ).all()
    
    def auto_close_idle(self, minutes: int = 3600):  # 1 hour
        """Auto-close idle conversations"""
        idle = self.get_idle_conversations(minutes)
        count = 0
        for conv in idle:
            self.close_conversation(conv)
            count += 1
        
        logger.info(f"🧹 Auto-closed {count} idle conversations")
        return count
    
    # ========================================================================
    # STATISTICS & ANALYTICS
    # ========================================================================
    
    def get_user_stats(self, phone_number: str) -> Dict[str, Any]:
        """Get user conversation statistics"""
        user = self.session.query(User).filter_by(phone_number=phone_number).first()
        if not user:
            return {}
        
        conversations = self.session.query(Conversation).filter_by(phone_number=phone_number).all()
        total_messages = self.session.query(MessageHistory).filter_by(phone_number=phone_number).count()
        resolved = len([c for c in conversations if c.current_state == ConversationState.RESOLVED.value])
        
        return {
            'total_conversations': len(conversations),
            'resolved_conversations': resolved,
            'total_messages': total_messages,
            'avg_messages_per_conversation': total_messages / len(conversations) if conversations else 0,
            'first_contact': user.first_contact_at.isoformat() if user else None,
            'last_contact': user.last_contact_at.isoformat() if user and user.last_contact_at else None,
            'preferred_language': user.preferred_language if user else 'unknown'
        }
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get statistics per issue category"""
        from sqlalchemy import func
        results = self.session.query(
            Conversation.category,
            func.count(Conversation.id).label('count')
        ).filter(
            Conversation.category != None
        ).group_by(Conversation.category).all()
        
        return {cat: count for cat, count in results}
    
    # ========================================================================
    # CONVERSATION TURNS (Detailed Logging)
    # ========================================================================
    
    def log_turn(
        self,
        conversation: Conversation,
        turn_number: int,
        user_message: str,
        user_intent: str,
        user_category: str,
        user_confidence: int,
        bot_response: str,
        bot_state: str,
        processing_time_ms: int = 0,
        turn_type: str = "standard"
    ) -> ConversationTurn:
        """Log detailed turn information"""
        turn = ConversationTurn(
            conversation_id=conversation.id,
            phone_number=conversation.phone_number,
            turn_number=turn_number,
            user_message=user_message,
            user_intent=user_intent,
            user_category=user_category,
            user_confidence=user_confidence,
            bot_response=bot_response,
            bot_state=bot_state,
            processing_time_ms=processing_time_ms,
            turn_type=turn_type
        )
        
        self.session.add(turn)
        self.session.commit()
        
        return turn
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    def export_conversation(self, conversation: Conversation) -> Dict[str, Any]:
        """Export full conversation as dict (for backup/analysis)"""
        messages = self.get_conversation_history(conversation, limit=1000)
        
        return {
            'id': conversation.id,
            'phone_number': conversation.phone_number,
            'state': conversation.current_state,
            'category': conversation.category,
            'issue_description': conversation.issue_description,
            'created_at': conversation.created_at.isoformat(),
            'updated_at': conversation.updated_at.isoformat(),
            'context': conversation.context_data,
            'messages': [
                {
                    'sender': msg.sender,
                    'text': msg.message_text,
                    'intent': msg.intent,
                    'category': msg.category,
                    'timestamp': msg.created_at.isoformat()
                }
                for msg in reversed(messages)
            ]
        }


# ============================================================================
# SINGLETON MANAGER (FOR GLOBAL USE)
# ============================================================================

_conversation_manager: Optional[ConversationManager] = None


def init_conversation_manager(session: Session) -> ConversationManager:
    """Initialize global conversation manager"""
    global _conversation_manager
    _conversation_manager = ConversationManager(session)
    return _conversation_manager


def get_conversation_manager() -> ConversationManager:
    """Get global conversation manager"""
    if _conversation_manager is None:
        raise RuntimeError("ConversationManager not initialized. Call init_conversation_manager first.")
    return _conversation_manager
