#!/usr/bin/env python3
"""
Database Initialization Script for TRAMOS
Initializes PostgreSQL database with all necessary tables and schemas
Safe to run multiple times (idempotent)
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database with all tables"""
    try:
        from app.config import settings
        from app.database_models import DatabaseManager
        
        logger.info("=" * 70)
        logger.info("TRAMOS DATABASE INITIALIZATION")
        logger.info("=" * 70)
        
        # Verify database URL is set
        if not settings.DATABASE_URL:
            logger.error("❌ DATABASE_URL not configured in environment")
            logger.error("   Set DATABASE_URL in .env file, e.g.:")
            logger.error("   DATABASE_URL=postgresql://user:pass@localhost:5434/tramos_db")
            return False
        
        logger.info(f"📦 Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'unknown'}")
        
        # Create database manager
        db_manager = DatabaseManager(settings.DATABASE_URL)
        
        # Verify connection
        logger.info("🔗 Verifying database connection...")
        try:
            session = db_manager.get_session()
            session.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Cannot connect to database: {e}")
            logger.error("   Make sure PostgreSQL is running:")
            logger.error("   brew services start postgresql")
            return False
        
        # Initialize tables
        logger.info("📋 Creating tables...")
        if db_manager.init_db():
            logger.info("✅ All tables created successfully")
        else:
            logger.error("❌ Failed to create tables")
            return False
        
        # Summary
        logger.info("=" * 70)
        logger.info("📊 DATABASE INITIALIZATION COMPLETE")
        logger.info("=" * 70)
        logger.info("\nTables created:")
        logger.info("  ✓ users (driver profiles & phone numbers)")
        logger.info("  ✓ conversations (multi-turn chat sessions)")
        logger.info("  ✓ message_history (every message exchanged)")
        logger.info("  ✓ whatsapp_webhooks (incoming webhook logs)")
        logger.info("  ✓ tickets (osTicket integration)")
        logger.info("  ✓ kb_solutions (knowledge base)")
        logger.info("  ✓ solution_attempts (tracking)")
        logger.info("  ✓ analytics_aggregates (metrics & reporting)")
        logger.info("  ✓ admin_users (operator access)")
        logger.info("  ✓ api_keys (external integrations)")
        logger.info("  ✓ audit_log (security & compliance)")
        logger.info("  ✓ settings (system configuration)")
        
        logger.info("\n✨ Database ready for production use!")
        logger.info("\nNext steps:")
        logger.info("  1. Start FastAPI server: python3 main.py")
        logger.info("  2. Setup WhatsApp webhook")
        logger.info("  3. Configure osTicket integration")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("   Make sure you're in the TRAMOS project directory")
        logger.error("   And dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
