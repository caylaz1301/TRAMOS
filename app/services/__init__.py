"""
Services Package - Organized into specialized modules

Modules:
- chatbot/: WhatsApp dialog flow, conversation management, NLP, websocket handling
- data_science/: Analytics, patterns, predictions, anomaly detection, benchmarking
- Root level: osTicket integration (ticket management)
"""

from .osticket_service import osticket_service, osTicketService
from .chatbot.whatsapp_service import whatsapp_service, WhatsAppService

# Import submodules for easy access
from . import chatbot
from . import data_science

__all__ = [
    # osTicket integration
    "osticket_service",
    "osTicketService",
    # WhatsApp service
    "whatsapp_service",
    "WhatsAppService",
    # Submodules
    "chatbot",
    "data_science",
]
