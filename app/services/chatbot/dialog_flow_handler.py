"""
Dialog Flow Handler - Smart Conversation Management for WhatsApp
ENHANCED VERSION: Delegates to SmartDialogFlowHandler with:
✅ Multi-turn conversation awareness
✅ Problem type-specific intelligent responses
✅ Smart input validation and clarification
✅ WhatsApp-optimized message formatting
✅ Context-aware response generation
✅ User frustration detection
✅ Adaptive conversation flow
"""

import logging
from typing import Tuple
from app.services.chatbot.session_manager import ConversationSession, DialogState
from app.services.chatbot.smart_dialog_flow import SmartDialogFlowHandler
from app.utils.smart_response_system import smart_response_system

logger = logging.getLogger(__name__)


class DialogFlowHandler:
    """
    Main Dialog Flow Handler - delegates to SmartDialogFlowHandler
    Maintains backward compatibility while providing enhanced intelligence
    """
    
    @staticmethod
    def get_next_prompt(session: ConversationSession, user_message: str = None) -> Tuple[str, DialogState]:
        """
        Get next conversation prompt based on current state
        Now using SmartDialogFlowHandler for intelligent responses
        
        Args:
            session: ConversationSession with current dialogue state
            user_message: User's input message
            
        Returns:
            Tuple of (response_message, next_dialog_state)
        """
        try:
            # Delegate to smart handler
            return SmartDialogFlowHandler.get_smart_response(session, user_message)
        except Exception as e:
            logger.error(f"Error in smart dialog handler: {e}", exc_info=True)
            # Fallback to safe response
            return (
                "Maaf, terjadi kesalahan sementara. Silakan coba lagi. 😊",
                session.current_state
            )
    
    # ===== GREETING STATE METHODS =====
    @staticmethod
    def _handle_greeting(session: ConversationSession) -> Tuple[str, DialogState]:
        """Handle greeting and ask for driver name"""
        greeting = smart_response_system.greeting()
        return (smart_response_system.format_for_whatsapp(greeting), DialogState.COLLECTING_NAME)
    
    # ===== NAME COLLECTION =====
    @staticmethod
    def _ask_for_problem(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask user what problem they're experiencing"""
        driver_name = session.driver_name or "Pengguna"
        problem_prompt = f"Terima kasih {driver_name}! 😊\n\n"
        problem_prompt += smart_response_system.format_question(
            "Ceritakan masalah yang Anda alami",
            options=["GPS tidak berfungsi", "Kamera error", "Baterai cepat habis", "Masalah koneksi"]
        )
        return (smart_response_system.format_for_whatsapp(problem_prompt), DialogState.COLLECTING_PROBLEM)
    
    # ===== PROBLEM ANALYSIS =====
    @staticmethod
    def _search_kb_solution(session: ConversationSession) -> Tuple[str, DialogState]:
        """Search for solution based on problem statement"""
        try:
            # Use AI to find potential solution
            response, next_state = SmartDialogFlowHandler._search_kb_smart(session)
            return (response, next_state)
        except Exception as e:
            logger.error(f"Error searching KB: {e}")
            return (
                "Sedang mencari solusi untuk masalah Anda...\n"
                "Bagaimanapun, saya sarankan:\n"
                "1. Restart device\n"
                "2. Verifikasi koneksi internet\n"
                "3. Periksa battery level\n"
                "\nApakah ada perbaikan? (ya/tidak)",
                DialogState.ASKING_SOLUTION_WORKED
            )
    
    # ===== SOLUTION PRESENTATION =====
    @staticmethod
    def _present_solution(session: ConversationSession) -> Tuple[str, DialogState]:
        """Present the found solution"""
        try:
            response, next_state = SmartDialogFlowHandler._present_solution_smart(session)
            return (response, next_state)
        except Exception as e:
            logger.error(f"Error presenting solution: {e}")
            msg = smart_response_system.format_escalation_message(
                "Solusi tidak ditemukan di database kami",
                estimated_time="Support team menghubungi Anda"
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)
    
    # ===== SOLUTION VERIFICATION =====
    @staticmethod
    def _ask_if_solution_worked(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask if the solution worked"""
        return SmartDialogFlowHandler._handle_solution_feedback(session, "")
    
    # ===== ADDITIONAL INFORMATION =====
    @staticmethod
    def _ask_for_unit(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask for TRAMOS unit information - INITIAL PROMPT (not handling user input)"""
        prompt = smart_response_system.format_for_whatsapp(
            "Baik, untuk kami assist lebih baik:\n\n"
            "Dari unit mana masalahnya? (misal: TRAM-001, Unit 5, atau 123)"
        )
        return (prompt, DialogState.COLLECTING_UNIT)
    
    @staticmethod
    def _ask_for_location(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask for location - INITIAL PROMPT"""
        prompt = smart_response_system.format_for_whatsapp(
            "Terimakasih. Sekarang, di mana kira-kira lokasi masalahnya?\n"
            "(Cukup sebut kota/area, misal: Jakarta, Bandara, Jalan Thamrin)"
        )
        return (prompt, DialogState.COLLECTING_LOCATION)
    
    @staticmethod
    def _ask_for_time(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask when the problem occurred - INITIAL PROMPT"""
        prompt = smart_response_system.format_for_whatsapp(
            "Baik. Kapan kira-kira masalah ini terjadi?\n"
            "(Bisa jam spesifik seperti 14:30 atau 'jam 3 sore')"
        )
        return (prompt, DialogState.COLLECTING_TIME)
    
    @staticmethod
    def _ask_for_confirmation(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask for final confirmation before escalation"""
        return SmartDialogFlowHandler._show_summary(session)
