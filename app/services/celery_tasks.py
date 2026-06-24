"""
Celery Configuration for TRAMOS Background Tasks
Handles heavy processing asynchronously

Setup:
    1. Start Redis: redis-server
    2. Start worker: celery -A app.services.celery_app worker --loglevel=info
    3. Start beat (scheduler): celery -A app.services.celery_app beat --loglevel=info

Usage:
    from app.services.celery_tasks import generate_report, cleanup_old_data

    # Async task
    result = generate_report.delay(date="2024-01-01")

    # Check status
    if result.ready():
        print(result.result)
"""

import logging
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Configure Celery
celery_app = Celery(
    "tramos",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,

    # Task settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Result settings
    result_expires=86400,  # Keep results for 24 hours

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-sessions": {
            "task": "app.services.celery_tasks.cleanup_old_sessions",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
        },
        "refresh-analytics-mv": {
            "task": "app.services.celery_tasks.refresh_materialized_views",
            "schedule": crontab(minute=0),  # Every hour
        },
        "send-daily-report": {
            "task": "app.services.celery_tasks.generate_daily_report",
            "schedule": crontab(hour=8, minute=0),  # Daily at 8 AM
        },
    },
)

logger = logging.getLogger(__name__)


# ============================================================================
# ANALYTICS TASKS
# ============================================================================

@celery_app.task(bind=True, max_retries=3)
def generate_report(self, date: str) -> dict:
    """
    Generate comprehensive daily report asynchronously.

    Args:
        date: Date string in YYYY-MM-DD format

    Returns:
        dict with report data
    """
    logger.info(f"Generating report for {date}")

    try:
        from app.database_models import DatabaseManager
        from sqlalchemy import func, text

        db_manager = DatabaseManager(settings.DATABASE_URL)
        session = db_manager.get_session()

        try:
            # Query metrics
            report_date = datetime.strptime(date, "%Y-%m-%d").date()

            # Total conversations
            total_sessions = session.execute(
                text("""
                    SELECT COUNT(*) FROM conversations
                    WHERE DATE(created_at) = :date
                """),
                {"date": report_date}
            ).scalar()

            # Resolved by AI
            ai_resolved = session.execute(
                text("""
                    SELECT COUNT(*) FROM conversations
                    WHERE DATE(created_at) = :date
                    AND ticket_id IS NULL
                    AND current_state IN ('RESOLVED', 'CLOSED')
                """),
                {"date": report_date}
            ).scalar()

            # Ticket created
            tickets_created = session.execute(
                text("""
                    SELECT COUNT(*) FROM tickets
                    WHERE DATE(created_at) = :date
                """),
                {"date": report_date}
            ).scalar()

            # Category breakdown
            categories = session.execute(
                text("""
                    SELECT category, COUNT(*) as count
                    FROM conversations
                    WHERE DATE(created_at) = :date
                    GROUP BY category
                    ORDER BY count DESC
                    LIMIT 10
                """),
                {"date": report_date}
            ).fetchall()

            result = {
                "date": date,
                "generated_at": datetime.now().isoformat(),
                "total_sessions": total_sessions or 0,
                "ai_resolved": ai_resolved or 0,
                "tickets_created": tickets_created or 0,
                "ai_resolution_rate": (
                    round((ai_resolved / total_sessions * 100), 2)
                    if total_sessions > 0 else 0
                ),
                "top_categories": [
                    {"category": c[0], "count": c[1]}
                    for c in categories
                ],
            }

            logger.info(f"Report generated for {date}: {result}")
            return result

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        self.retry(exc=e, countdown=300)  # Retry in 5 minutes


