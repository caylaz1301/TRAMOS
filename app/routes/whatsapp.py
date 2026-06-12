"""
WhatsApp Business API Webhook Handler
Handles incoming messages dari Meta WhatsApp Business Platform
Multi-turn conversation dengan AI intent detection dan KB troubleshooting
"""

import logging
import json
from typing import Optional, Tuple
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import Response

from app.config import settings
from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING, get_kb_category
from app.utils.ai_logic import ai_engine
from app.services.osticket_service import osticket_service
from app.services.chatbot.whatsapp_service import whatsapp_service
from app.services.chatbot import session_manager as sm_module
from app.services.chatbot.session_manager import DialogState
from app.services.chatbot.smart_dialog_flow import SmartDialogFlowHandler
from app.services.chatbot.nlp_extractor import problem_extractor
from app.utils.smart_response_system import smart_response_system
from app.schemas.ticket import CreateTicketRequest
from app.services.database_tracker import db_tracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["whatsapp"])

# ============================================================================
# MESSAGE DEDUPLICATION - Prevent duplicate webhook processing
# Meta can send the same webhook event multiple times
# ============================================================================
_processed_message_ids: dict = {}  # {message_id: timestamp}
_DEDUP_WINDOW = 30  # seconds to keep message IDs
_DEDUP_MAX_SIZE = 1000  # max entries to prevent memory leak

def _is_duplicate_message(message_id: str) -> bool:
    """Check if this message was already processed (Meta duplicate webhook)"""
    import time
    now = time.time()
    
    # Clean old entries (older than dedup window)
    expired = [mid for mid, ts in _processed_message_ids.items() if now - ts > _DEDUP_WINDOW]
    for mid in expired:
        del _processed_message_ids[mid]
    
    # Hard cap: evict oldest entries if dict is too large (prevents memory leak)
    if len(_processed_message_ids) >= _DEDUP_MAX_SIZE:
        sorted_ids = sorted(_processed_message_ids.items(), key=lambda x: x[1])
        for mid, _ in sorted_ids[:len(sorted_ids) // 2]:  # Remove oldest 50%
            del _processed_message_ids[mid]
    
    if message_id in _processed_message_ids:
        logger.warning(f"⚠️ Duplicate message detected: {message_id}, skipping")
        return True
    
    _processed_message_ids[message_id] = now
    return False


def get_session_manager():
    """Get the globally initialized session manager"""
    return sm_module.session_manager


def _track_turn(session, phone_number: str, message_body: str, response: str,
                state_value: str, intent: str, category: str = None,
                turn_start: float = None):
    """Helper to track a conversation turn in the database.
    Eliminates repetitive 8-line DB tracking blocks from every state handler.
    """
    if not getattr(session, '_db_conversation_id', None):
        return
    try:
        import time as _time
        _ms = int((_time.time() - turn_start) * 1000) if turn_start else 0
        db_tracker.track_full_turn(
            phone_number, message_body, response,
            session._db_conversation_id, session.message_count, state_value,
            intent=intent, category=category, processing_time_ms=_ms
        )
    except Exception as e:
        logger.warning(f"⚠️ DB tracking error (non-fatal): {e}")



# ============================================================================
# WEBHOOK VERIFICATION (GET request)
# ============================================================================
@router.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
) -> Response:
    """
    Webhook verification dari Meta WhatsApp Business API
    Meta sends GET request untuk verify webhook URL
    """
    if hub_verify_token != settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.warning("❌ Invalid webhook token")
        return Response(status_code=403, content="Invalid token")
    
    if hub_mode != "subscribe":
        logger.warning(f"❌ Invalid mode: {hub_mode}")
        return Response(status_code=400, content="Invalid mode")
    
    logger.info("✅ WhatsApp webhook verified successfully")
    return Response(content=hub_challenge, media_type="text/plain")


