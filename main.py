"""Main FastAPI application entry point"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import webhook, tickets

# Reload trigger v1 - reload to pick up new .env config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered WhatsApp support system for TRAMOS fleet management",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(webhook.router)
app.include_router(tickets.router)


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"osTicket API URL: {settings.OSTICKET_API_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info(f"Shutting down {settings.APP_NAME}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/api/docs",
        "openapi": "/api/openapi.json"
    }


@app.get("/health")
async def health_check():
    """Application health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/config/status")
async def config_status():
    """Check configuration status"""
    return {
        "debug": settings.DEBUG,
        "osticket_configured": bool(settings.OSTICKET_API_KEY and settings.OSTICKET_API_URL),
        "whatsapp_configured": bool(settings.WHATSAPP_API_TOKEN),
        "webhook_verify_token_set": bool(settings.WEBHOOK_VERIFY_TOKEN),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