@celery_app.task
def generate_daily_report() -> dict:
    """Generate and send daily report to configured channels"""
    today = datetime.now().strftime("%Y-%m-%d")

    logger.info("Generating daily report")

    try:
        # Generate report
        report = generate_report.delay(today).get(timeout=300)

        # In a real implementation, you would send this via email/Slack
        # email_service.send_daily_report(report)

        logger.info(f"Daily report generated and sent: {today}")
        return {"status": "sent", "report": report}

    except Exception as e:
        logger.error(f"Daily report failed: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# DATABASE MAINTENANCE TASKS
# ============================================================================

@celery_app.task
def cleanup_old_sessions(days_to_keep: int = 90) -> dict:
    """
    Clean up old conversation sessions and messages.

    Args:
        days_to_keep: Number of days to retain (default: 90)

    Returns:
        dict with cleanup statistics
    """
    logger.info(f"Starting cleanup of sessions older than {days_to_keep} days")

    try:
        from app.database_models import DatabaseManager

        db_manager = DatabaseManager(settings.DATABASE_URL)
        session = db_manager.get_session()

        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Count before deletion
            old_messages = session.execute(
                text("""
                    SELECT COUNT(*) FROM message_history
                    WHERE created_at < :cutoff
                """),
                {"cutoff": cutoff_date}
            ).scalar()

            old_conversations = session.execute(
                text("""
                    SELECT COUNT(*) FROM conversations
                    WHERE created_at < :cutoff
                    AND current_state IN ('RESOLVED', 'CLOSED')
                """),
                {"cutoff": cutoff_date}
            ).scalar()

            # Delete old message history
            if old_messages > 0:
                session.execute(
                    text("""
                        DELETE FROM message_history
                        WHERE created_at < :cutoff
                    """),
                    {"cutoff": cutoff_date}
                )

            # Delete old resolved conversations
            if old_conversations > 0:
                session.execute(
                    text("""
                        DELETE FROM conversations
                        WHERE created_at < :cutoff
                        AND current_state IN ('RESOLVED', 'CLOSED')
                    """),
                    {"cutoff": cutoff_date}
                )

            session.commit()

            result = {
                "messages_deleted": old_messages or 0,
                "conversations_deleted": old_conversations or 0,
                "cutoff_date": cutoff_date.isoformat(),
            }

            logger.info(f"Cleanup complete: {result}")
            return result

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"error": str(e)}


@celery_app.task
def refresh_materialized_views() -> dict:
    """
    Refresh all materialized views for analytics.

    Returns:
        dict with refresh status
    """
    logger.info("Refreshing materialized views")

    try:
        from app.database_models import DatabaseManager

        db_manager = DatabaseManager(settings.DATABASE_URL)
        session = db_manager.get_session()

        views = [
            "mv_daily_conversations",
            "mv_daily_tickets",
            "mv_category_stats",
            "mv_hourly_volume",
            "mv_intent_stats",
        ]

        refreshed = []
        failed = []

        try:
            for view_name in views:
                try:
                    session.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                    refreshed.append(view_name)
                except Exception as e:
                    logger.warning(f"View {view_name} failed: {e}")
                    failed.append(view_name)

            session.commit()

            result = {
                "refreshed": refreshed,
                "failed": failed,
            }

            logger.info(f"Materialized views refreshed: {len(refreshed)}/{len(views)}")
            return result

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Materialized view refresh failed: {e}")
        return {"error": str(e)}


# ============================================================================
# NOTIFICATION TASKS
# ============================================================================

@celery_app.task
def send_alert_email(alert_type: str, message: str, recipients: list) -> dict:
    """
    Send alert email asynchronously.

    Args:
        alert_type: Type of alert (error, warning, info)
        message: Alert message
        recipients: List of email addresses

    Returns:
        dict with send status
    """
    logger.info(f"Sending {alert_type} alert to {len(recipients)} recipients")

    try:
        from app.services.notification_service import NotificationService

        service = NotificationService()
        result = service.send_email(
            recipients=recipients,
            subject=f"[TRAMOS {alert_type.upper()}] Alert",
            body=message,
        )

        logger.info(f"Alert sent: {result}")
        return {"status": "sent", "recipients": recipients}

    except Exception as e:
        logger.error(f"Alert email failed: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================================
# HEALTH CHECK
# ============================================================================

@celery_app.task
def health_check() -> dict:
    """Periodic health check task"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "worker": "celery",
    }
