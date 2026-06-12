#!/usr/bin/env python3
"""
KB Validation Script - Validates Knowledge Base setup and retrieval

Usage:
    python scripts/validate_kb.py

This script validates:
1. KB source files exist and are readable
2. KB ingestion was successful (documents, chunks, embeddings)
3. KB retrieval works with sample queries
4. Fallback mechanisms are functional
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment
load_dotenv()


def print_header(text: str):
    """Print section header"""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_result(status: str, message: str):
    """Print test result with status indicator"""
    if status == "OK":
        print(f"  ✅ {message}")
    elif status == "FAIL":
        print(f"  ❌ {message}")
    elif status == "WARN":
        print(f"  ⚠️  {message}")
    else:
        print(f"  ℹ️  {message}")


def validate_source_files():
    """Validate KB source files exist and are readable"""
    print_header("Validasi File KB Source")

    kb_dir = Path("knowledge_base")
    if not kb_dir.exists():
        print_result("FAIL", f"Directory tidak ditemukan: {kb_dir.absolute()}")
        return False

    expected_files = [
        "tramos_driver_chatbot_kb.txt",
        "tramos_systems_operator_kb.txt"
    ]

    all_ok = True
    for filename in expected_files:
        filepath = kb_dir / filename
        if filepath.exists():
            try:
                content = filepath.read_text(encoding="utf-8")
                lines = len(content.splitlines())
                chars = len(content)
                print_result("OK", f"{filename}: {lines} lines, {chars} chars")
            except Exception as e:
                print_result("FAIL", f"{filename}: Gagal membaca - {e}")
                all_ok = False
        else:
            print_result("WARN", f"{filename}: Tidak ditemukan")
            all_ok = False

    return all_ok


def validate_database_schema():
    """Validate KB database tables and data"""
    print_header("Validasi Database Schema")

    try:
        from app.config import settings
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Check tables exist
        tables = ['kb_documents', 'kb_chunks', 'kb_ingestion_runs', 'kb_retrieval_logs']
        for table in tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print_result("OK", f"Table '{table}': {result} records")
            except Exception as e:
                print_result("FAIL", f"Table '{table}': {e}")
                return False

        # Check documents
        docs = session.execute(text("SELECT doc_id, title, category FROM kb_documents WHERE is_active = true")).fetchall()
        if docs:
            print_result("OK", f"Dokumen aktif: {len(docs)}")
            for doc in docs:
                print(f"    - {doc[0]}: {doc[1]} ({doc[2]})")
        else:
            print_result("WARN", "Tidak ada dokumen aktif. Jalankan ingest_knowledge_base.py")

        # Check chunks
        chunks = session.execute(text("SELECT COUNT(*) FROM kb_chunks WHERE is_active = true")).scalar()
        embedded = session.execute(text("SELECT COUNT(*) FROM kb_chunks WHERE embedding_json IS NOT NULL")).scalar()
        print_result("OK", f"Total chunks aktif: {chunks}")
        print_result("OK", f"Chunks dengan embedding: {embedded}")

        session.close()
        return True

    except Exception as e:
        print_result("FAIL", f"Database error: {e}")
        return False


def validate_retrieval():
    """Test KB retrieval with sample queries"""
    print_header("Validasi KB Retrieval")

    try:
        from app.config import settings
        from app.services.knowledge_base import KnowledgeBaseRetrievalService, GeminiEmbeddingService
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        if not settings.KB_RAG_ENABLED:
            print_result("WARN", "KB_RAG_ENABLED=false - retrieval test skipped")
            return True

        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()

        retrieval_service = KnowledgeBaseRetrievalService(session, GeminiEmbeddingService())

        # Sample queries untuk testing
        test_queries = [
            ("GPS tidak update lokasi", "driver"),
            ("Aplikasi crash saat dibuka", "driver"),
            ("Login gagal password salah", "driver"),
            ("Kamera tidak tampil video hitam", "driver"),
        ]

        all_ok = True
        for query, audience in test_queries:
            results = retrieval_service.search(query, audience=audience, top_k=3, log=False)
            if results:
                top_result = results[0]
                print_result("OK", f"Query: '{query}'")
                print(f"    → Top result: {top_result.title} (score: {top_result.score:.2f})")
                print(f"    → Category: {top_result.category}, Method: {top_result.retrieval_method}")
            else:
                print_result("WARN", f"Query: '{query}' - Tidak ada hasil")
                all_ok = False

        session.close()
        return all_ok

    except Exception as e:
        print_result("FAIL", f"Retrieval error: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_embedding_service():
    """Test embedding service availability"""
    print_header("Validasi Embedding Service")

    try:
        from app.services.knowledge_base import GeminiEmbeddingService

        embedding_service = GeminiEmbeddingService()

        if embedding_service.available:
            print_result("OK", f"Embedding service aktif: {embedding_service.active_model_name}")
        else:
            print_result("WARN", f"Embedding service tidak tersedia: {embedding_service._client_error or 'No API key'}")

            # Test hash fallback
            test_text = "GPS tidak update lokasi"
            hash_embedding = embedding_service._hash_embedding(test_text)
            print_result("OK", f"Hash fallback berfungsi: {len(hash_embedding)} dimensions")
            return True

        return True

    except Exception as e:
        print_result("FAIL", f"Embedding service error: {e}")
        return False


def validate_pgvector():
    """Check pgvector availability"""
    print_header("Validasi pgvector")

    try:
        from app.config import settings
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            # Check pgvector extension
            result = conn.execute(text("SELECT to_regtype('vector') IS NOT NULL")).scalar()
            if result:
                print_result("OK", "pgvector extension aktif")
            else:
                print_result("WARN", "pgvector extension tidak tersedia (fallback: cosine similarity)")

            # Check embedding_vector column
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'kb_chunks' AND column_name = 'embedding_vector'
                )
            """)).scalar()
            if result:
                print_result("OK", "embedding_vector column tersedia")
            else:
                print_result("WARN", "embedding_vector column tidak ada (fallback: embedding_json)")

        return True

    except Exception as e:
        print_result("FAIL", f"pgvector check error: {e}")
        return False


def main():
    """Main validation runner"""
    print("\n" + "=" * 60)
    print("  TRAMOS KB VALIDATION SCRIPT")
    print("=" * 60)

    results = {
        "source_files": validate_source_files(),
        "pgvector": validate_pgvector(),
        "embedding_service": validate_embedding_service(),
        "database_schema": validate_database_schema(),
        "retrieval": validate_retrieval(),
    }

    # Summary
    print_header("RINGKASAN VALIDASI")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        status = "✅ LULUS" if result else "❌ GAGAL"
        print(f"  {status} - {check}")

    print(f"\nTotal: {passed}/{total} validation berhasil")

    if passed == total:
        print("\n🎉 Semua validation berhasil! KB siap digunakan.\n")
        return 0
    else:
        print("\n⚠️  Beberapa validation gagal. Periksa output di atas.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())