# ============================================================================
# MESSAGE HANDLING (POST request)
# ============================================================================
@router.post("/webhook/whatsapp")
async def handle_incoming_message(request: Request) -> Response:
    """
    Handle incoming messages dari WhatsApp users
    
    Flow:
    1. Parse incoming message
    2. Detect intent using smart dialog flow + KB search
    3. Generate response based on intent and KB
    4. Send response back via WhatsApp API
    """
    try:
        body = await request.json()
        
        # Validate webhook format
        if body.get("object") != "whatsapp_business_account":
            return Response(
                content=json.dumps({"status": "ignored"}), 
                media_type="application/json"
            )
        
        # Extract message data
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        statuses = value.get("statuses", [])
        if statuses:
            for status in statuses:
                message_id = status.get("id", "unknown")
                recipient_id = status.get("recipient_id", "unknown")
                status_name = status.get("status", "unknown")
                errors = status.get("errors", [])

                if errors:
                    for error in errors:
                        logger.warning(
                            "⚠️ WhatsApp delivery status: %s message_id=%s recipient=%s error_code=%s title=%s detail=%s",
                            status_name,
                            message_id,
                            recipient_id,
                            error.get("code", "unknown"),
                            error.get("title", "unknown"),
                            error.get("error_data", {}).get("details", error.get("message", "")),
                        )
                else:
                    logger.info(
                        "📬 WhatsApp delivery status: %s message_id=%s recipient=%s",
                        status_name,
                        message_id,
                        recipient_id,
                    )

            return Response(
                content=json.dumps({"status": "ok", "event": "statuses"}),
                media_type="application/json",
                status_code=200,
            )

        messages = value.get("messages", [])
        if not messages:
            logger.info(
                "ℹ️ WhatsApp webhook event with no messages/statuses: keys=%s",
                sorted(value.keys()),
            )
            return Response(
                content=json.dumps({"status": "ok"}), 
                media_type="application/json"
            )
        
        message = messages[0]
        from_phone = message.get("from")
        message_type = message.get("type")
        
        # Only handle text messages
        if message_type != "text":
            logger.info(f"📎 Non-text message from {from_phone}: {message_type}")
            return Response(
                content=json.dumps({"status": "ok"}), 
                media_type="application/json"
            )
        
        message_body = message.get("text", {}).get("body", "").strip()
        if not message_body:
            return Response(
                content=json.dumps({"status": "ok"}), 
                media_type="application/json"
            )
        
        # ====== DEDUPLICATION: Skip if already processed ======
        wa_message_id = message.get("id", "")
        if wa_message_id and _is_duplicate_message(wa_message_id):
            return Response(
                content=json.dumps({"status": "ok", "duplicate": True}), 
                media_type="application/json",
                status_code=200
            )
        
        # Get user profile
        contacts = value.get("contacts", [{}])[0]
        user_name = contacts.get("profile", {}).get("name", "User")
        
        logger.info(f"📱 [{from_phone}] {user_name}: {message_body[:80]}")
        
        # ====== PROCESS MESSAGE WITH AI ======
        response_text = await process_message_with_ai(
            message_body=message_body,
            user_name=user_name,
            phone_number=from_phone
        )
        
        # Debug: Log response content
        logger.debug(f"Response content: '{response_text[:200]}...' (length: {len(response_text)})")
        
        # ====== SEND RESPONSE VIA WHATSAPP ======
        if whatsapp_service.is_configured():
            if not response_text or response_text.strip() == "":
                logger.warning(f"⚠️ Response is empty for {from_phone}, skipping send")
            else:
                send_success = await whatsapp_service.send_message(from_phone, response_text)
                if send_success:
                    logger.info(f"✅ Response sent to {from_phone}")
                else:
                    logger.warning(f"⚠️ Failed to send response to {from_phone}")
        else:
            logger.info(f"📝 Response (not sent - sandbox mode): {response_text[:100]}")
        
        return Response(
            content=json.dumps({"status": "ok"}), 
            media_type="application/json",
            status_code=200
        )
    
    except json.JSONDecodeError:
        logger.error("❌ Invalid JSON in webhook")
        return Response(
            content=json.dumps({"error": "invalid_json"}), 
            media_type="application/json",
            status_code=400
        )
    
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {str(e)}", exc_info=True)
        return Response(
            content=json.dumps({"error": "internal_error"}), 
            media_type="application/json",
            status_code=500
        )


# ============================================================================
# AI-POWERED MESSAGE PROCESSING
# ============================================================================
# Alur ini menangani semua pesan masuk dari WhatsApp dengan state machine
# yang tersusun dalam 13 state:
# GREETING → COLLECTING_NAME → COLLECTING_PROBLEM → ASKING_SOLUTION_WORKED →
# COLLECTING_UNIT → COLLECTING_LOCATION → COLLECTING_TIME → CONFIRMING_DETAILS →
# CREATING_TICKET → (RESOLVED atau CLOSED)
#
# Setiap state memiliki handler spesifik yang melakukan:
# 1. Validasi input user
# 2. Ekstraksi data terstruktur
# 3. Transisi ke state berikutnya
# 4. Logging untuk analytics

