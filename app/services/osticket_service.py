"""osTicket API integration service (async with httpx)"""
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.config import settings
from app.schemas.ticket import CreateTicketRequest, CreateTicketResponse
from app.services.notification_service import email_notification_service

logger = logging.getLogger(__name__)


class osTicketService:
    """Service for interacting with osTicket API (async with httpx)"""
    
    def __init__(self):
        self.base_url = settings.OSTICKET_BASE_URL or settings.OSTICKET_API_URL
        self.api_key = settings.OSTICKET_API_KEY
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
    
    async def create_ticket(self, ticket_data: CreateTicketRequest) -> CreateTicketResponse:
        """
        Create a new ticket in osTicket via API (async)
        
        Args:
            ticket_data: Ticket information (name, email, subject, message, etc)
        
        Returns:
            CreateTicketResponse with success status and ticket ID
        """
        try:
            # osTicket API requires valid registered email
            # Fallback to admin email if provided email is not registered in osTicket
            email = ticket_data.email
            # Common pattern: WhatsApp tickets use whatsapp.tramos.id domain
            if email.endswith("@whatsapp.tramos.id"):
                email = "adm.helpdesk.tramos@gmail.com"
            
            payload = {
                "name": ticket_data.name,
                "email": email,
                "subject": ticket_data.subject,
                "message": ticket_data.message,
                "source": "api",  # osTicket API only accepts "api" as source
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/tickets.json",
                    json=payload,
                    headers=self.headers
                )
            
            # osTicket API returns 201 on success
            if response.status_code == 201:
                # osTicket API returns plain text ticket ID
                try:
                    ticket_id = response.text.strip()
                    logger.info(f"✅ Ticket created successfully: {ticket_id}")
                    
                    # Send email notification to operators
                    ticket_notification_data = {
                        'ticket_id': ticket_id,
                        'subject': ticket_data.subject,
                        'user_name': ticket_data.name,
                        'user_contact': getattr(ticket_data, 'phone', ticket_data.email),
                        'category': getattr(ticket_data, 'category', 'General'),
                        'priority': self._convert_priority_to_string(getattr(ticket_data, 'priority', 'normal')),
                        'message': ticket_data.message,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Send email asynchronously (non-blocking)
                    try:
                        email_notification_service.send_new_ticket_notification(ticket_notification_data)
                    except Exception as email_error:
                        logger.warning(f"⚠️ Failed to send email notification: {str(email_error)}")
                        # Don't fail ticket creation if email fails
                    
                    return CreateTicketResponse(
                        success=True,
                        ticket_id=str(ticket_id),
                        message=f"Ticket #{ticket_id} created successfully"
                    )
                except Exception as parse_error:
                    error_msg = f"Failed to parse response: {str(parse_error)}, raw: {response.text}"
                    logger.error(error_msg)
                    return CreateTicketResponse(
                        success=False,
                        message="Failed to parse ticket response",
                        error=error_msg
                    )
            else:
                try:
                    error_msg = f"osTicket API returned {response.status_code}: {response.text}"
                except Exception:
                    error_msg = f"osTicket API returned {response.status_code}"
                logger.error(error_msg)
                return CreateTicketResponse(
                    success=False,
                    message="Failed to create ticket",
                    error=error_msg
                )
        
        except httpx.TimeoutException:
            error_msg = "Request to osTicket API timed out"
            logger.error(error_msg)
            return CreateTicketResponse(
                success=False,
                message="Failed to create ticket",
                error=error_msg
            )
        except httpx.RequestError as e:
            error_msg = f"Request to osTicket API failed: {str(e)}"
            logger.error(error_msg)
            return CreateTicketResponse(
                success=False,
                message="Failed to create ticket",
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Unexpected error during ticket creation: {str(e)}"
            logger.error(error_msg)
            return CreateTicketResponse(
                success=False,
                message="Failed to create ticket",
                error=error_msg
            )
    
    def create_ticket_sync(self, ticket_data: CreateTicketRequest) -> CreateTicketResponse:
        """
        Create a new ticket in osTicket via API (sync version for backward compatibility)
        """
        try:
            payload = {
                "name": ticket_data.name,
                "email": ticket_data.email,
                "subject": ticket_data.subject,
                "message": ticket_data.message,
                "ip": ticket_data.ip,
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.base_url}/tickets.json",
                    json=payload,
                    headers=self.headers
                )
            
            if response.status_code == 201:
                ticket_id = response.text.strip()
                logger.info(f"✅ Ticket created successfully: {ticket_id}")
                return CreateTicketResponse(
                    success=True,
                    ticket_id=str(ticket_id),
                    message=f"Ticket #{ticket_id} created successfully"
                )
            else:
                error_msg = f"osTicket API returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                return CreateTicketResponse(
                    success=False,
                    message="Failed to create ticket",
                    error=error_msg
                )
        
        except Exception as e:
            error_msg = f"Error during ticket creation: {str(e)}"
            logger.error(error_msg)
            return CreateTicketResponse(
                success=False,
                message="Failed to create ticket",
                error=error_msg
            )
    
    def is_configured(self) -> bool:
        """Check if osTicket API is properly configured"""
        return bool(self.base_url and self.api_key)
    
    def _convert_priority_to_string(self, priority) -> str:
        """Convert priority (int or string) to readable string"""
        if isinstance(priority, int):
            priority_map = {
                1: "critical",
                2: "high",
                3: "normal",
                4: "low"
            }
            return priority_map.get(priority, "normal")
        return str(priority).lower()


# Singleton instance
osticket_service = osTicketService()
