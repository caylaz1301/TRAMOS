"""
TRAMOS AI Support System
Main FastAPI application entry point

AI-powered WhatsApp support system for fleet management
"""

import logging
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import tickets, whatsapp, analytics, auth
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
    logger.info(f"Ollama AI: ✅ Local (localhost:11434)")
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
    """Enhanced health check endpoint for monitoring - checks all system components"""
    import httpx
    from app.utils.ai_logic import ai_engine
    
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database
    db_status = "connected"
    try:
        if not db_manager:
            db_status = "not_configured"
        else:
            # Try to get a session to verify connectivity
            session = db_manager.get_session()
            session.close()
    except Exception as e:
        db_status = f"error: {str(e)[:30]}"
    health_status["components"]["database"] = db_status
    
    # Check AI engine (Ollama)
    ai_status = "unknown"
    try:
        if ai_engine:
            # Check if ollama is reachable
            try:
                result = ai_engine.analyze_user_input("test")
                ai_status = "operational" if result else "degraded"
            except:
                ai_status = "unreachable"
    except:
        ai_status = "not_configured"
    health_status["components"]["ai_engine"] = ai_status
    
    # Check WhatsApp API configuration
    whatsapp_status = "configured" if settings.WHATSAPP_API_TOKEN else "not_configured"
    health_status["components"]["whatsapp_api"] = whatsapp_status
    
    # Check osTicket configuration
    osticket_status = "configured" if settings.OSTICKET_API_KEY else "not_configured"
    health_status["components"]["osticket"] = osticket_status
    
    # Check KB system
    kb_status = "loaded"
    try:
        from app.utils.kb_troubleshooting import KB_TROUBLESHOOTING
        kb_status = f"loaded ({len(KB_TROUBLESHOOTING)} solutions)"
    except:
        kb_status = "error"
    health_status["components"]["knowledge_base"] = kb_status
    
    # Overall status
    if "error" in str(health_status.get("components", {})) or ai_status == "unreachable":
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/config/status", tags=["system"])
async def config_status():
    """Check configuration status of all services"""
    return {
        "debug": settings.DEBUG,
        "services": {
            "osticket": bool(settings.OSTICKET_API_KEY),
            "whatsapp": bool(settings.WHATSAPP_API_TOKEN),
            "database": bool(db_manager),
            "ai_engine": "ollama_local",
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
