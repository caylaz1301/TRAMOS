"""
WhatsApp Business API Webhook Handler
Handles incoming messages dari Meta WhatsApp Business Platform
Multi-turn conversation dengan AI intent detection dan KB troubleshooting
"""

import logging
import json
from typing import Optional, Tuple
from fastapi import APIRouter, Request, Depends
from fastapi.responses import Response

from app.config import settings
from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING, get_kb_category
from app.utils.ai_logic import ai_engine
from app.services.osticket_service import osticket_service
from app.services.whatsapp_service import whatsapp_service
from app.schemas.ticket import CreateTicketRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="", tags=["whatsapp"])


# ============================================================================
# WEBHOOK VERIFICATION (GET request)
# ============================================================================
@router.get("/webhook/whatsapp")
async def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None,
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
    2. Detect intent menggunakan AI (Gemini) + fallback keyword
    3. Generate response berdasarkan intent dan KB
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
        
        messages = value.get("messages", [])
        if not messages:
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
        
        # ====== SEND RESPONSE VIA WHATSAPP ======
        if whatsapp_service.is_configured():
            send_success = await whatsapp_service.send_message(from_phone, response_text)
            if send_success:
                logger.info(f"✅ Response sent to {from_phone}")
            else:
                logger.warning(f"⚠️ Failed to send response to {from_phone}")
        else:
            logger.debug(f"📝 Response (not sent): {response_text[:100]}")
        
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

async def process_message_with_ai(
    message_body: str, 
    user_name: str, 
    phone_number: str
) -> str:
    """
    Process message menggunakan AI intent detection + KB troubleshooting
    
    Intent types:
    - greeting: Salam pembuka
    - troubleshooting: Masalah teknis yang perlu solusi
    - escalate: User minta bicara dengan manusia
    - resolved: Masalah sudah selesai
    - unresolved: Solusi tidak berhasil
    - ticket: Minta buat tiket support
    - unknown: Tidak terdeteksi
    """
    message_lower = message_body.lower()
    
    # ===== DETECT INTENT WITH AI =====
    intent, category = ai_engine.detect_intent(message_body)
    logger.info(f"🤖 Intent: {intent}, Category: {category}")
    
    # ===== HANDLE BASED ON INTENT =====
    
    # 1. Greeting
    if is_greeting(message_lower):
        return generate_greeting_response(user_name)
    
    # 2. Resolved - user confirms issue is fixed
    if intent == "resolved":
        return generate_resolved_response(user_name)
    
    # 3. Unresolved - solution didn't work
    if intent == "unresolved":
        return generate_unresolved_response(user_name, category)
    
    # 4. Escalate - user wants human support
    if intent == "escalate" or is_escalation_request(message_lower):
        return await handle_escalation(user_name, phone_number, message_body, category)
    
    # 5. Ticket creation request
    if is_ticket_request(message_lower):
        return await handle_ticket_creation(user_name, phone_number, message_body)
    
    # 6. Troubleshooting - technical issue
    if intent == "troubleshooting" and category:
        return generate_troubleshooting_response(category, user_name)
    
    # 7. Try KB matching as fallback
    words = message_lower.split()
    kb_category = get_kb_category(words)
    if kb_category:
        return generate_kb_response(kb_category, user_name)
    
    # 8. Status check
    if is_status_check(message_lower):
        return "✅ Sistem sedang berjalan normal.\n\nAda masalah spesifik? Cerita dong detailnya! 💪"
    
    # 9. Fallback
    return generate_fallback_response(user_name)


# ============================================================================
# INTENT DETECTION HELPERS
# ============================================================================

def is_greeting(message: str) -> bool:
    """Check if message is a greeting"""
    greetings = [
        "halo", "hi", "hello", "hey", "hai",
        "pagi", "siang", "sore", "malam",
        "apa kabar", "assalamu", "selamat"
    ]
    return any(g in message for g in greetings) and len(message.split()) <= 5


def is_escalation_request(message: str) -> bool:
    """Check if user wants to talk to human"""
    keywords = [
        "operator", "manusia", "human", "agent", "cs",
        "customer service", "tolong bantu", "bicara dengan"
    ]
    return any(kw in message for kw in keywords)


def is_ticket_request(message: str) -> bool:
    """Check if user wants to create a ticket"""
    keywords = ["tiket", "ticket", "buat laporan", "lapor masalah"]
    return any(kw in message for kw in keywords)


def is_status_check(message: str) -> bool:
    """Check if user is asking for system status"""
    keywords = ["status", "check", "test", "ping"]
    return any(kw in message for kw in keywords) and len(message.split()) <= 3


# ============================================================================
# RESPONSE GENERATORS
# ============================================================================

def generate_greeting_response(user_name: str) -> str:
    """Generate greeting response with menu"""
    return (
        f"Halo {user_name}! 👋\n\n"
        f"Selamat datang di TRAMOS Support. Ada yang bisa kami bantu?\n\n"
        f"Silakan ceritakan masalah Anda atau pilih kategori:\n"
        f"• 🗺️ GPS/Tracking\n"
        f"• 📡 Koneksi Internet\n"
        f"• 🔧 Device/Hardware\n"
        f"• 📱 Aplikasi\n"
        f"• 📝 Buat Tiket Support"
    )


