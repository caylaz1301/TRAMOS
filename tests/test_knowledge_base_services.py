from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database_models import Base, KBChunk, KBDocument
from app.services.knowledge_base import (
    GeminiEmbeddingService,
    KnowledgeBaseParser,
    KnowledgeBaseRetrievalService,
)


def test_kb_parser_reads_metadata_and_chunks(tmp_path: Path):
    kb_file = tmp_path / "sample.txt"
    kb_file.write_text(
        """doc_id: sample_driver
title: Sample Driver KB
audience: driver, chatbot
category: driver_support
tags: gps, aplikasi
version: 1
last_updated: 2026-06-04
source: test

# Sample Driver KB

## GPS

GPS tidak update dapat dicek dengan memastikan koneksi internet aktif, menepi di tempat aman, dan menunggu update data.

## Application

Aplikasi loading terus dapat dicoba dengan force close, tunggu 5 detik, lalu buka ulang aplikasi.
""",
        encoding="utf-8",
    )

    parser = KnowledgeBaseParser()
    doc = parser.parse_file(kb_file)
    chunks = parser.chunk_document(doc, min_chars=40)

    assert doc.metadata["doc_id"] == "sample_driver"
    assert doc.metadata["audience"] == "driver,chatbot"
    assert "gps" in doc.metadata["tags"]
    assert len(chunks) >= 2
    assert any("GPS" in chunk.heading_path for chunk in chunks)


def test_embedding_fallback_is_deterministic_without_api_key():
    service = GeminiEmbeddingService(api_key="", dimensions=32)
    first = service.embed_query("gps tidak update")
    second = service.embed_query("gps tidak update")

    assert len(first) == 32
    assert first == second
    assert sum(abs(value) for value in first) > 0


def test_retrieval_keyword_and_cosine_fallback():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    embedding_service = GeminiEmbeddingService(api_key="", dimensions=32)

    doc = KBDocument(
        doc_id="sample_driver",
        title="Sample Driver KB",
        source_path="sample.txt",
        source_hash="hash",
        audience="driver,chatbot",
        category="driver_support",
        tags=["gps"],
        is_active=True,
    )
    session.add(doc)
    session.flush()

    content = "GPS tidak update di jalan. Menepi dulu, cek koneksi internet, restart aplikasi, lalu tunggu 2 sampai 5 menit."
    session.add(
        KBChunk(
            document_id=doc.id,
            chunk_index=0,
            heading_path="GPS",
            content=content,
            content_hash="chunkhash",
            audience=doc.audience,
            category=doc.category,
            tags=doc.tags,
            embedding_model="fallback",
            embedding_dimensions=32,
            embedding_json=embedding_service.embed_document(content),
            is_active=True,
        )
    )
    session.commit()

    retrieval = KnowledgeBaseRetrievalService(session, embedding_service)
    results = retrieval.search("gps tidak update", audience="driver", top_k=3, min_score=0.01, log=False)

    assert results
    assert results[0].doc_id == "sample_driver"
    assert "GPS" in results[0].heading_path
