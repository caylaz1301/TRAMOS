"""Konfigurasi utama aplikasi TRAMOS.

Semua nilai diambil dari environment variable agar konfigurasi lokal, demo,
dan production tidak tercampur di dalam source code.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: str) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return int(default)


def _env_float(name: str, default: str) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def _env_first(*names: str, default: str = "") -> str:
    """Ambil nilai env pertama yang terisi, termasuk format __ dari service lain."""
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _env_int_first(*names: str, default: str) -> int:
    try:
        return int(_env_first(*names, default=default))
    except (TypeError, ValueError):
        return int(default)


class Settings:
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = "TRAMOS AI Support System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = _env_bool("DEBUG", "true")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").strip().lower()

    # ===== META WHATSAPP BUSINESS API =====
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v19.0")
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_MODE: str = os.getenv("WHATSAPP_MODE", "sandbox")  # sandbox or production
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
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/tramos_db")

    # ===== AI / LLM Configuration =====
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_PROJECT_ID: str = os.getenv("GEMINI_PROJECT_ID", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    GEMINI_EMBEDDING_DIMENSIONS: int = _env_int("GEMINI_EMBEDDING_DIMENSIONS", "1536")
    # Provider embedding dipisah dari provider chat. Mendukung env Python
    # (EMBEDDING_*) dan env style .NET (Embedding__*) agar mudah dipakai lintas server.
    EMBEDDING_PROVIDER: str = _env_first("EMBEDDING_PROVIDER", "Embedding__Provider", default="gemini").lower()
    EMBEDDING_MODEL: str = _env_first(
        "EMBEDDING_MODEL",
        "Embedding__Model",
        default=GEMINI_EMBEDDING_MODEL,
    )
    EMBEDDING_DIMENSIONS: int = _env_int_first(
        "EMBEDDING_DIMENSIONS",
        "Embedding__Dimensions",
        default=str(GEMINI_EMBEDDING_DIMENSIONS),
    )
    EMBEDDING_OLLAMA_URL: str = _env_first(
        "EMBEDDING_OLLAMA_URL",
        "Embedding__OllamaUrl",
        default="http://localhost:11434",
    ).rstrip("/")
    EMBEDDING_REQUEST_TIMEOUT_SECONDS: int = _env_int_first(
        "EMBEDDING_REQUEST_TIMEOUT_SECONDS",
        "Embedding__RequestTimeoutSeconds",
        default="180",
    )
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    ANTHROPIC_BASE_URL: str = os.getenv("ANTHROPIC_BASE_URL", "")
    LLM_REQUEST_TIMEOUT_SECONDS: int = _env_int("LLM_REQUEST_TIMEOUT_SECONDS", "60")
    USE_LLM: bool = os.getenv("USE_LLM", os.getenv("AI_USE_LLM", "true")).strip().lower() == "true"
    AI_CONFIDENCE_THRESHOLD: float = _env_float("AI_CONFIDENCE_THRESHOLD", "0.7")

    # ===== Knowledge Base / RAG Configuration =====
    KB_RAG_ENABLED: bool = _env_bool("KB_RAG_ENABLED", "true")
    KB_SOURCE_DIR: str = os.getenv("KB_SOURCE_DIR", "knowledge_base")
    KB_TOP_K: int = _env_int("KB_TOP_K", "5")
    KB_MIN_SCORE: float = _env_float("KB_MIN_SCORE", "0.35")
    KB_PGVECTOR_REQUIRED: bool = _env_bool("KB_PGVECTOR_REQUIRED", "false")
    KB_CONTEXT_MAX_CHARS: int = _env_int("KB_CONTEXT_MAX_CHARS", "4500")

    # ===== Email Notification Configuration =====
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = _env_int("SMTP_PORT", "587")
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@tramos.local")
    SMTP_USE_TLS: bool = _env_bool("SMTP_USE_TLS", "true")
    OPERATOR_EMAILS: list = [email.strip() for email in os.getenv("OPERATOR_EMAILS", "").split(",") if email.strip()]

    # ===== Google OAuth =====
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # ===== Dashboard Auth =====
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "tramos_dashboard_secret_key_change_me")
    DASHBOARD_USERNAME: str = os.getenv("DASHBOARD_USERNAME", "admin")
    DASHBOARD_PASSWORD: str = os.getenv("DASHBOARD_PASSWORD", "")
    DASHBOARD_ENABLE_LEGACY_ADMIN: bool = _env_bool("DASHBOARD_ENABLE_LEGACY_ADMIN", "true")
    TOKEN_EXPIRE_MINUTES: int = _env_int("TOKEN_EXPIRE_MINUTES", "480")

    # ===== CORS Configuration =====
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT in {"production", "prod"}

    def production_warnings(self) -> list[str]:
        """Daftar konfigurasi yang harus diganti sebelum deployment production."""
        warnings = []
        if self.JWT_SECRET_KEY == "tramos_dashboard_secret_key_change_me":
            warnings.append("JWT_SECRET_KEY masih memakai default.")
        if self.DASHBOARD_ENABLE_LEGACY_ADMIN and not self.DASHBOARD_PASSWORD:
            warnings.append("Legacy admin aktif tetapi DASHBOARD_PASSWORD belum diisi.")
        if self.WEBHOOK_VERIFY_TOKEN == "tramos_webhook_token_change_me":
            warnings.append("WEBHOOK_VERIFY_TOKEN masih memakai default.")
        if self.CORS_ORIGINS == ["*"] and self.is_production:
            warnings.append("CORS_ORIGINS masih wildcard pada environment production.")
        return warnings


settings = Settings()
