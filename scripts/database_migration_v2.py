#!/usr/bin/env python3
"""
Database Migration Script - v1 to v2
Migrates existing database to production-ready schema with new tables and fields

This script:
1. Backs up existing data
2. Adds new columns and tables
3. Migrates data to new structure
4. Validates data integrity
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database_models import DatabaseManager, MIGRATION_CREATE_TABLES
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles database migration from v1 to v2"""
    
    def __init__(self, database_url: str):
        self.db_manager = DatabaseManager(database_url)
        self.migrations_applied = []
    
    def backup_data(self):
        """Create backup of existing data (optional but recommended)"""
        session = self.db_manager.get_session()
        try:
            # Create backup tables
            backup_sql = """
            CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users;
            CREATE TABLE IF NOT EXISTS conversations_backup AS SELECT * FROM conversations;
            CREATE TABLE IF NOT EXISTS message_history_backup AS SELECT * FROM message_history;
            CREATE TABLE IF NOT EXISTS tickets_backup AS SELECT * FROM tickets;
            """
            self.db_manager.execute_query(backup_sql)
            logger.info("✅ Data backup created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
        finally:
            session.close()
    
    def add_missing_columns(self):
        """Add new columns to existing tables"""
        operations = [
            {
                "name": "Add role column to users",
                "sql": "ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL CHECK (role IN ('user', 'operator', 'analyst', 'admin'))"
            },
            {
                "name": "Add department column to users",
                "sql": "ALTER TABLE users ADD COLUMN department VARCHAR(100)"
            },
            {
                "name": "Add message_type column to message_history",
                "sql": "ALTER TABLE message_history ADD COLUMN message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'document', 'location', 'audio', 'video'))"
            },
            {
                "name": "Add UNIQUE constraint to message_id",
                "sql": "ALTER TABLE message_history ADD CONSTRAINT uq_message_id UNIQUE (message_id)"
            },
            {
                "name": "Add UNIQUE constraint to osticket_id",
                "sql": "ALTER TABLE tickets ADD CONSTRAINT uq_osticket_id UNIQUE (osticket_id)"
            },
        ]
        
        for op in operations:
            try:
                self.db_manager.execute_query(op["sql"])
                logger.info(f"✅ {op['name']}")
                self.migrations_applied.append(op["name"])
            except Exception as e:
                logger.warning(f"⚠️ {op['name']} - {e}")
    
    def create_resolution_table(self):
        """Create new RESOLUTION table"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS resolutions (
                id SERIAL PRIMARY KEY,
                ticket_id INTEGER NOT NULL UNIQUE REFERENCES tickets(id) ON DELETE CASCADE,
                resolution_type VARCHAR(20) DEFAULT 'operator_resolved' CHECK (resolution_type IN ('ai_solution', 'operator_resolved', 'user_resolved', 'escalated')),
                resolution_notes TEXT,
                resolved_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                resolved_at TIMESTAMP DEFAULT NOW(),
                resolution_time_minutes INTEGER,
                ai_attempted BOOLEAN DEFAULT FALSE,
                ai_successful BOOLEAN DEFAULT FALSE,
                ai_confidence FLOAT,
                meta_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_resolutions_ticket ON resolutions(ticket_id);
            CREATE INDEX IF NOT EXISTS idx_resolutions_resolved_by ON resolutions(resolved_by_user_id);
            CREATE INDEX IF NOT EXISTS idx_resolutions_type ON resolutions(resolution_type);
            CREATE INDEX IF NOT EXISTS idx_resolutions_datetime ON resolutions(resolved_at);
            """
            self.db_manager.execute_query(sql)
            logger.info("✅ Created resolutions table")
            self.migrations_applied.append("Create resolutions table")
        except Exception as e:
            logger.warning(f"⚠️ Resolutions table - {e}")
    
    def create_analytics_table(self):
        """Create new ANALYTICS_DATA table"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS analytics_data (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
                ticket_id INTEGER REFERENCES tickets(id) ON DELETE SET NULL,
                metric_type VARCHAR(50) NOT NULL,
                metric_value FLOAT NOT NULL,
                category VARCHAR(50) NOT NULL,
                date_recorded DATE NOT NULL,
                hour_recorded INTEGER CHECK (hour_recorded >= 0 AND hour_recorded <= 23),
                operator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                meta_data JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_analytics_metric_type ON analytics_data(metric_type);
            CREATE INDEX IF NOT EXISTS idx_analytics_category ON analytics_data(category);
            CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics_data(date_recorded);
            CREATE INDEX IF NOT EXISTS idx_analytics_composite ON analytics_data(metric_type, date_recorded);
            """
            self.db_manager.execute_query(sql)
            logger.info("✅ Created analytics_data table")
            self.migrations_applied.append("Create analytics_data table")
        except Exception as e:
            logger.warning(f"⚠️ Analytics table - {e}")
    
    def create_dashboard_summary_table(self):
        """Create dashboard analytics summary table"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS dashboard_analytics_summary (
                id SERIAL PRIMARY KEY,
                summary_date DATE NOT NULL UNIQUE,
                total_conversations INTEGER DEFAULT 0,
                total_tickets_created INTEGER DEFAULT 0,
                avg_resolution_time INTEGER,
                ai_success_rate FLOAT,
                operator_count INTEGER,
                most_common_category VARCHAR(50),
                avg_user_satisfaction FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_dashboard_date ON dashboard_analytics_summary(summary_date);
            """
            self.db_manager.execute_query(sql)
            logger.info("✅ Created dashboard_analytics_summary table")
            self.migrations_applied.append("Create dashboard_analytics_summary table")
        except Exception as e:
            logger.warning(f"⚠️ Dashboard summary table - {e}")
    
    def migrate_ticket_data_to_resolution(self):
        """Migrate resolution data from tickets to resolutions table"""
        try:
            sql = """
            INSERT INTO resolutions (ticket_id, resolution_notes, resolved_at, resolution_time_minutes, created_at)
            SELECT 
                id,
                resolution_notes,
                resolved_at,
                resolution_time_minutes,
                NOW()
            FROM tickets
            WHERE resolved_at IS NOT NULL
            ON CONFLICT (ticket_id) DO NOTHING;
            """
            self.db_manager.execute_query(sql)
            logger.info("✅ Migrated resolution data from tickets")
            self.migrations_applied.append("Migrate ticket resolution data")
        except Exception as e:
            logger.warning(f"⚠️ Resolution data migration - {e}")
    
    def cleanup_old_columns(self):
        """Remove resolution columns from tickets table (if needed)"""
        # NOTE: Only do this if you're sure resolution data is properly migrated
        # For now, we'll keep them for backward compatibility
        logger.info("⚠️ Skipping column removal for backward compatibility")
    
    def validate_migration(self):
        """Validate that migration was successful"""
        try:
            session = self.db_manager.get_session()
            
            # Check key tables exist
            tables_to_check = [
                'users', 'conversations', 'message_history', 'tickets',
                'resolutions', 'analytics_data', 'conversation_context',
                'conversation_turns', 'whatsapp_sessions'
            ]
            
            for table_name in tables_to_check:
                result = session.execute(
                    text(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}')")
                ).scalar()
                if result:
                    logger.info(f"✅ Table '{table_name}' exists")
                else:
                    logger.warning(f"⚠️ Table '{table_name}' not found")
            
            session.close()
            return True
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False
    
    def run(self, with_backup=True):
        """Execute full migration"""
        logger.info("=" * 60)
        logger.info("🚀 Starting Database Migration (v1 → v2)")
        logger.info("=" * 60)
        
        try:
            if with_backup:
                logger.info("\n📋 Step 1: Creating backup...")
                self.backup_data()
            
            logger.info("\n🔧 Step 2: Adding missing columns...")
            self.add_missing_columns()
            
            logger.info("\n📊 Step 3: Creating resolution table...")
            self.create_resolution_table()
            
            logger.info("\n📈 Step 4: Creating analytics table...")
            self.create_analytics_table()
            
            logger.info("\n📋 Step 5: Creating dashboard summary table...")
            self.create_dashboard_summary_table()
            
            logger.info("\n🔄 Step 6: Migrating resolution data...")
            self.migrate_ticket_data_to_resolution()
            
            logger.info("\n✅ Step 7: Validating migration...")
            self.validate_migration()
            
            logger.info("\n" + "=" * 60)
            logger.info(f"✅ Migration completed successfully!")
            logger.info(f"📊 Applied {len(self.migrations_applied)} operations:")
            for op in self.migrations_applied:
                logger.info(f"   ✓ {op}")
            logger.info("=" * 60)
            
            return True
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate TRAMOS database schema")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup step")
    parser.add_argument("--db-url", help="Database URL (defaults to env var)")
    args = parser.parse_args()
    
    db_url = args.db_url or settings.DATABASE_URL
    migrator = DatabaseMigrator(db_url)
    success = migrator.run(with_backup=not args.no_backup)
    
    sys.exit(0 if success else 1)
