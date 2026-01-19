"""WhatsApp webhook routes"""
import logging
from fastapi import APIRouter, Request, Query, HTTPException
from typing import Dict, Any

from app.config import settings
from app.schemas.whatsapp import WhatsAppWebhookPayload
from app.services import osticket_service, conversation_manager
from app.utils import ai_engine
from app.schemas.ticket import CreateTicketRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None),
    hub_challenge: str = Query(None),
    hub_verify_token: str = Query(None),
) -> str:
    """
    Webhook verification endpoint for WhatsApp
    
    WhatsApp sends verification request to confirm the webhook URL
    """
    if not all([hub_mode, hub_challenge, hub_verify_token]):
        logger.warning("Incomplete webhook verification parameters")
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    if hub_verify_token != settings.WEBHOOK_VERIFY_TOKEN:
        logger.warning(f"Invalid webhook verify token: {hub_verify_token}")
        raise HTTPException(status_code=403, detail="Invalid verify token")
    
    if hub_mode != "subscribe":
        logger.warning(f"Invalid hub mode: {hub_mode}")
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    logger.info("WhatsApp webhook verified successfully")
    return hub_challenge


@router.post("/whatsapp")
async def handle_whatsapp_webhook(payload: WhatsAppWebhookPayload) -> Dict[str, Any]:
    """
    Handle incoming WhatsApp messages
    
    Flow:
    1. Extract message and sender info
    2. Detect user intent (troubleshooting, escalation, etc)
    3. Respond with appropriate troubleshooting steps or create ticket
    4. Track conversation state
    """
    try:
        if payload.object != "whatsapp_business_account":
            logger.warning(f"Invalid payload object: {payload.object}")
            return {"status": "ignored"}
        
        # Process each entry (usually one)
        for entry in payload.entry:
            logger.debug(f"Processing entry: {entry.id}")
            
            for change in entry.changes:
                if change.field != "messages":
                    continue
                
                # Extract message and contact info
                if not change.value.messages:
                    continue
                
                message_obj = change.value.messages[0]
                
                # Only process text messages for now
                if message_obj.type != "text" or not message_obj.text:
                    logger.info(f"Ignoring non-text message: {message_obj.type}")
                    continue
                
                # Extract data
                phone_number = message_obj.from_
                message_text = message_obj.text.body
                message_id = message_obj.id
                
                logger.info(f"Received message from {phone_number}: {message_text}")
                
                # Update conversation state
                conversation = conversation_manager.get_or_create(phone_number)
                
                # Detect intent
                intent, category = ai_engine.detect_intent(message_text)
                logger.debug(f"Intent detected: {intent}, Category: {category}")
                
                # Handle based on intent
                if intent == "resolved":
                    response_text = "Great! I'm glad I could help. Feel free to reach out anytime you need assistance. 👍"
                    conversation_manager.close_conversation(phone_number)
                
                elif intent == "unresolved":
                    response_text = (
                        "I understand. Let me escalate this to our support team. "
                        "Please provide the following details:\n"
                        "1. What exactly is not working?\n"
                        "2. When did this issue start?\n"
                        "3. Any error messages?\n\n"
                        "A support agent will respond shortly."
                    )
                    conversation_manager.update_conversation(
                        phone_number,
                        message_text,
                        status="awaiting_details",
                        category=category
                    )
                
                elif intent == "escalate":
                    response_text = (
                        "I see this is urgent. Creating a support ticket now...\n\n"
                        "Please provide your email address to receive the ticket number and updates."
                    )
                    conversation_manager.update_conversation(
                        phone_number,
                        message_text,
                        status="escalated",
                        category=category
                    )
                
                elif intent == "troubleshooting":
                    response_text = ai_engine.get_troubleshooting_response(category)
                    conversation_manager.update_conversation(
                        phone_number,
                        message_text,
                        status="troubleshooting",
                        category=category
                    )
                
                else:  # unknown intent
                    response_text = (
                        "I want to help you with your issue. Could you please provide more details about "
                        "what's happening? For example:\n"
                        "- GPS/Location issues\n"
                        "- Camera problems\n"
                        "- Network/Connectivity\n"
                        "- Battery issues\n"
                        "- Other technical problems"
                    )
                    conversation_manager.update_conversation(
                        phone_number,
                        message_text,
                        status="initial"
                    )
                
                # TODO: Send response_text back to WhatsApp
                # This will be implemented when integrating with WhatsApp provider
                logger.info(f"Response ready for {phone_number}: {response_text[:50]}...")
        
        return {"status": "processed"}
    
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}
