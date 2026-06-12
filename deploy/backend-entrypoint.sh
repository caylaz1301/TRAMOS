#!/usr/bin/env sh
set -eu

echo "[TRAMOS] Starting backend entrypoint"

if [ "${RUN_PRODUCTION_TABLES_MIGRATION:-true}" = "true" ]; then
  echo "[TRAMOS] Ensuring production support tables"
  python scripts/ensure_production_tables.py
fi

if [ "${RUN_KB_MIGRATION:-true}" = "true" ]; then
  echo "[TRAMOS] Ensuring KB/RAG schema"
  python scripts/database_migration_kb_rag.py
fi

if [ "${AUTO_INGEST_KB:-false}" = "true" ]; then
  echo "[TRAMOS] Ingesting knowledge base"
  python scripts/ingest_knowledge_base.py --source "${KB_SOURCE_DIR:-knowledge_base}" --reindex
fi

exec "$@"
