#!/usr/bin/env python3
"""
Ingest TRAMOS knowledge base TXT files into PostgreSQL.

Usage:
    python scripts/ingest_knowledge_base.py --source knowledge_base --reindex
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database_models import DatabaseManager
from app.services.knowledge_base import GeminiEmbeddingService, KnowledgeBaseIngestionService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest TRAMOS KB into PostgreSQL")
    parser.add_argument("--source", default=settings.KB_SOURCE_DIR, help="Knowledge base folder")
    parser.add_argument("--reindex", action="store_true", help="Rebuild chunks even if source hash is unchanged")
    args = parser.parse_args()

    db_manager = DatabaseManager(settings.DATABASE_URL)
    db_manager.init_db()
    session = db_manager.get_session()
    try:
        service = KnowledgeBaseIngestionService(session, GeminiEmbeddingService())
        summary = service.ingest_folder(args.source, reindex=args.reindex)
        logger.info("Ingestion summary: %s", summary)
        return 0 if summary.get("status") in {"success", "partial"} else 1
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
