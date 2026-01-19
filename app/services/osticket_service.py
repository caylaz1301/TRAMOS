"""osTicket API integration service"""
import requests
import logging
from typing import Optional, Dict, Any
from app.config import settings
from app.schemas.ticket import CreateTicketRequest, CreateTicketResponse

logger = logging.getLogger(__name__)


class osTicketService:
    """Service for interacting with osTicket API"""
    
    def __init__(self):
        self.base_url = settings.OSTICKET_API_URL
        self.api_key = settings.OSTICKET_API_KEY
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
    
    def create_ticket(self, ticket_data: CreateTicketRequest) -> CreateTicketResponse:
        """
        Create a new ticket in osTicket via API
        
        Args:
            ticket_data: Ticket information (name, email, subject, message, etc)
        
        Returns:
            CreateTicketResponse with success status and ticket ID
        """
        try:
            payload = {
                "name": ticket_data.name,
                "email": ticket_data.email,
                "subject": ticket_data.subject,
                "message": ticket_data.message,
                "ip": ticket_data.ip,
                # Note: priority field is not supported by osTicket API
                # It will be set via dashboard if needed
            }
            
            logger.debug(f"Creating ticket with payload: {payload}")
            logger.debug(f"osTicket endpoint: {self.base_url}/tickets.json")
            
            response = requests.post(
                f"{self.base_url}/tickets.json",
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            logger.debug(f"osTicket API response status: {response.status_code}")
            logger.debug(f"osTicket API response body: {response.text}")
            
            # osTicket API returns 201 on success
            if response.status_code == 201:
                # osTicket API returns plain text ticket ID
                try:
                    ticket_id = response.text.strip()
                    logger.info(f"Ticket created successfully: {ticket_id}")
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
                except:
                    error_msg = f"osTicket API returned {response.status_code}"
                logger.error(error_msg)
                return CreateTicketResponse(
                    success=False,
                    message="Failed to create ticket",
                    error=error_msg
                )
        
        except requests.exceptions.Timeout:
            error_msg = "Request to osTicket API timed out"
            logger.error(error_msg)
            return CreateTicketResponse(
                success=False,
                message="Failed to create ticket",
                error=error_msg
            )
        except requests.exceptions.RequestException as e:
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
    
    def is_configured(self) -> bool:
        """Check if osTicket API is properly configured"""
        return bool(self.base_url and self.api_key)


# Singleton instance
osticket_service = osTicketService()
