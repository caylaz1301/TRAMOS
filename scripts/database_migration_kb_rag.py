#!/usr/bin/env python3
"""
Idempotent migration for TRAMOS production knowledge base RAG tables.

Creates:
- kb_documents
- kb_chunks
- kb_ingestion_runs
- kb_retrieval_logs

Also tries to enable pgvector and add kb_chunks.embedding_vector with the
configured embedding dimension.
If pgvector is not installed locally and KB_PGVECTOR_REQUIRED=false, the migration
keeps JSON embeddings as the safe fallback path.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.config import settings
from app.database_models import Base, DatabaseManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_migration() -> bool:
    db_manager = DatabaseManager(settings.DATABASE_URL)
    embedding_dimensions = int(settings.EMBEDDING_DIMENSIONS)

    logger.info("Creating ORM-managed KB tables if missing...")
    if not db_manager.init_db():
        return False

    with db_manager.engine.connect() as conn:
        trans = conn.begin()
        try:
            logger.info("Ensuring KB indexes and helper columns...")
            conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_kb_chunks_content_trgm_like
                    ON kb_chunks USING btree (category, audience);

                    CREATE INDEX IF NOT EXISTS idx_kb_retrieval_created_desc
                    ON kb_retrieval_logs (created_at DESC);
                    """
                )
            )
            trans.commit()
        except Exception as exc:
            trans.rollback()
            logger.error("Base KB migration failed: %s", exc)
            return False

    pgvector_enabled = False
    with db_manager.engine.connect() as conn:
        trans = conn.begin()
        try:
            logger.info("Trying to enable pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

            existing_type = conn.execute(
                text(
                    """
                    SELECT format_type(a.atttypid, a.atttypmod)
                    FROM pg_attribute a
                    JOIN pg_class c ON c.oid = a.attrelid
                    WHERE c.relname = 'kb_chunks'
                      AND a.attname = 'embedding_vector'
                      AND NOT a.attisdropped
                    """
                )
            ).scalar()
            expected_type = f"vector({embedding_dimensions})"
            if existing_type and existing_type != expected_type:
                logger.warning(
                    "Rebuilding kb_chunks.embedding_vector from %s to %s",
                    existing_type,
                    expected_type,
                )
                conn.execute(text("DROP INDEX IF EXISTS idx_kb_chunks_embedding_vector"))
                conn.execute(text("ALTER TABLE kb_chunks DROP COLUMN IF EXISTS embedding_vector"))

            conn.execute(
                text(
                    f"""
                    ALTER TABLE kb_chunks
                    ADD COLUMN IF NOT EXISTS embedding_vector vector({embedding_dimensions});
                    """
                )
            )
            trans.commit()
            pgvector_enabled = True
            logger.info("pgvector column is enabled for kb_chunks.embedding_vector")
        except Exception as exc:
            trans.rollback()
            message = str(exc)
            if settings.KB_PGVECTOR_REQUIRED:
                logger.error("pgvector migration failed and KB_PGVECTOR_REQUIRED=true: %s", message)
                return False
            logger.warning("pgvector unavailable; JSON embedding fallback remains active: %s", message[:240])

    if pgvector_enabled:
        with db_manager.engine.connect() as conn:
            trans = conn.begin()
            try:
                if embedding_dimensions <= 2000:
                    conn.execute(
                        text(
                            """
                            CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding_vector
                            ON kb_chunks USING ivfflat (embedding_vector vector_cosine_ops)
                            WITH (lists = 100);
                            """
                        )
                    )
                    logger.info("pgvector ivfflat index is enabled")
                else:
                    # pgvector ivfflat index untuk tipe vector dibatasi 2000 dimensi.
                    # Untuk qwen3-embedding:4b (2560 dimensi), exact vector scan tetap jalan.
                    conn.execute(text("DROP INDEX IF EXISTS idx_kb_chunks_embedding_vector"))
                    logger.warning(
                        "Skipping ivfflat index because embedding dimension %s exceeds pgvector index limit 2000",
                        embedding_dimensions,
                    )
                trans.commit()
            except Exception as exc:
                trans.rollback()
                if settings.KB_PGVECTOR_REQUIRED:
                    logger.error("pgvector index migration failed and KB_PGVECTOR_REQUIRED=true: %s", exc)
                    return False
                logger.warning("pgvector index unavailable; exact vector scan/fallback remains active: %s", str(exc)[:240])

    logger.info("KB RAG migration complete. pgvector_enabled=%s", pgvector_enabled)
    return True


if __name__ == "__main__":
    ok = run_migration()
    sys.exit(0 if ok else 1)
