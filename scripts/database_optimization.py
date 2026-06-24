"""
Database Optimization Script for TRAMOS
Adds indexes, materialized views, and performance optimizations

Usage:
    python -m scripts.database_optimization

This script is safe to run multiple times - uses CREATE INDEX IF NOT EXISTS
"""

import logging
from sqlalchemy import text
from app.database_models import DatabaseManager
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_analytics_indexes(session):
    """Create indexes for analytics queries"""
    indexes = [
        # Conversations - commonly queried patterns
        ("idx_conv_state_created", "conversations", "current_state, created_at"),
        ("idx_conv_category_created", "conversations", "category, created_at"),
        ("idx_conv_user_created", "conversations", "user_id, created_at"),

        # Tickets - status and date queries
        ("idx_ticket_status_created", "tickets", "status, created_at"),
        ("idx_ticket_category_status", "tickets", "category, status"),

        # Messages - analytics aggregations
        ("idx_msg_conversation_timestamp", "message_history", "conversation_id, created_at"),
        ("idx_msg_intent_category", "message_history", "intent, category"),

        # Users - active users queries
        ("idx_users_last_contact", "users", "last_contact_at"),
        ("idx_users_total_messages", "users", "total_messages DESC"),

        # Metrics - time-series queries
        ("idx_metrics_date_type", "metrics", "date, metric_type"),
    ]

    for idx_name, table, columns in indexes:
        try:
            sql = f"""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON {table} ({columns})
            """
            session.execute(text(sql))
            logger.info(f"Created index: {idx_name}")
        except Exception as e:
            logger.warning(f"Index {idx_name} failed: {e}")


def create_materialized_views(session):
    """Create materialized views for fast analytics"""
    views = [
        # Daily conversation stats
        ("mv_daily_conversations", """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_conversations AS
            SELECT
                DATE(created_at) as date,
                current_state as state,
                COUNT(*) as conversation_count,
                COUNT(DISTINCT phone_number) as unique_users,
                AVG(EXTRACT(EPOCH FROM (COALESCE(last_message_at, NOW()) - created_at))) as avg_duration_seconds
            FROM conversations
            GROUP BY DATE(created_at), current_state
        """),

        # Daily ticket stats
        ("mv_daily_tickets", """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_tickets AS
            SELECT
                DATE(created_at) as date,
                status,
                category,
                COUNT(*) as ticket_count,
                AVG(EXTRACT(EPOCH FROM (COALESCE(updated_at, NOW()) - created_at))) as avg_resolution_seconds
            FROM tickets
            GROUP BY DATE(created_at), status, category
        """),

        # Category distribution
        ("mv_category_stats", """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_category_stats AS
            SELECT
                category,
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE current_state = 'RESOLVED') as resolved_count,
                COUNT(*) FILTER (WHERE ticket_id IS NOT NULL) as escalated_count,
                ROUND(
                    COUNT(*) FILTER (WHERE ticket_id IS NULL AND current_state = 'RESOLVED')::NUMERIC /
                    NULLIF(COUNT(*), 0) * 100,
                    2
                ) as ai_resolution_rate
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY category
        """),

        # Hourly volume for staffing
        ("mv_hourly_volume", """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_volume AS
            SELECT
                EXTRACT(DOW FROM created_at) as day_of_week,
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as conversation_count,
                COUNT(*) FILTER (WHERE ticket_id IS NOT NULL) as escalated
            FROM conversations
            WHERE created_at >= NOW() - INTERVAL '90 days'
            GROUP BY
                EXTRACT(DOW FROM created_at),
                EXTRACT(HOUR FROM created_at)
        """),

        # Intent distribution
        ("mv_intent_stats", """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_intent_stats AS
            SELECT
                intent,
                category,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM message_history
            WHERE created_at >= NOW() - INTERVAL '30 days'
                AND intent IS NOT NULL
            GROUP BY intent, category
        """),
    ]

    for view_name, view_sql in views:
        try:
            # Check if view exists
            result = session.execute(text("""
                SELECT 1 FROM pg_matviews WHERE matviewname = :name
            """), {"name": view_name}).fetchone()

            if result:
                logger.info(f"Materialized view {view_name} already exists, skipping")
            else:
                session.execute(text(view_sql))
                logger.info(f"Created materialized view: {view_name}")
        except Exception as e:
            logger.warning(f"Materialized view {view_name} failed: {e}")


