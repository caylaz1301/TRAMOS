"""
TRAMOS AI Support System
Main FastAPI application entry point

AI-powered WhatsApp support system for fleet management
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import tickets, whatsapp
from app.database_models import DatabaseManager
from app.services import init_conversation_manager

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
    
    # Initialize database
    try:
        db_manager = DatabaseManager(settings.DATABASE_URL)
        db_manager.init_db()
        
        # Initialize conversation manager with database session
        session = db_manager.get_session()
        init_conversation_manager(session)
        
        logger.info("✅ Database & ConversationManager initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database init failed: {e}")
        logger.warning("Running without database persistence")
    
    # Log service status
    logger.info(f"osTicket: {'✅ Configured' if settings.OSTICKET_API_KEY else '❌ Not configured'}")
    logger.info(f"WhatsApp: {'✅ Configured' if settings.WHATSAPP_API_TOKEN else '❌ Not configured'}")
    logger.info(f"Gemini AI: {'✅ Configured' if settings.GEMINI_API_KEY else '❌ Not configured'}")
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
    """Root endpoint - API information"""
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
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected" if db_manager else "not configured"
    }


@app.get("/config/status", tags=["system"])
async def config_status():
    """Check configuration status of all services"""
    return {
        "debug": settings.DEBUG,
        "services": {
            "osticket": bool(settings.OSTICKET_API_KEY),
            "whatsapp": bool(settings.WHATSAPP_API_TOKEN),
            "database": bool(db_manager),
            "gemini_ai": bool(settings.GEMINI_API_KEY),
        },
        "webhook_path": settings.WEBHOOK_PATH,
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