async def process_message_with_ai(
    message_body: str, 
    user_name: str, 
    phone_number: str
) -> str:
    """
    Process message menggunakan SESSION-AWARE AI with dialog flow management
    
    Enhanced flow:
    1. Get or create conversation session
    2. Route through dialog state machine (greeting → name → problem → unit → location → time → confirm → ticket)
    3. Collect structured data via dialog flow
    4. Generate contextual, natural responses
    5. Create ticket when data is complete
    """
    import time as _time
    _turn_start = _time.time()
    message_lower = message_body.lower()
    
    # ===== SESSION MANAGEMENT =====
    # Get or create session for this user
    session_manager = get_session_manager()
    session = session_manager.get_or_create_session(phone_number)
    session.update_activity()
    
    logger.info(
        f"💬 [{phone_number}] {user_name} | State: {session.current_state.value} | Message: {message_body[:60]}"
    )
    
    # ===== DATABASE TRACKING: ensure user + conversation exist =====
    _user_id = db_tracker.get_or_create_user(phone_number, user_name)
    # Use get_or_create to survive server restart / cache miss
    if not getattr(session, '_db_conversation_id', None):
        session._db_conversation_id = db_tracker.get_or_create_conversation(phone_number, _user_id) if _user_id else None
    
    # ===== DIALOG FLOW ROUTING =====
    # Dialog state machine handles structured data collection
    
    if session.current_state == DialogState.GREETING:
        # First message - greet and ask for name
        session.add_message(sender="user", message=message_body, intent="greeting", category=None)
        # Langsung gunakan formatter global agar tidak men-shadow import module.
        response = smart_response_system.format_for_whatsapp(smart_response_system.greeting())
        session.current_state = DialogState.COLLECTING_NAME
        session.add_message(sender="bot", message=response, intent="greeting", category=None)
        get_session_manager().save_session(session)
        # DB tracking
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, DialogState.COLLECTING_NAME.value,
                intent="greeting", processing_time_ms=_ms)
        return response
    
    elif session.current_state == DialogState.COLLECTING_NAME:
        # Collect driver name - delegate to SmartDialogFlowHandler for validation
        session.add_message(sender="user", message=message_body, intent="data_collection", category=None)
        
        response, next_state = SmartDialogFlowHandler._handle_name_input(session, message_body)
        session.current_state = next_state
        session.add_message(sender="bot", message=response, intent="data_collection", category=None)
        get_session_manager().save_session(session)
        # DB tracking
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, next_state.value,
                intent="data_collection", processing_time_ms=_ms)
            if session.driver_name:
                db_tracker.update_user_name(phone_number, session.driver_name)
        return response
    
    elif session.current_state == DialogState.COLLECTING_PROBLEM:
        # Collect problem description + extract category
        problem_text = message_body.strip()
        if SmartDialogFlowHandler.is_blame_without_evidence_request(problem_text):
            session.add_message(sender="user", message=message_body, intent="policy_guardrail", category="Driver")
            response = SmartDialogFlowHandler.blame_without_evidence_response()
            session.add_message(sender="bot", message=response, intent="policy_guardrail", category="Driver")
            get_session_manager().save_session(session)
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, session.current_state.value,
                    intent="policy_guardrail", category="Driver", processing_time_ms=_ms)
            return response

        if SmartDialogFlowHandler.is_sensitive_or_out_of_scope(problem_text):
            session.add_message(sender="user", message=message_body, intent="out_of_scope", category=None)
            response = SmartDialogFlowHandler.sensitive_request_response()
            session.add_message(sender="bot", message=response, intent="out_of_scope", category=None)
            get_session_manager().save_session(session)
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, session.current_state.value,
                    intent="out_of_scope", processing_time_ms=_ms)
            return response

        ack_only = problem_text.lower() in SmartDialogFlowHandler.ACKNOWLEDGMENT_PATTERNS
        if len(problem_text) < 5 or ack_only:
            session.add_message(sender="user", message=message_body, intent="clarification", category=None)
            response = (
                "Saya belum menangkap detail masalahnya.\n\n"
                "Tolong ceritakan kendala yang dialami driver/unit, misalnya:\n"
                "- GPS tidak update lokasi\n"
                "- Kamera mati atau layar hitam\n"
                "- Kendaraan mogok di jalan\n"
                "- Aplikasi error saat dipakai"
            )
            response = smart_response_system.format_for_whatsapp(response)
            session.add_message(sender="bot", message=response, intent="clarification", category=None)
            get_session_manager().save_session(session)
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, session.current_state.value,
                    intent="clarification", processing_time_ms=_ms)
            return response

        session.problem_description = message_body.strip()
        session.add_message(sender="user", message=message_body, intent="data_collection", category=None)
        
        # Use keyword analysis (same as SmartDialogFlowHandler.analyze_problem) for consistency
        analysis = SmartDialogFlowHandler.analyze_problem(message_body)
        session.problem_category = analysis.get('category') or 'Service'
        session.problem_severity = analysis.get('severity', 'medium')
        
        # Also try NLP extractor as fallback if category is still generic
        if session.problem_category == 'Service':
            problem_details = problem_extractor.extract_problem_details(message_body)
            extracted_cat = problem_details.get('category', 'Service')
            if extracted_cat != 'Service':
                session.problem_category = extracted_cat
                session.problem_severity = problem_details.get('severity', session.problem_severity)
        
        logger.debug(f"📊 Problem extraction: Category={session.problem_category}, Severity={session.problem_severity}")
        
        # Search for KB solution and get feedback directly
        # Gunakan SmartDialogFlowHandler._search_kb_smart untuk pencarian solusi
        response, next_state = SmartDialogFlowHandler._search_kb_smart(session)
        session.current_state = next_state
        session.add_message(sender="bot", message=response, intent="solution_search", category=session.problem_category)
        get_session_manager().save_session(session)
        # DB tracking
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, next_state.value,
                intent="solution_search", category=session.problem_category, processing_time_ms=_ms)
            db_tracker.update_conversation_state(session._db_conversation_id,
                next_state.value, category=session.problem_category,
                issue_description=session.problem_description)
            # Log solution attempt if KB solution was found
            if session.kb_solution:
                session._db_solution_attempt_id = db_tracker.log_solution_attempt(
                    conversation_id=session._db_conversation_id,
                    phone_number=phone_number,
                    solution_id=session.kb_solution.get('category', 'unknown'),
                    category=session.problem_category or 'Service',
                    problem_description=session.problem_description or '',
                    kb_match_score=session.kb_solution.get('confidence'),
                )
        return response
    
    elif session.current_state == DialogState.ASKING_SOLUTION_WORKED:
        # Get user feedback on KB solution - use SmartDialogFlowHandler for consistent matching
        session.add_message(sender="user", message=message_body, intent="solution_feedback", category=session.problem_category)
        
        response, next_state = SmartDialogFlowHandler._handle_solution_feedback(session, message_body)
        session.current_state = next_state
        
        if next_state == DialogState.RESOLVED:
            logger.info(f"✅ KB solution worked for {phone_number}")
        elif next_state == DialogState.COLLECTING_UNIT:
            logger.info(f"❌ KB solution didn't work, escalating for {phone_number}")
        
        session.add_message(sender="bot", message=response, intent="solution_feedback", category=session.problem_category)
        get_session_manager().save_session(session)
        # DB tracking
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, next_state.value,
                intent="solution_feedback", category=session.problem_category, processing_time_ms=_ms)
            # Update solution attempt outcome
            attempt_id = getattr(session, '_db_solution_attempt_id', None)
            # Fallback: recover from DB if lost (e.g. server restart)
            if not attempt_id and session._db_conversation_id:
                attempt_id = db_tracker.get_active_solution_attempt(session._db_conversation_id)
            if attempt_id:
                if next_state == DialogState.RESOLVED:
                    db_tracker.update_solution_outcome(attempt_id, 'worked')
                    db_tracker.update_user_profile(phone_number, session.problem_category, issue_resolved=True)
                    # AI resolution analytics
                    conv_duration = (session.last_activity - session.created_at).total_seconds() / 60
                    db_tracker.create_ai_resolution(
                        session._db_conversation_id, phone_number,
                        session.problem_category, resolution_time_minutes=int(conv_duration))
                elif next_state == DialogState.COLLECTING_UNIT:
                    db_tracker.update_solution_outcome(attempt_id, 'escalated', escalation_needed=True)
        return response
    
    elif session.current_state == DialogState.COLLECTING_UNIT:
        # Collect vehicle unit/equipment ID - delegate to SmartDialogFlowHandler for validation
        session.add_message(sender="user", message=message_body, intent="data_collection", category=session.problem_category)
        
        response, next_state = SmartDialogFlowHandler._handle_unit_input(session, message_body)
        session.current_state = next_state
        session.add_message(sender="bot", message=response, intent="data_collection", category=session.problem_category)
        get_session_manager().save_session(session)
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, next_state.value,
                intent="data_collection", category=session.problem_category, processing_time_ms=_ms)
        return response
    
    elif session.current_state == DialogState.COLLECTING_LOCATION:
        # Collect location - delegate to SmartDialogFlowHandler for validation
        session.add_message(sender="user", message=message_body, intent="data_collection", category=session.problem_category)
        
        response, next_state = SmartDialogFlowHandler._handle_location_input(session, message_body)
        session.current_state = next_state
        session.add_message(sender="bot", message=response, intent="data_collection", category=session.problem_category)
        get_session_manager().save_session(session)
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, next_state.value,
                intent="data_collection", category=session.problem_category, processing_time_ms=_ms)
        return response
    
    elif session.current_state == DialogState.COLLECTING_TIME:
        # Use SmartDialogFlowHandler to parse time properly (not raw text)
        session.add_message(sender="user", message=message_body, intent="data_collection", category=session.problem_category)
        
        response, next_state = SmartDialogFlowHandler._handle_time_input(session, message_body)
        session.current_state = next_state
        session.add_message(sender="bot", message=response, intent="data_collection", category=session.problem_category)
        get_session_manager().save_session(session)
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, next_state.value,
                intent="data_collection", category=session.problem_category, processing_time_ms=_ms)
        return response
    
    elif session.current_state == DialogState.CONFIRMING_DETAILS:
        # Confirm all collected data before creating ticket
        session.add_message(sender="user", message=message_body, intent="confirmation", category=session.problem_category)
        
        # Check if user is providing more problem details instead of confirmation
        # (e.g., saying "gps error mulu" when bot asked "jelaskan lebih detail")
        detail_keywords = ['error', 'rusak', 'mogok', 'mati', 'offline', 'tidak bisa', 'problema', 'masalah', 'issue', 'gagal', 'failed']
        is_detail_response = any(keyword in message_lower for keyword in detail_keywords)
        
        if is_detail_response and len(message_body) > 5:
            # User is providing detail, not confirmation - re-process as problem detail
            session.problem_description = message_body.strip()
            
            # Re-extract category from new detail
            problem_details = problem_extractor.extract_problem_details(message_body)
            if problem_details.get('category') != 'Service':
                # Better category found, update it
                session.problem_category = problem_details.get('category', session.problem_category)
            
            session.problem_severity = problem_details.get('severity', session.problem_severity)
            logger.info(f"Re-extracted problem: {session.problem_category} from user detail: {message_body[:50]}")
            
            # Go back and search KB with updated problem
            response, next_state = SmartDialogFlowHandler._search_kb_smart(session)
            session.current_state = next_state
            session.add_message(sender="bot", message=response, intent="solution_search", category=session.problem_category)
            get_session_manager().save_session(session)
            # DB tracking
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, next_state.value,
                    intent="solution_search", category=session.problem_category, processing_time_ms=_ms)
            return response
        
        # Normal confirmation handling (yes/no)
        response, next_state = SmartDialogFlowHandler._handle_confirmation(session, message_body)
        
        if next_state == DialogState.CREATING_TICKET:
            # User confirmed - proceed to ticket creation
            session.current_state = next_state
            session.add_message(sender="bot", message=response, intent="confirmation", category=session.problem_category)
            get_session_manager().save_session(session)
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, next_state.value,
                    intent="confirmation", category=session.problem_category, processing_time_ms=_ms)
            return await _create_ticket_from_session(session, phone_number, user_name)
        elif next_state == DialogState.COLLECTING_UNIT:
            # User wants to change data - start unit collection again
            session.current_state = next_state
            session.add_message(sender="bot", message=response, intent="data_collection", category=session.problem_category)
            get_session_manager().save_session(session)
            # DB tracking
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, next_state.value,
                    intent="data_collection", category=session.problem_category, processing_time_ms=_ms)
            return response
        else:
            # Clarification needed - ask again
            session.current_state = next_state
            session.add_message(sender="bot", message=response, intent="confirmation", category=session.problem_category)
            get_session_manager().save_session(session)
            # DB tracking
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, next_state.value,
                    intent="confirmation", category=session.problem_category, processing_time_ms=_ms)
            return response
    
    elif session.current_state == DialogState.CREATING_TICKET:
        # Ticket creation in progress — user sent another message while waiting
        session.add_message(sender="user", message=message_body, intent="waiting", category=session.problem_category)
        response = "Tiket Anda sedang dalam proses pembuatan. Mohon tunggu sebentar... ⏳"
        session.add_message(sender="bot", message=response, intent="waiting", category=session.problem_category)
        get_session_manager().save_session(session)
        if session._db_conversation_id:
            _ms = int((_time.time() - _turn_start) * 1000)
            db_tracker.track_full_turn(phone_number, message_body, response,
                session._db_conversation_id, session.message_count, "creating_ticket",
                intent="waiting", category=session.problem_category, processing_time_ms=_ms)
        return response
    
    elif session.current_state == DialogState.CLOSED or session.current_state == DialogState.RESOLVED:
        # Close old conversation in DB before starting a new one
        old_conv_id = getattr(session, '_db_conversation_id', None)
        if old_conv_id:
            db_tracker.close_conversation(old_conv_id, session.current_state.value)
        
        # Session closed/resolved - start fresh conversation
        session_manager.close_session(phone_number)
        session = session_manager.create_session(phone_number)
        session.add_message(sender="user", message=message_body, intent="greeting", category=None)
        # Langsung gunakan formatter global saat sesi lama ditutup dan sesi baru dimulai.
        response = smart_response_system.format_for_whatsapp(smart_response_system.greeting())
        session.current_state = DialogState.COLLECTING_NAME
        session.add_message(sender="bot", message=response, intent="greeting", category=None)
        get_session_manager().save_session(session)
        
        # DB tracking for new conversation
        _user_id_new = db_tracker.get_or_create_user(phone_number, user_name)
        if _user_id_new:
            session._db_conversation_id = db_tracker.create_conversation(phone_number, _user_id_new)
            if session._db_conversation_id:
                _ms = int((_time.time() - _turn_start) * 1000)
                db_tracker.track_full_turn(phone_number, message_body, response,
                    session._db_conversation_id, session.message_count, DialogState.COLLECTING_NAME.value,
                    intent="greeting", processing_time_ms=_ms)
        return response
    
    # Fallback - shouldn't reach here normally
    logger.warning(f"⚠️ Unexpected state: {session.current_state.value} for {phone_number}")
    return "Maaf, terjadi kesalahan. Kirim 'halo' untuk memulai percakapan baru. 🙏"


async def _create_ticket_from_session(session, phone_number: str, user_name: str) -> str:
    """Create osTicket from collected session data"""
    
    try:
        # Prepare ticket data
        driver_name = session.driver_name or "Unknown Driver"
        problem_desc = session.problem_description or "Tidak ada deskripsi"
        equipment = session.vehicle_unit or "Tidak disebutkan"
        location = session.location or "Tidak disebutkan"
        issue_time = session.issue_time or "Tidak disebutkan"
        problem_cat = session.problem_category or "Service"
        severity = session.problem_severity or "medium"
        
        # Build informative subject: [TRAMOS] SEVERITY - Category: Problem summary
        severity_label = severity.upper()
        problem_summary = problem_desc[:50].replace('\n', ' ')
        subject = f"[TRAMOS] {severity_label} - {problem_cat}: {problem_summary}"
        
        # Build structured ticket body
        # Section 1: Reporter info
        body_parts = [
            "📋 LAPORAN MASALAH TRAMOS",
            "━" * 30,
            "",
            "👤 PELAPOR",
            f"   Nama: {driver_name}",
            f"   Telepon: {phone_number}",
            "",
            "🛠️ DETAIL MASALAH",
            f"   Deskripsi: {problem_desc}",
            f"   Kategori: {problem_cat}",
            f"   Tingkat Urgensi: {severity_label}",
            "",
            "📍 INFORMASI LAPANGAN",
            f"   Unit/Kendaraan: {equipment}",
            f"   Lokasi: {location}",
            f"   Waktu Kejadian: {issue_time}",
            "",
            "🤖 ANALISIS AI",
            f"   Solusi KB: {'Dicoba - gagal' if session.tried_kb_solution else 'Tidak tersedia untuk kategori ini'}",
            f"   Status: Dieskalasi ke tim support",
            f"   Jumlah pesan: {session.message_count}",
        ]
        
        # Section 2: Last conversation messages (max 5)
        if session.conversation_history:
            body_parts.append("")
            body_parts.append("💬 RIWAYAT PERCAKAPAN (5 terakhir)")
            body_parts.append("━" * 30)
            recent_msgs = session.conversation_history[-5:]
            for msg in recent_msgs:
                sender = "User" if msg.get('sender') == 'user' else 'Bot'
                text = msg.get('message', '')[:120]
                body_parts.append(f"   [{sender}] {text}")
        
        message_body = "\n".join(body_parts)
        
        # Determine priority from severity
        priority_map = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        priority = priority_map.get(severity, 3)
        
        # Create ticket in osTicket
        ticket_request = CreateTicketRequest(
            name=session.driver_name or user_name,
            email=f"{phone_number}@whatsapp.tramos.id",
            subject=subject,
            message=message_body.strip(),
            source="whatsapp",
            ip="127.0.0.1"
        )
        
        result = await osticket_service.create_ticket(ticket_request)
        
        if result.success:
            session.ticket_id = result.ticket_id
            session.ticket_created = True
            session.current_state = DialogState.CLOSED
            
            response = (
                f"✅ **Tiket Berhasil Dibuat!**\n\n"
                f"📌 Nomor Tiket: #{result.ticket_id}\n"
                f"🏷️ Kategori: {session.problem_category}\n"
                f"🚗 Equipment: {session.vehicle_unit}\n"
                f"📍 Lokasi: {session.location}\n"
                f"⏰ Waktu: {session.issue_time}\n\n"
                f"Tim support TRAMOS akan segera menangani masalah Anda.\n"
                f"Kami akan menghubungi Anda berdasarkan detail yang Anda berikan.\n\n"
                f"Terima kasih telah melaporkan! 🙏"
            )
            
            session.add_message(sender="bot", message=response, intent="ticket_created", category=session.problem_category)
            
            # Save session to database with ticket ID and closed state
            get_session_manager().save_session(session)
            
            # ===== DB TRACKING: ticket + resolution + analytics =====
            _user_id = db_tracker.get_or_create_user(phone_number, session.driver_name)
            _conv_id = getattr(session, '_db_conversation_id', None)
            if _user_id and _conv_id:
                try:
                    osticket_id_int = int(result.ticket_id) if result.ticket_id else None
                except (ValueError, TypeError):
                    osticket_id_int = None
                
                # Create ticket record
                _ticket_id = db_tracker.create_ticket_record(
                    user_id=_user_id,
                    phone_number=phone_number,
                    conversation_id=_conv_id,
                    osticket_id=osticket_id_int,
                    subject=subject,
                    description=message_body.strip(),
                    category=session.problem_category or "Service",
                    priority=severity,
                )
                
                # Create resolution record
                if _ticket_id:
                    conv_duration = (session.last_activity - session.created_at).total_seconds() / 60
                    db_tracker.create_resolution(
                        ticket_id=_ticket_id,
                        resolution_type="escalated",
                        resolution_notes=f"Escalated via WhatsApp. KB solution {'tried' if session.tried_kb_solution else 'not available'}.",
                        ai_attempted=session.tried_kb_solution,
                        ai_successful=False,
                        resolution_time_minutes=int(conv_duration),
                    )
                
                # Increment user ticket count
                db_tracker.increment_user_tickets(phone_number)
                
                # Update user profile
                db_tracker.update_user_profile(phone_number, session.problem_category, issue_resolved=False)
                
                # Log ticket analytics
                db_tracker.log_analytics("ticket_volume", 1.0, session.problem_category or "Service",
                    conversation_id=_conv_id, ticket_id=_ticket_id)
                
                # Link ticket to conversation record
                if _ticket_id:
                    db_tracker.link_ticket_to_conversation(_conv_id, _ticket_id)
                
                # Update conversation state to closed
                db_tracker.update_conversation_state(_conv_id, "closed",
                    category=session.problem_category, intent="ticket_created")
                
                # Update dashboard
                db_tracker.update_dashboard_summary()
            
            logger.info(f"✅ Ticket #{result.ticket_id} created from session {session.session_id}")
            return response
        else:
            # Ticket creation failed - increment retry counter
            session.ticket_retry_count = getattr(session, 'ticket_retry_count', 0) + 1
            session.current_state = DialogState.CONFIRMING_DETAILS

            # Escape hatch: jika sudah 2x gagal, jangan terus retry
            if session.ticket_retry_count >= 2:
                escape_message = (
                    f"⚠️ Sistem pencatatan laporan sedang mengalami gangguan.\n\n"
                    f"Data laporan Anda sudah tersimpan di sistem kami:\n"
                    f"• Nama: {session.driver_name or 'N/A'}\n"
                    f"• Masalah: {session.problem_description[:100] if session.problem_description else 'N/A'}...\n"
                    f"• Unit: {session.vehicle_unit or 'N/A'}\n"
                    f"• Lokasi: {session.location or 'N/A'}\n\n"
                    f"Tim TRAMOS akan tetap menghubungi Anda berdasarkan data yang sudah dikumpulkan.\n"
                    f"Atau hubungi langsung: *admin@tramos.id* atau *0812-xxxx-xxxx*\n\n"
                    f"Terima kasih atas kesabarannya. 🙏"
                )
                session.current_state = DialogState.CLOSED
                session.add_message(sender="bot", message=escape_message, intent="escape_hatch", category=None)
                get_session_manager().save_session(session)
                logger.warning(f"Escape hatch triggered for {phone_number} after {session.ticket_retry_count} failed retries")
                return escape_message

            # First failure: give retry option
            user_facing_error = (
                f"❌ Maaf {session.driver_name or 'Bapak/Ibu'}, laporan belum bisa dibuat menjadi tiket saat ini.\n\n"
                f"Data laporan Anda tetap tersimpan di percakapan ini. Tim TRAMOS tetap bisa menindaklanjuti "
                f"berdasarkan detail yang sudah Anda kirim.\n\n"
                f"Silakan kirim *ya* untuk mencoba lagi, atau hubungi support TRAMOS jika kondisi di lapangan urgent."
            )
            session.add_message(sender="bot", message=user_facing_error, intent="error", category=None)

            # Save failed attempt to database
            get_session_manager().save_session(session)

            logger.error(f"Failed to create ticket (attempt {session.ticket_retry_count}): {result.error}")
            return user_facing_error
    
    except Exception as e:
        logger.error(f"Error in ticket creation: {e}", exc_info=True)
        session.ticket_retry_count = getattr(session, 'ticket_retry_count', 0) + 1
        session.current_state = DialogState.CONFIRMING_DETAILS

        # Escape hatch: jika sudah 2x gagal, jangan terus retry
        if session.ticket_retry_count >= 2:
            escape_message = (
                f"⚠️ Sistem pencatatan laporan sedang mengalami gangguan.\n\n"
                f"Data laporan Anda sudah tersimpan di sistem kami:\n"
                f"• Nama: {session.driver_name or 'N/A'}\n"
                f"• Masalah: {session.problem_description[:100] if session.problem_description else 'N/A'}...\n"
                f"• Unit: {session.vehicle_unit or 'N/A'}\n"
                f"• Lokasi: {session.location or 'N/A'}\n\n"
                f"Tim TRAMOS akan tetap menghubungi Anda berdasarkan data yang sudah dikumpulkan.\n"
                f"Atau hubungi langsung: *admin@tramos.id* atau *0812-xxxx-xxxx*\n\n"
                f"Terima kasih atas kesabarannya. 🙏"
            )
            session.current_state = DialogState.CLOSED
            session.add_message(sender="bot", message=escape_message, intent="escape_hatch", category=None)
            get_session_manager().save_session(session)
            logger.warning(f"Escape hatch triggered (exception) for {phone_number} after {session.ticket_retry_count} failed attempts")
            return escape_message

        user_facing_error = (
            f"❌ Maaf, laporan belum bisa dibuat menjadi tiket saat ini.\n\n"
            f"Data laporan Anda tetap tersimpan di percakapan ini. Silakan kirim *ya* untuk mencoba lagi, "
            f"atau hubungi support TRAMOS jika kondisi di lapangan urgent."
        )
        session.add_message(sender="bot", message=user_facing_error, intent="error", category=None)
        get_session_manager().save_session(session)
        return user_facing_error