def create_unique_indexes(session):
    """Create partial/index-only scans for common patterns"""
    partial_indexes = [
        # Active conversations only
        ("idx_conv_active", "conversations",
         "current_state, created_at",
         "WHERE current_state NOT IN ('RESOLVED', 'CLOSED')"),

        # Recent messages
        ("idx_msg_recent", "message_history",
         "conversation_id, created_at DESC",
         "WHERE created_at >= NOW() - INTERVAL '7 days'"),

        # Open tickets
        ("idx_ticket_open", "tickets",
         "priority, created_at",
         "WHERE status IN ('OPEN', 'IN_PROGRESS', 'PENDING')"),
    ]

    for idx_name, table, columns, where_clause in partial_indexes:
        try:
            sql = f"""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON {table} ({columns})
                {where_clause}
            """
            session.execute(text(sql))
            logger.info(f"Created partial index: {idx_name}")
        except Exception as e:
            logger.warning(f"Partial index {idx_name} failed: {e}")


def create_audit_table(session):
    """Create audit trail table for compliance"""
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                action VARCHAR(100) NOT NULL,
                table_name VARCHAR(50),
                record_id INTEGER,
                old_value JSONB,
                new_value JSONB,
                ip_address INET,
                user_agent TEXT,
                request_id VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))

        # Create index on audit log
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_user_time
            ON audit_log (user_id, created_at DESC)
        """))

        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_audit_table_time
            ON audit_log (table_name, created_at DESC)
        """))

        logger.info("Created audit_log table and indexes")
    except Exception as e:
        logger.warning(f"Audit table creation failed: {e}")


def refresh_materialized_views(session):
    """Refresh all materialized views"""
    views = [
        "mv_daily_conversations",
        "mv_daily_tickets",
        "mv_category_stats",
        "mv_hourly_volume",
        "mv_intent_stats",
    ]

    for view_name in views:
        try:
            session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
            logger.info(f"Refreshed: {view_name}")
        except Exception as e:
            logger.warning(f"Refresh {view_name} failed: {e}")


def analyze_tables(session):
    """Run ANALYZE to update statistics"""
    try:
        session.execute(text("ANALYZE"))
        logger.info("Database statistics updated")
    except Exception as e:
        logger.warning(f"Analyze failed: {e}")


def optimize_connection_settings(session):
    """Apply connection pool optimizations (requires superuser)"""
    optimizations = [
        # Increase work_mem for complex aggregations
        ("SET work_mem = '64MB'", "Work memory"),

        # Effective cache size
        ("SET effective_cache_size = '256MB'", "Effective cache"),

        # Random page cost for SSD
        ("SET random_page_cost = 1.1", "Random page cost (SSD)"),

        # Enable parallel queries
        ("SET max_parallel_workers_per_gather = 4", "Parallel workers"),
    ]

    for sql, description in optimizations:
        try:
            session.execute(text(sql))
            logger.info(f"Applied optimization: {description}")
        except Exception as e:
            logger.debug(f"Optimization {description}: {e}")  # Don't warn - these require superuser


def main():
    """Run all database optimizations"""
    logger.info("=" * 60)
    logger.info("Starting TRAMOS Database Optimization")
    logger.info("=" * 60)

    try:
        db_manager = DatabaseManager(settings.DATABASE_URL)

        with db_manager.get_session() as session:
            # Run optimizations
            logger.info("\n--- Creating Analytics Indexes ---")
            create_analytics_indexes(session)

            logger.info("\n--- Creating Materialized Views ---")
            create_materialized_views(session)

            logger.info("\n--- Creating Partial Indexes ---")
            create_unique_indexes(session)

            logger.info("\n--- Creating Audit Table ---")
            create_audit_table(session)

            logger.info("\n--- Analyzing Tables ---")
            analyze_tables(session)

            # Commit all changes
            session.commit()

        logger.info("\n" + "=" * 60)
        logger.info("Database Optimization Complete")
        logger.info("=" * 60)
        logger.info("\nNote: Run 'REFRESH MATERIALIZED VIEW <name>' to update data")
        logger.info("Or schedule: SELECT cron.schedule('refresh-mv', '0 * * * *', $$REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_conversations$$);")

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        raise


if __name__ == "__main__":
    main()
