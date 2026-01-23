"""WhatsApp messaging service for sending responses"""
import httpx
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for sending messages via WhatsApp (async with httpx)"""
    
    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.phone_id = settings.WHATSAPP_PHONE_ID
    
    def is_configured(self) -> bool:
        """Check if WhatsApp API is properly configured"""
        return bool(self.api_url and self.api_token and self.phone_id)
    
    async def send_message(self, phone_number: str, message_text: str) -> bool:
        """
        Send a text message to a WhatsApp user (async)
        
        Args:
            phone_number: Recipient phone number (with country code)
            message_text: Message content to send
        
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("WhatsApp service not configured - message not sent")
            return False
        
        try:
            # Format phone number (remove special characters)
            clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
            
            # WhatsApp API endpoint for sending messages
            url = f"{self.api_url}/{self.phone_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            logger.debug(f"Sending WhatsApp message to {phone_number}")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
            
            logger.debug(f"WhatsApp API response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
        
        except httpx.TimeoutException:
            logger.error("Request to WhatsApp API timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return False
    
    def send_message_sync(self, phone_number: str, message_text: str) -> bool:
        """
        Send a text message to a WhatsApp user (sync version for backward compatibility)
        
        Args:
            phone_number: Recipient phone number (with country code)
            message_text: Message content to send
        
        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("WhatsApp service not configured - message not sent")
            return False
        
        try:
            # Format phone number (remove special characters)
            clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
            
            # WhatsApp API endpoint for sending messages
            url = f"{self.api_url}/{self.phone_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            logger.debug(f"Sending WhatsApp message to {phone_number}")
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)
            
            logger.debug(f"WhatsApp API response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"✅ Message sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.status_code} - {response.text}")
                return False
        
        except httpx.TimeoutException:
            logger.error("Request to WhatsApp API timed out")
            return False
        except httpx.RequestError as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {str(e)}")
            return False


# Singleton instance
whatsapp_service = WhatsAppService()
