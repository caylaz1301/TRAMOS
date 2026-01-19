"""Ticket management routes"""
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.ticket import CreateTicketRequest, CreateTicketResponse
from app.services import osticket_service

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
    logger.debug(f"Ticket data: {ticket_data.model_dump()}")
    
    result = osticket_service.create_ticket(ticket_data)
    
    logger.info(f"Ticket creation result: success={result.success}, ticket_id={result.ticket_id}, message={result.message}")
    
    if not result.success:
        logger.error(f"Failed to create ticket: {result.error}")
        raise HTTPException(status_code=500, detail=result.message)
    
    logger.info(f"Successfully returning ticket response: {result}")
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
        "osticket_url": osticket_service.base_url if osticket_service.is_configured() else "not configured"
    }
