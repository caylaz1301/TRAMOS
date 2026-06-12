#!/usr/bin/env python3
"""
Manual terminal test for TRAMOS KB retrieval.

Usage:
    python scripts/test_kb_retrieval.py "gps tidak update di jalan" --audience driver
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database_models import DatabaseManager
from app.services.knowledge_base import KnowledgeBaseContextBuilder, KnowledgeBaseRetrievalService


DEFAULT_QUERIES = [
    ("gps tidak update di jalan", "driver"),
    ("cara cek speeding report", "operator"),
    ("minta password admin", "driver"),
    ("cara cek task driver di Task Monitor", "operator"),
]


def run_query(query: str, audience: str | None, top_k: int):
    db_manager = DatabaseManager(settings.DATABASE_URL)
    session = db_manager.get_session()
    try:
        retrieval = KnowledgeBaseRetrievalService(session)
        results = retrieval.search(query, audience=audience, top_k=top_k, log=False)
        print("=" * 88)
        print(f"QUERY    : {query}")
        print(f"AUDIENCE : {audience or '-'}")
        print(f"RESULTS  : {len(results)}")
        for idx, result in enumerate(results, 1):
            print("-" * 88)
            print(f"{idx}. score={result.score:.3f} method={result.retrieval_method}")
            print(f"   doc={result.doc_id} section={result.heading_path}")
            print(f"   {result.content[:420].replace(chr(10), ' ')}...")
        if results:
            print("-" * 88)
            print("CONTEXT PREVIEW")
            print(KnowledgeBaseContextBuilder(max_chars=1200).build_context(results))
    finally:
        session.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Test TRAMOS KB retrieval")
    parser.add_argument("query", nargs="*", help="Query text. If empty, default queries run.")
    parser.add_argument("--audience", default=None, help="Audience filter, e.g. driver/operator")
    parser.add_argument("--top-k", type=int, default=settings.KB_TOP_K)
    args = parser.parse_args()

    if args.query:
        run_query(" ".join(args.query), args.audience, args.top_k)
    else:
        for query, audience in DEFAULT_QUERIES:
            run_query(query, audience, args.top_k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
