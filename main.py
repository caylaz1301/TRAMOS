"""Entry point FastAPI untuk TRAMOS AI Support System."""

import logging
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.routes import tickets, whatsapp, analytics, auth, kb
from app.database_models import DatabaseManager
from app.services.chatbot.session_manager import init_session_manager
from app.services.database_tracker import init_db_tracker

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable noisy debug logs from external libraries
for noisy_logger in ["python_multipart", "urllib3", "asyncio", "httpx", "httpcore"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# ============================================================================
# GLOBAL STATE
# ============================================================================

db_manager: Optional[DatabaseManager] = None


# ============================================================================
# APPLICATION LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - handles startup and shutdown"""
    global db_manager
    
    # === STARTUP ===
    logger.info("=" * 50)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 50)
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Webhook: {settings.WEBHOOK_PATH}")
    for warning in settings.production_warnings():
        logger.warning("Production config warning: %s", warning)
    
    # Initialize database
    try:
        db_manager = DatabaseManager(settings.DATABASE_URL)
        db_manager.init_db()
        
        # Initialize session manager with database
        init_session_manager(db_manager.SessionLocal)
        
        # Initialize database tracker for all table writes
        init_db_tracker()
        
        logger.info("✅ Database initialized")
        logger.info("✅ Session Manager initialized with database persistence")
    except Exception as e:
        logger.warning(f"⚠️ Database init failed: {e}")
        logger.warning("Running without database persistence")
    
    # Log service status
    logger.info(f"osTicket: {'✅ Configured' if settings.OSTICKET_API_KEY else '❌ Not configured'}")
    logger.info(f"WhatsApp: {'✅ Configured' if settings.WHATSAPP_API_TOKEN else '❌ Not configured'}")
    logger.info(f"Gemini AI: ✅ {getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')} (Cloud API)")
    logger.info("=" * 50)
    
    yield
    
    # === SHUTDOWN ===
    logger.info(f"🛑 Shutting down {settings.APP_NAME}")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered WhatsApp support system for TRAMOS fleet management",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(tickets.router)
app.include_router(whatsapp.router)
app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(kb.router)


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db_session():
    """Get database session for dependency injection"""
    if db_manager:
        return db_manager.get_session()
    return None


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/", tags=["system"])
async def root():
    """Informasi singkat API untuk sanity check manual."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "health": "/health",
            "config": "/config/status"
        }
    }


@app.get("/health", tags=["system"])
async def health_check():
    """Health check lengkap untuk monitoring dashboard dan readiness demo."""
    from app.utils.ai_logic import ai_engine
    
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Database dianggap sehat jika query sederhana berhasil dieksekusi.
    db_status = "connected"
    try:
        if not db_manager:
            db_status = "not_configured"
        else:
            session = db_manager.get_session()
            try:
                session.execute(text("SELECT 1"))
            finally:
                session.close()
    except Exception as e:
        db_status = f"error: {str(e)[:30]}"
    health_status["components"]["database"] = db_status
    
    # Gemini tidak dipanggil live agar endpoint health tetap ringan.
    ai_status = "unknown"
    try:
        if ai_engine:
            ai_status = "operational" if getattr(ai_engine, 'gemini_available', False) else "not_configured"
    except Exception:
        ai_status = "not_configured"
    health_status["components"]["ai_engine"] = ai_status
    
    whatsapp_status = "configured" if settings.WHATSAPP_API_TOKEN else "not_configured"
    health_status["components"]["whatsapp_api"] = whatsapp_status
    
    osticket_status = "configured" if settings.OSTICKET_API_KEY else "not_configured"
    health_status["components"]["osticket"] = osticket_status
    
    # RAG dicek dari metadata database; fallback KB tetap dilaporkan jika RAG belum siap.
    kb_status = "loaded"
    try:
        from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING
        kb_status = f"fallback loaded ({len(KB_TROUBLESHOOTING)} solutions)"
        if settings.KB_RAG_ENABLED and db_manager:
            from app.services.knowledge_base import KnowledgeBaseRetrievalService

            session = db_manager.get_session()
            try:
                rag_health = KnowledgeBaseRetrievalService(session).health()
                kb_status = (
                    f"rag enabled ({rag_health['documents']} docs, "
                    f"{rag_health['chunks']} chunks, pgvector={rag_health['pgvector_enabled']})"
                )
            finally:
                session.close()
    except Exception as exc:
        logger.warning("Knowledge base health check failed: %s", str(exc)[:160])
        kb_status = "error"
    health_status["components"]["knowledge_base"] = kb_status
    
    # Overall status
    if "error" in str(health_status.get("components", {})) or ai_status == "unreachable":
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/config/status", tags=["system"])
async def config_status():
    """Status konfigurasi aman untuk dashboard; tidak mengembalikan secret."""
    return {
        "debug": settings.DEBUG,
        "environment": settings.ENVIRONMENT,
        "services": {
            "osticket": bool(settings.OSTICKET_API_KEY),
            "whatsapp": bool(settings.WHATSAPP_API_TOKEN),
            "database": bool(db_manager),
            "ai_engine": settings.GEMINI_MODEL,
            "knowledge_base_rag": settings.KB_RAG_ENABLED,
        },
        "webhook_path": settings.WEBHOOK_PATH,
        "production_warnings": settings.production_warnings(),
    }


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )
