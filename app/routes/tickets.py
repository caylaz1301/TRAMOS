"""Ticket management routes"""
import logging
from fastapi import APIRouter, HTTPException, Query
from app.schemas.ticket import CreateTicketRequest, CreateTicketResponse
from app.services.osticket_service import osticket_service
from app.services.chatbot.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=CreateTicketResponse)
async def create_ticket(ticket_data: CreateTicketRequest) -> CreateTicketResponse:
    """
    Create a new ticket in osTicket
    
    This endpoint wraps the osTicket API to provide a consistent interface
    for ticket creation from WhatsApp conversations.
    
    Args:
        ticket_data: Ticket information (name, email, subject, message, priority)
    
    Returns:
        CreateTicketResponse with success status and ticket ID
    """
    logger.info(f"Received ticket creation request for {ticket_data.email}")
    
    if not osticket_service.is_configured():
        logger.error("osTicket service is not properly configured")
        raise HTTPException(
            status_code=500,
            detail="osTicket service is not configured"
        )
    
    logger.info(f"Creating ticket for {ticket_data.email}: {ticket_data.subject}")
    
    # Use async version
    result = await osticket_service.create_ticket(ticket_data)
    
    logger.info(f"Ticket creation result: success={result.success}, ticket_id={result.ticket_id}, message={result.message}")
    
    if not result.success:
        logger.error(f"Failed to create ticket: {result.error}")
        raise HTTPException(status_code=500, detail=result.message)
    
    logger.info(f"Successfully returning ticket response: {result}")
    return result


@router.post("/whatsapp/{phone_number}")
async def create_ticket_from_whatsapp(
    phone_number: str,
    email: str = Query(..., description="Requester email"),
    subject: str = Query(..., description="Ticket subject"),
    message: str = Query(..., description="Ticket message"),
) -> CreateTicketResponse:
    """
    Create a ticket from a WhatsApp conversation and notify the user
    
    Args:
        phone_number: User's WhatsApp phone number (with country code)
        email: Requester email for ticket
        subject: Ticket subject
        message: Ticket message/description
    
    Returns:
        CreateTicketResponse with success status and ticket ID
    """
    logger.info(f"Creating ticket from WhatsApp conversation: {phone_number}")
    
    # Extract name from email prefix
    name = email.split("@")[0].replace(".", " ").title() if email else "WhatsApp User"
    
    # Create ticket data
    ticket_data = CreateTicketRequest(
        name=name,
        email=email,
        subject=subject,
        message=message,
        ip="127.0.0.1"  # Default IP for webhook sources
    )
    
    # Create ticket (async)
    result = await osticket_service.create_ticket(ticket_data)
    
    # Notify user if ticket was created successfully (async)
    if result.success and whatsapp_service.is_configured():
        notification_text = (
            f"✅ Tiket support Anda telah berhasil dibuat.\n\n"
            f"📌 Nomor Tiket: #{result.ticket_id}\n\n"
            f"Tim support kami akan segera merespons. Simpan nomor tiket ini untuk referensi."
        )
        await whatsapp_service.send_message(phone_number, notification_text)
        logger.info(f"✅ Notified user {phone_number} about ticket {result.ticket_id}")
    
    return result


@router.get("/health")
async def ticket_health_check() -> dict:
    """
    Health check endpoint for ticket service
    
    Returns osTicket service configuration status
    """
    return {
        "status": "healthy",
        "osticket_configured": osticket_service.is_configured(),
        "osticket_url": osticket_service.base_url if osticket_service.is_configured() else "not configured",
        "whatsapp_configured": whatsapp_service.is_configured(),
    }
