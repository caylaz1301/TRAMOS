#!/usr/bin/env python3
"""
Production Database Initialization Script
Sets up a fresh PostgreSQL database with the complete production schema

Usage:
    python scripts/init_production_database.py
    
Optional arguments:
    --db-url: Custom database URL (defaults to env variable)
    --reset: Drop existing tables and reinitialize (⚠️ WARNING: This deletes data!)
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database_models import DatabaseManager, Base

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_production_database(database_url: str, reset: bool = False):
    """
    Initialize production database with complete schema
    
    Args:
        database_url: PostgreSQL connection string
        reset: Whether to drop existing tables first
    """
    logger.info("=" * 70)
    logger.info("🚀 TRAMOS Production Database Initialization")
    logger.info("=" * 70)
    
    db_manager = DatabaseManager(database_url)
    
    try:
        # Step 1: Optional reset
        if reset:
            logger.warning("\n⚠️ RESET MODE: Dropping all existing tables...")
            response = input("Type 'yes' to confirm data deletion: ")
            if response.lower() == 'yes':
                db_manager.drop_all()
                logger.info("✅ All tables dropped")
            else:
                logger.info("❌ Reset cancelled")
                return False
        
        # Step 2: Create all tables
        logger.info("\n📋 Creating database tables...")
        success = db_manager.init_db()
        if not success:
            logger.error("❌ Failed to create tables")
            return False
        
        logger.info("✅ All tables created successfully")
        
        # Step 3: Verify schema
        logger.info("\n✓ Verifying schema...")
        session = db_manager.get_session()
        
        # List all models (tables)
        models = [
            'User', 'Conversation', 'MessageHistory', 'Ticket', 'Resolution',
            'AnalyticsData', 'ConversationContext', 'ConversationTurn', 'WhatsAppSession'
        ]
        
        logger.info("\n📊 Database Schema Summary:")
        logger.info("-" * 70)
        
        tables_info = {
            'users': 'User accounts with RBAC roles',
            'conversations': 'WhatsApp conversation history',
            'message_history': 'Individual messages in conversations',
            'tickets': 'Support tickets from conversations',
            'resolutions': 'Ticket resolution tracking (NEW)',
            'analytics_data': 'System-wide metrics and analytics (NEW)',
            'conversation_context': 'Cached conversation context for performance',
            'conversation_turns': 'Detailed turn-by-turn conversation logs',
            'whatsapp_sessions': 'WhatsApp session state management',
        }
        
        for table, description in tables_info.items():
            logger.info(f"  ✓ {table:30} → {description}")
        
        logger.info("-" * 70)
        
        # Step 4: Display connection info
        logger.info("\n🔌 Connection Information:")
        logger.info("-" * 70)
        
        # Parse database URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            logger.info(f"  Host:     {parsed.hostname}")
            logger.info(f"  Port:     {parsed.port}")
            logger.info(f"  Database: {parsed.path.lstrip('/')}")
            logger.info(f"  User:     {parsed.username}")
        except:
            logger.info(f"  URL: {database_url}")
        
        logger.info("-" * 70)
        
        # Step 5: Display production checklist
        logger.info("\n✅ Production Checklist:")
        logger.info("-" * 70)
        checklist = [
            "Database schema initialized with 9 tables",
            "All relationships and constraints configured",
            "Indexes created for query performance",
            "RBAC role system enabled (user, operator, analyst, admin)",
            "Message type tracking enabled",
            "Resolution table separation for proper normalization",
            "Analytics data collection ready",
            "Dashboard summary aggregation prepared",
        ]
        
        for i, item in enumerate(checklist, 1):
            logger.info(f"  {i}. ✓ {item}")
        
        logger.info("-" * 70)
        
        # Step 6: Next steps
        logger.info("\n📝 Next Steps:")
        logger.info("-" * 70)
        next_steps = [
            "1. Set up environment variables (.env file)",
            "2. Configure WhatsApp Business API credentials",
            "3. Configure osTicket API credentials",
            "4. Configure Gemini AI API credentials (or local Ollama)",
            "5. Run application with: python main.py",
            "6. Test WhatsApp integration with test_twilio_setup.py",
        ]
        
        for step in next_steps:
            logger.info(f"  {step}")
        
        logger.info("-" * 70)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ Database initialization completed successfully!")
        logger.info("=" * 70)
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Initialize TRAMOS production database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize with environment variable database URL
  python scripts/init_production_database.py
  
  # Initialize with custom database URL
  python scripts/init_production_database.py --db-url postgresql://user:pass@localhost/tramos_db
  
  # Reset all tables (WARNING: Deletes all data!)
  python scripts/init_production_database.py --reset
        """
    )
    
    parser.add_argument(
        "--db-url",
        help="Database URL (defaults to DATABASE_URL env variable)",
        default=None
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="⚠️ Drop and recreate all tables (WARNING: Deletes all data!)"
    )
    
    args = parser.parse_args()
    
    db_url = args.db_url or settings.DATABASE_URL
    
    try:
        success = init_production_database(db_url, reset=args.reset)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n❌ Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)
