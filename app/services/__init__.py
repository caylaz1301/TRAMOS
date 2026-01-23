"""Services package"""
from .osticket_service import osticket_service, osTicketService
from .whatsapp_service import whatsapp_service, WhatsAppService
from .conversation_manager import (
    ConversationManager,
    init_conversation_manager,
    get_conversation_manager
)

__all__ = [
    # osTicket
    "osticket_service",
    "osTicketService",
    # WhatsApp
    "whatsapp_service",
    "WhatsAppService",
    # Conversation Manager (database-backed)
    "ConversationManager",
    "init_conversation_manager",
    "get_conversation_manager",
]