def generate_resolved_response(user_name: str) -> str:
    """Generate response when issue is resolved"""
    return (
        f"Senang bisa membantu, {user_name}! 🎉\n\n"
        f"Jika ada masalah lain, jangan ragu untuk menghubungi kami.\n\n"
        f"Terima kasih telah menggunakan TRAMOS Support! 🙏"
    )


def generate_unresolved_response(user_name: str, category: Optional[str]) -> str:
    """Generate response when solution didn't work"""
    response = (
        f"Maaf solusi sebelumnya tidak berhasil, {user_name}. 😔\n\n"
    )
    
    if category:
        response += (
            f"Mari kita coba langkah lanjutan untuk masalah {category}:\n\n"
            f"1. Restart perangkat sepenuhnya\n"
            f"2. Periksa semua koneksi kabel\n"
            f"3. Pastikan firmware sudah terupdate\n\n"
        )
    
    response += (
        f"Jika masih bermasalah, ketik 'tiket' untuk eskalasi ke tim support."
    )
    return response


async def handle_escalation(
    user_name: str, 
    phone_number: str, 
    message: str,
    category: Optional[str]
) -> str:
    """Handle escalation to human support by creating ticket"""
    subject = f"Eskalasi: {category or 'General'} - {user_name}"
    
    ticket_request = CreateTicketRequest(
        name=user_name,
        email=f"{phone_number}@whatsapp.tramos.id",
        subject=subject,
        message=f"Eskalasi dari WhatsApp:\n\nPesan terakhir: {message}\nKategori: {category or 'Tidak terdeteksi'}",
        ip="127.0.0.1"
    )
    
    result = await osticket_service.create_ticket(ticket_request)
    
    if result.success:
        return (
            f"✅ Permintaan eskalasi berhasil, {user_name}!\n\n"
            f"Nomor Tiket: #{result.ticket_id}\n\n"
            f"Tim support kami akan segera menghubungi Anda.\n"
            f"Terima kasih atas kesabarannya! 🙏"
        )
    else:
        return (
            f"Maaf {user_name}, gagal membuat tiket eskalasi.\n\n"
            f"Silakan hubungi support langsung atau coba lagi nanti."
        )


async def handle_ticket_creation(
    user_name: str,
    phone_number: str, 
    message: str
) -> str:
    """Create support ticket from WhatsApp"""
    ticket_request = CreateTicketRequest(
        name=user_name,
        email=f"{phone_number}@whatsapp.tramos.id",
        subject=f"WhatsApp Support: {user_name}",
        message=f"Dari WhatsApp ({phone_number}):\n\n{message}",
        ip="127.0.0.1"
    )
    
    result = await osticket_service.create_ticket(ticket_request)
    
    if result.success:
        return (
            f"✅ Tiket support berhasil dibuat!\n\n"
            f"Nomor Tiket: #{result.ticket_id}\n\n"
            f"Tim kami akan menghubungi Anda segera.\n"
            f"Terima kasih, {user_name}! 🙏"
        )
    else:
        logger.error(f"Failed to create ticket: {result.error}")
        return "❌ Maaf, gagal membuat tiket. Silakan coba lagi."


def generate_troubleshooting_response(category: str, user_name: str) -> str:
    """Generate troubleshooting response based on AI-detected category"""
    
    # Map AI category to KB
    category_map = {
        "GPS": "gps",
        "Camera": "camera",
        "Battery": "battery",
        "Connectivity": "connectivity",
    }
    
    kb_key = category_map.get(category, category.lower())
    kb_data = KB_TROUBLESHOOTING.get(kb_key)
    
    if kb_data:
        return generate_kb_response(kb_data, user_name)
    
    # Generic troubleshooting
    return (
        f"Saya mendeteksi masalah {category}, {user_name}.\n\n"
        f"Langkah umum:\n"
        f"1. Restart perangkat\n"
        f"2. Periksa koneksi dan kabel\n"
        f"3. Pastikan power supply stabil\n\n"
        f"Apakah langkah ini membantu? Balas 'sudah' atau 'masih error'."
    )


def generate_kb_response(kb_data: dict, user_name: str) -> str:
    """Generate response from Knowledge Base"""
    first_response = kb_data.get("first_response", "")
    steps = kb_data.get("troubleshooting_steps", [])
    
    response = f"{first_response}\n\n"
    
    # Add troubleshooting steps
    if steps:
        response += "📋 *Langkah-langkah:*\n\n"
        for step in steps[:2]:  # First 2 steps only
            step_num = step.get("step", 1)
            step_title = step.get("title", "")
            instructions = step.get("instructions", [])
            
            response += f"*Step {step_num}: {step_title}*\n"
            for instruction in instructions[:3]:  # Max 3 instructions per step
                response += f"  • {instruction}\n"
            response += "\n"
    
    response += "Setelah selesai, balas '*sudah*' atau '*masih error*' ✅"
    
    return response


def generate_fallback_response(user_name: str) -> str:
    """Generate fallback response when intent is unclear"""
    return (
        f"Maaf {user_name}, saya belum sepenuhnya paham. 🤔\n\n"
        f"Bisa jelaskan lebih detail masalahnya?\n\n"
        f"Atau pilih kategori:\n"
        f"• 🗺️ GPS/Tracking\n"
        f"• 📡 Koneksi/Internet\n"
        f"• 🔧 Device/Hardware\n"
        f"• 📱 Aplikasi\n"
        f"• 📝 Buat Tiket"
    )
