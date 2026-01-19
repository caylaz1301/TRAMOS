"""Configuration and environment variables"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "TRAMOS AI Support System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # osTicket API Configuration
    OSTICKET_API_URL: str = os.getenv("OSTICKET_API_URL", "http://localhost/osticket/api")
    OSTICKET_API_KEY: str = os.getenv("OSTICKET_API_KEY", "")
    
    # WhatsApp Configuration (for future provider integration)
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL", "")
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    
    # Webhook Configuration
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "tramos_webhook_token")
    
    # Default ticket settings
    DEFAULT_TICKET_PRIORITY: int = 3  # 1=Urgent, 2=High, 3=Medium, 4=Low
    DEFAULT_TICKET_SOURCE: str = "WhatsApp"
    
    # Client IP for osTicket (used when source is webhook)
    CLIENT_IP: str = os.getenv("CLIENT_IP", "127.0.0.1")


settings = Settings()
