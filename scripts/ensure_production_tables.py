#!/usr/bin/env python3
"""Pastikan tabel pendukung production tersedia.

Sebagian tabel dashboard dibuat lewat SQL manual, bukan model SQLAlchemy ORM.
Script ini idempotent dan aman dijalankan saat startup container/VPS.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database_models import DatabaseManager  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def ensure_tables() -> bool:
    manager = DatabaseManager(settings.DATABASE_URL)
    if not manager.init_db():
        return False

    with manager.engine.begin() as conn:
        conn.execute(
            text(
                """
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

                CREATE INDEX IF NOT EXISTS idx_dashboard_date
                ON dashboard_analytics_summary(summary_date);

                ALTER TABLE whatsapp_sessions
                ADD COLUMN IF NOT EXISTS context_data JSONB DEFAULT '{}'::jsonb;
                """
            )
        )

    logger.info("Production support tables are ready")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if ensure_tables() else 1)
