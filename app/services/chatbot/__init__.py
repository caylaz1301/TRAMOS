"""
Chatbot Module - WhatsApp Dialog Flow & Conversation Management

This module handles all WhatsApp chatbot functionality:
- Dialog flow management (13-state machine)
- Smart conversation handling with context awareness
- NLP-based problem extraction and analysis
- Session management and state tracking
- KB solution search and recommendation
- WhatsApp message sending/receiving

Key Classes:
- SmartDialogFlowHandler: AI-powered smart responses (main dialog orchestrator)
- ConversationSession: Multi-turn session management
- ProblemExtractor: Problem extraction and categorization
- SolutionSearcher: KB search and matching
- WhatsAppService: WhatsApp Cloud API integration
"""

from .smart_dialog_flow import SmartDialogFlowHandler
from .session_manager import ConversationSession, DialogState, SessionManager
from .nlp_extractor import ProblemExtractor, problem_extractor
from .solution_searcher import SolutionSearcher, solution_searcher
from .whatsapp_service import WhatsAppService

__all__ = [
    "SmartDialogFlowHandler",
    "ConversationSession",
    "DialogState",
    "SessionManager",
    "ProblemExtractor",
    "problem_extractor",
    "SolutionSearcher",
    "solution_searcher",
    "WhatsAppService",
]
