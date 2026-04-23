"""
WhatsApp messaging service
Sandbox + Production Ready Version
"""

import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp Cloud API Service
    Supports:
    - Sandbox (Template Only)
    - Production (Free Text)
    """

    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.phone_id = settings.WHATSAPP_PHONE_ID

        # Set this in .env
        # MODE = sandbox / production
        self.mode = getattr(settings, "WHATSAPP_MODE", "sandbox")

    # ===============================
    # CONFIG CHECK
    # ===============================
    def is_configured(self) -> bool:
        return bool(self.api_url and self.api_token and self.phone_id)

    # ===============================
    # PHONE NORMALIZATION
    # ===============================
    def normalize_phone(self, phone: str) -> str:

        phone = phone.strip()
        phone = phone.replace(" ", "").replace("-", "")

        if phone.startswith("+"):
            phone = phone[1:]

        if phone.startswith("08"):
            phone = "628" + phone[2:]

        elif phone.startswith("8"):
            phone = "62" + phone

        elif phone.startswith("62"):
            pass

        else:
            raise ValueError(f"Invalid phone format: {phone}")

        return phone

    # ===============================
    # TEMPLATE MESSAGE (SANDBOX)
    # ===============================
    async def send_template(
        self,
        phone_number: str,
        template_name: str = "hello_world",
        language: str = "en_US"
    ) -> bool:

        try:
            phone = self.normalize_phone(phone_number)

            url = f"{self.api_url}/{self.phone_id}/messages"

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language
                    }
                }
            }

            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.post(url, json=payload, headers=headers)

            if res.status_code == 200:
                logger.info(f"✅ Template sent to {phone}")
                return True

            logger.error(f"❌ Template failed: {res.text}")
            return False

        except Exception as e:
            logger.error(f"❌ Template error: {str(e)}")
            return False

    # ===============================
    # TEXT MESSAGE (PRODUCTION)
    # ===============================
    async def send_text(
        self,
        phone_number: str,
        message_text: str
    ) -> bool:

        try:
            phone = self.normalize_phone(phone_number)

            url = f"{self.api_url}/{self.phone_id}/messages"

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": phone,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }

            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.post(url, json=payload, headers=headers)

            if res.status_code == 200:
                logger.info(f"✅ Text sent to {phone}")
                try:
                    response_json = res.json()
                    logger.info(f"✅ Message ID: {response_json.get('messages', [{}])[0].get('id', 'N/A')}")
                except:
                    pass
                return True

            logger.error(f"❌ Text failed (Status {res.status_code}): {res.text}")
            return False

        except Exception as e:
            logger.error(f"❌ Text error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    # ===============================
    # MAIN SENDER (AUTO MODE)
    # ===============================
    async def send_message(
        self,
        phone_number: str,
        message_text: str
    ) -> bool:

        if not self.is_configured():
            logger.warning("WhatsApp not configured")
            return False

        logger.info(f"📨 Send mode: {self.mode}")

        # SANDBOX MODE → TEMPLATE
        if self.mode == "sandbox":
            return await self.send_template(phone_number)

        # PRODUCTION MODE → TEXT
        return await self.send_text(phone_number, message_text)

    # ===============================
    # SYNC BACKUP
    # ===============================
    def send_message_sync(
        self,
        phone_number: str,
        message_text: str
    ) -> bool:

        import asyncio
        return asyncio.run(
            self.send_message(phone_number, message_text)
        )


# Singleton
whatsapp_service = WhatsAppService()
