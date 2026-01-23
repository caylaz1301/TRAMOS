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
    
    # ===== META WHATSAPP BUSINESS API =====
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "tramos_webhook_token_change_me")
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "tramos_webhook_token_change_me")
    
    # Webhook endpoint
    WEBHOOK_PATH: str = "/webhook/whatsapp"
    
    # ===== osTicket Configuration =====
    OSTICKET_BASE_URL: str = os.getenv("OSTICKET_BASE_URL", "")
    OSTICKET_API_KEY: str = os.getenv("OSTICKET_API_KEY", "")
    OSTICKET_API_URL: str = os.getenv("OSTICKET_API_URL", "")  # Alias for BASE_URL
    OSTICKET_TICKETS_ENDPOINT: str = os.getenv("OSTICKET_TICKETS_ENDPOINT", "/api/tickets.json")
    DEFAULT_TICKET_IP: str = os.getenv("DEFAULT_TICKET_IP", "127.0.0.1")
    DEFAULT_TICKET_PRIORITY: str = os.getenv("DEFAULT_TICKET_PRIORITY", "normal")
    DEFAULT_TICKET_SOURCE: str = "WhatsApp"
    
    # ===== Database Configuration =====
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/tramos_db")
    
    # ===== AI / LLM Configuration =====
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_PROJECT_ID: str = os.getenv("GEMINI_PROJECT_ID", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    USE_LLM: bool = os.getenv("USE_LLM", os.getenv("AI_USE_LLM", "true")).lower() == "true"
    AI_CONFIDENCE_THRESHOLD: float = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.7"))
    
    # ===== CORS Configuration =====
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")


settings = Settings()

