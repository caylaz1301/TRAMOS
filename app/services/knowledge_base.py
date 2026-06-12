"""
Production knowledge base RAG services for TRAMOS.

This module keeps the implementation self-contained:
- TXT metadata parsing and chunking
- Gemini/Ollama embedding with deterministic fallback for local tests
- PostgreSQL persistence
- Hybrid keyword + vector retrieval with pgvector fallback
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import requests
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database_models import KBChunk, KBDocument, KBIngestionRun, KBRetrievalLog

logger = logging.getLogger(__name__)


@dataclass
class KBParsedDocument:
    path: Path
    metadata: Dict[str, Any]
    title: str
    content: str
    source_hash: str


@dataclass
class KBParsedChunk:
    chunk_index: int
    heading_path: str
    content: str
    content_hash: str
    start_char_pos: int
    end_char_pos: int
    token_estimate: int


@dataclass
class KBRetrievalResult:
    chunk_id: int
    document_id: int
    doc_id: str
    title: str
    heading_path: str
    content: str
    audience: str
    category: str
    tags: List[str]
    score: float
    source_path: str
    retrieval_method: str


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_tags(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [item.strip() for item in str(raw).split(",") if item.strip()]


def _normalize_audience(raw: Any) -> str:
    values = _normalize_tags(raw)
    return ",".join(values) if values else "general"


class GeminiEmbeddingService:
    """Generate embeddings for RAG.

    Nama class dipertahankan untuk kompatibilitas kode lama. Provider yang dipakai
    ditentukan dari env:
    - gemini: pakai Gemini Embedding API
    - ollama: pakai endpoint Ollama internal/kantor
    - hash: fallback deterministik untuk test/offline
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        provider: Optional[str] = None,
        ollama_url: Optional[str] = None,
    ):
        explicit_empty_key = api_key == ""
        self.provider = (provider or ("hash" if explicit_empty_key else settings.EMBEDDING_PROVIDER)).strip().lower()
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimensions = int(dimensions or settings.EMBEDDING_DIMENSIONS)
        self.ollama_url = (ollama_url or settings.EMBEDDING_OLLAMA_URL).rstrip("/")
        self.timeout_seconds = int(settings.EMBEDDING_REQUEST_TIMEOUT_SECONDS)
        self._client = None
        self._client_error = None
        self._last_model_name = f"fallback-hash-{self.dimensions}"

    @property
    def available(self) -> bool:
        if self.provider == "ollama":
            return bool(self.ollama_url and self.model)
        if self.provider == "gemini":
            return bool(self.api_key) and self._client_error is None
        return False

    @property
    def active_model_name(self) -> str:
        return self._last_model_name

    def _get_client(self):
        if self._client is not None:
            return None if self._client is False else self._client
        if not self.api_key:
            self._client = False
            self._client_error = "GEMINI_API_KEY is not configured"
            return None
        try:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
            return self._client
        except Exception as exc:  # pragma: no cover - depends on environment package
            self._client = False
            self._client_error = str(exc)
            logger.warning("Gemini embedding client unavailable: %s", str(exc)[:120])
            return None

    def embed_text(self, content: str, task_type: str = "RETRIEVAL_DOCUMENT", retries: int = 2) -> List[float]:
        content = (content or "").strip()
        if not content:
            return [0.0] * self.dimensions

        if self.provider == "ollama":
            for attempt in range(retries + 1):
                try:
                    embedding = self._embed_with_ollama(content)
                    if embedding:
                        self._last_model_name = f"ollama:{self.model}"
                        return self._fit_dimensions(embedding)
                except Exception as exc:  # pragma: no cover - external service behavior
                    logger.warning(
                        "Ollama embedding failed attempt %s/%s: %s",
                        attempt + 1,
                        retries + 1,
                        str(exc)[:160],
                    )
                    if attempt < retries:
                        time.sleep(1.5 * (attempt + 1))

        client = self._get_client() if self.provider == "gemini" else None
        if client:
            for attempt in range(retries + 1):
                try:
                    from google.genai import types

                    response = client.models.embed_content(
                        model=self.model,
                        contents=content,
                        config=types.EmbedContentConfig(
                            task_type=task_type,
                            output_dimensionality=self.dimensions,
                        ),
                    )
                    embedding = self._extract_embedding(response)
                    if embedding:
                        self._last_model_name = self.model
                        return self._fit_dimensions(embedding)
                except Exception as exc:  # pragma: no cover - external API behavior
                    logger.warning(
                        "Gemini embedding failed attempt %s/%s: %s",
                        attempt + 1,
                        retries + 1,
                        str(exc)[:160],
                    )
                    if attempt < retries:
                        time.sleep(1.5 * (attempt + 1))

        return self._hash_embedding(content)

    def embed_query(self, query: str) -> List[float]:
        return self.embed_text(query, task_type="RETRIEVAL_QUERY")

    def embed_document(self, content: str) -> List[float]:
        return self.embed_text(content, task_type="RETRIEVAL_DOCUMENT")

    @staticmethod
    def _extract_embedding(response: Any) -> List[float]:
        if hasattr(response, "embeddings") and response.embeddings:
            first = response.embeddings[0]
            if hasattr(first, "values"):
                return list(first.values)
            if isinstance(first, dict):
                return list(first.get("values", []))
        if hasattr(response, "embedding") and response.embedding:
            embedding = response.embedding
            if hasattr(embedding, "values"):
                return list(embedding.values)
            if isinstance(embedding, dict):
                return list(embedding.get("values", []))
        if isinstance(response, dict):
            embeddings = response.get("embeddings") or []
            if embeddings:
                return list(embeddings[0].get("values", []))
        return []

    def _embed_with_ollama(self, content: str) -> List[float]:
        """Panggil endpoint Ollama /api/embed dan parse format respons modern/lama."""
        payload = {"model": self.model, "input": content}
        response = requests.post(
            f"{self.ollama_url}/api/embed",
            json=payload,
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            # Kompatibilitas untuk Ollama lama yang masih memakai /api/embeddings.
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": content},
                timeout=self.timeout_seconds,
            )
        response.raise_for_status()
        data = response.json()
        if isinstance(data.get("embeddings"), list) and data["embeddings"]:
            return [float(value) for value in data["embeddings"][0]]
        if isinstance(data.get("embedding"), list):
            return [float(value) for value in data["embedding"]]
        return []

    def _fit_dimensions(self, embedding: Sequence[float]) -> List[float]:
        """Samakan panjang embedding dengan dimensi kolom pgvector yang aktif."""
        vector = [float(value) for value in embedding]
        if len(vector) > self.dimensions:
            vector = vector[: self.dimensions]
        elif len(vector) < self.dimensions:
            vector = vector + [0.0] * (self.dimensions - len(vector))
        return self._normalize_vector(vector)

    def _hash_embedding(self, content: str) -> List[float]:
        self._last_model_name = f"fallback-hash-{self.dimensions}"
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-zA-Z0-9_]+", content.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        return self._normalize_vector(vector)

    @staticmethod
    def _normalize_vector(vector: Sequence[float]) -> List[float]:
        norm = math.sqrt(sum(float(v) * float(v) for v in vector))
        if norm <= 0:
            return [0.0 for _ in vector]
        return [float(v) / norm for v in vector]


class KnowledgeBaseParser:
    """Parse TXT KB files with front-matter-like metadata and Markdown headings."""

    METADATA_KEYS = {
        "doc_id",
        "title",
        "audience",
        "category",
        "tags",
        "version",
        "last_updated",
        "source",
    }

    def parse_file(self, path: Path) -> KBParsedDocument:
        content = path.read_text(encoding="utf-8")
        metadata, body = self._parse_metadata(content)
        title = metadata.get("title") or self._extract_title(body) or path.stem
        doc_id = metadata.get("doc_id") or re.sub(r"[^a-z0-9_]+", "_", path.stem.lower()).strip("_")
        metadata["doc_id"] = doc_id
        metadata["title"] = title
        return KBParsedDocument(
            path=path,
            metadata=metadata,
            title=title,
            content=body.strip(),
            source_hash=_sha256(content),
        )

    def chunk_document(
        self,
        document: KBParsedDocument,
        min_chars: int = 180,
        target_chars: int = 1200,
        max_chars: int = 2200,
    ) -> List[KBParsedChunk]:
        units = self._split_sections(document.content)
        chunks: List[KBParsedChunk] = []
        buffer: List[str] = []
        heading = ""
        start_pos = 0
        cursor = 0

        def flush(end_pos: int):
            nonlocal buffer, start_pos, heading
            text_value = "\n\n".join(part.strip() for part in buffer if part.strip()).strip()
            if len(text_value) >= min_chars:
                chunks.append(
                    KBParsedChunk(
                        chunk_index=len(chunks),
                        heading_path=heading or document.title,
                        content=text_value,
                        content_hash=_sha256(text_value),
                        start_char_pos=start_pos,
                        end_char_pos=end_pos,
                        token_estimate=max(1, len(text_value.split())),
                    )
                )
            buffer = []
            start_pos = end_pos

        for section_heading, section_text, section_start, section_end in units:
            if buffer and section_heading and section_heading != heading:
                buffered_text = "\n\n".join(buffer).strip()
                if len(buffered_text) >= min_chars:
                    flush(section_start)
            heading = section_heading or heading or document.title
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
            for paragraph in paragraphs:
                if not buffer:
                    start_pos = section_start
                candidate = "\n\n".join(buffer + [paragraph])
                if len(candidate) > max_chars and buffer:
                    flush(cursor)
                buffer.append(paragraph)
                cursor = section_end
                if len("\n\n".join(buffer)) >= target_chars:
                    flush(cursor)

        if buffer:
            flush(len(document.content))

        if not chunks and document.content.strip():
            clean = document.content.strip()
            chunks.append(
                KBParsedChunk(
                    chunk_index=0,
                    heading_path=document.title,
                    content=clean[:max_chars],
                    content_hash=_sha256(clean[:max_chars]),
                    start_char_pos=0,
                    end_char_pos=min(len(clean), max_chars),
                    token_estimate=max(1, len(clean[:max_chars].split())),
                )
            )
        return chunks

    def _parse_metadata(self, content: str) -> tuple[Dict[str, Any], str]:
        metadata: Dict[str, Any] = {}
        lines = content.splitlines()
        body_start = 0
        for idx, line in enumerate(lines[:30]):
            stripped = line.strip()
            if not stripped:
                body_start = idx + 1
                continue
            if stripped.startswith("#"):
                body_start = idx
                break
            if ":" not in stripped:
                body_start = idx
                break
            key, value = stripped.split(":", 1)
            key = key.strip().lower()
            if key not in self.METADATA_KEYS:
                body_start = idx
                break
            metadata[key] = value.strip()
            body_start = idx + 1
        metadata["tags"] = _normalize_tags(metadata.get("tags"))
        metadata["audience"] = _normalize_audience(metadata.get("audience"))
        return metadata, "\n".join(lines[body_start:])

    @staticmethod
    def _extract_title(content: str) -> Optional[str]:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
            if stripped and len(stripped) > 20:
                return stripped[:500]
        return None

    @staticmethod
    def _split_sections(content: str) -> List[tuple[str, str, int, int]]:
        matches = list(re.finditer(r"(?m)^(#{1,4})\s+(.+)$", content))
        if not matches:
            return [("", content, 0, len(content))]

        sections: List[tuple[str, str, int, int]] = []
        heading_stack: List[str] = []
        for index, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(title)
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            section_text = content[start:end].strip()
            sections.append((" > ".join(heading_stack), section_text, start, end))
        return sections


class KnowledgeBaseIngestionService:
    """Load KB TXT files, chunk, embed, and store in PostgreSQL."""

    def __init__(
        self,
        db: Session,
        embedding_service: Optional[GeminiEmbeddingService] = None,
        parser: Optional[KnowledgeBaseParser] = None,
    ):
        self.db = db
        self.embedding_service = embedding_service or GeminiEmbeddingService()
        self.parser = parser or KnowledgeBaseParser()
        self.pgvector_enabled = self._pgvector_available()

    def ingest_folder(self, source_dir: str, reindex: bool = False) -> Dict[str, Any]:
        source_path = Path(source_dir)
        run = KBIngestionRun(source_dir=str(source_path), status="running", started_at=datetime.utcnow())
        self.db.add(run)
        self.db.commit()

        errors: List[str] = []
        files = sorted(source_path.rglob("*.txt")) if source_path.exists() else []
        run.files_found = len(files)
        self.db.commit()

        if not source_path.exists():
            run.status = "failed"
            run.errors = [f"Knowledge base folder not found: {source_path}"]
            run.finished_at = datetime.utcnow()
            self.db.commit()
            return self._run_summary(run)

        try:
            for file_path in files:
                try:
                    parsed = self.parser.parse_file(file_path)
                    doc_id = parsed.metadata["doc_id"]
                    existing = self.db.query(KBDocument).filter(KBDocument.doc_id == doc_id).first()
                    if existing and existing.source_hash == parsed.source_hash and not reindex:
                        run.skipped_unchanged += 1
                        continue

                    document = existing or KBDocument(doc_id=doc_id, title=parsed.title, source_path=str(file_path))
                    document.title = parsed.title
                    document.source_path = str(file_path)
                    document.source_hash = parsed.source_hash
                    document.audience = parsed.metadata.get("audience", "general")
                    document.category = parsed.metadata.get("category", "general")
                    document.tags = _normalize_tags(parsed.metadata.get("tags"))
                    document.version = parsed.metadata.get("version")
                    document.source = parsed.metadata.get("source")
                    document.meta_data = parsed.metadata
                    document.is_active = True
                    document.updated_at = datetime.utcnow()
                    if not existing:
                        self.db.add(document)
                        self.db.flush()
                    else:
                        self.db.query(KBChunk).filter(KBChunk.document_id == document.id).delete()
                        self.db.flush()

                    parsed_chunks = self.parser.chunk_document(parsed)
                    document.chunk_count = len(parsed_chunks)
                    run.documents_processed += 1

                    for parsed_chunk in parsed_chunks:
                        embedding = self.embedding_service.embed_document(parsed_chunk.content)
                        chunk = KBChunk(
                            document_id=document.id,
                            chunk_index=parsed_chunk.chunk_index,
                            heading_path=parsed_chunk.heading_path,
                            content=parsed_chunk.content,
                            content_hash=parsed_chunk.content_hash,
                            audience=document.audience,
                            category=document.category,
                            tags=document.tags,
                            embedding_model=self.embedding_service.active_model_name,
                            embedding_dimensions=len(embedding),
                            embedding_json=embedding,
                            token_estimate=parsed_chunk.token_estimate,
                            start_char_pos=parsed_chunk.start_char_pos,
                            end_char_pos=parsed_chunk.end_char_pos,
                            is_active=True,
                        )
                        self.db.add(chunk)
                        self.db.flush()
                        run.chunks_created += 1
                        if embedding:
                            run.chunks_embedded += 1

                    self.db.commit()
                    if self.pgvector_enabled:
                        self._backfill_pgvector_for_document(document.id)
                except Exception as exc:
                    self.db.rollback()
                    error = f"{file_path}: {str(exc)[:300]}"
                    errors.append(error)
                    logger.exception("KB ingestion error for %s", file_path)

            run.status = "success" if not errors else "partial"
            run.errors = errors
            run.finished_at = datetime.utcnow()
            self.db.commit()
            return self._run_summary(run)
        except Exception as exc:
            self.db.rollback()
            run.status = "failed"
            run.errors = errors + [str(exc)[:300]]
            run.finished_at = datetime.utcnow()
            self.db.add(run)
            self.db.commit()
            return self._run_summary(run)

    def _pgvector_available(self) -> bool:
        try:
            result = self.db.execute(text("SELECT to_regtype('vector') IS NOT NULL")).scalar()
            if not result:
                self.db.rollback()
                return False
            has_column = self.db.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'kb_chunks' AND column_name = 'embedding_vector'
                    )
                    """
                )
            ).scalar()
            self.db.rollback()
            return bool(has_column)
        except Exception:
            self.db.rollback()
            return False

    def _backfill_pgvector_for_document(self, document_id: int):
        chunks = (
            self.db.query(KBChunk)
            .filter(KBChunk.document_id == document_id, KBChunk.embedding_json.isnot(None))
            .all()
        )
        for chunk in chunks:
            self._try_store_pgvector(chunk.id, chunk.embedding_json or [])
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            if settings.KB_PGVECTOR_REQUIRED:
                raise
            logger.debug("Skipping pgvector backfill commit: %s", str(exc)[:120])

    def _try_store_pgvector(self, chunk_id: int, embedding: Sequence[float]) -> bool:
        if not self.pgvector_enabled or not embedding:
            return False
        vector_literal = "[" + ",".join(f"{float(v):.8f}" for v in embedding) + "]"
        try:
            self.db.execute(
                text("UPDATE kb_chunks SET embedding_vector = CAST(:embedding AS vector) WHERE id = :chunk_id"),
                {"embedding": vector_literal, "chunk_id": chunk_id},
            )
            return True
        except Exception as exc:
            self.db.rollback()
            self.pgvector_enabled = False
            if settings.KB_PGVECTOR_REQUIRED:
                raise
            logger.debug("Skipping pgvector store for chunk %s: %s", chunk_id, str(exc)[:120])
            return False

    @staticmethod
    def _run_summary(run: KBIngestionRun) -> Dict[str, Any]:
        return {
            "run_id": run.id,
            "status": run.status,
            "source_dir": run.source_dir,
            "files_found": run.files_found,
            "documents_processed": run.documents_processed,
            "chunks_created": run.chunks_created,
            "chunks_embedded": run.chunks_embedded,
            "skipped_unchanged": run.skipped_unchanged,
            "errors": run.errors or [],
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }


class KnowledgeBaseRetrievalService:
    """Hybrid KB retrieval using keyword + pgvector/Python cosine fallback."""

    STOPWORDS = {
        "apa",
        "itu",
        "ini",
        "yang",
        "dan",
        "ke",
        "di",
        "dari",
        "untuk",
        "dengan",
        "adalah",
        "ada",
        "bisa",
        "cara",
        "bagaimana",
        "kenapa",
        "tolong",
        "mohon",
        "bantu",
        "saya",
        "aku",
        "kamu",
        "kami",
        "the",
        "is",
        "what",
        "how",
        "can",
        "please",
    }

    def __init__(self, db: Session, embedding_service: Optional[GeminiEmbeddingService] = None):
        self.db = db
        self.embedding_service = embedding_service or GeminiEmbeddingService()

    def search(
        self,
        query: str,
        audience: Optional[str] = None,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        log: bool = True,
    ) -> List[KBRetrievalResult]:
        """
        Hybrid search: Gabungan vector search (pgvector/cosine) + keyword search.

        Prioritas retrieval:
        1. Jika pgvector tersedia → gunakan vector similarity search
        2. Jika tidak ada hasil pgvector → fallback ke cosine similarity
        3. Selalu jalankan keyword search sebagai pelengkap
        4. Merge hasil dengan scoring scheme (vector 72% + keyword 38%)
        5. Filter berdasarkan min_score threshold

        Fallback chain:
        pgvector → cosine → keyword (selalu jalan)
        """
        started = time.perf_counter()
        top_k = int(top_k or settings.KB_TOP_K)
        min_score = float(settings.KB_MIN_SCORE if min_score is None else min_score)
        query = (query or "").strip()
        if not query:
            return []

        query_embedding = self.embedding_service.embed_query(query)
        vector_results: List[KBRetrievalResult] = []
        used_pgvector = False
        if query_embedding:
            # Coba pgvector dulu (paling akurat)
            vector_results = self._search_pgvector(query_embedding, audience, category, top_k * 2)
            used_pgvector = bool(vector_results)
            # Fallback ke cosine similarity jika pgvector tidak ada hasil
            if not vector_results:
                vector_results = self._search_cosine(query_embedding, audience, category, top_k * 2)

        # Keyword search selalu jalan sebagai pelengkap
        keyword_results = self._search_keyword(query, audience, category, top_k * 2)
        # Merge hasil dengan weighted scoring
        merged = self._merge_results(keyword_results, vector_results, top_k, min_score)

        if log:
            self._log_retrieval(
                query=query,
                audience=audience,
                category=category,
                top_k=top_k,
                min_score=min_score,
                results=merged,
                used_pgvector=used_pgvector,
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
        return merged

    def health(self) -> Dict[str, Any]:
        doc_count = self.db.query(func.count(KBDocument.id)).scalar() or 0
        chunk_count = self.db.query(func.count(KBChunk.id)).scalar() or 0
        embedded_count = self.db.query(func.count(KBChunk.id)).filter(KBChunk.embedding_json.isnot(None)).scalar() or 0
        return {
            "enabled": settings.KB_RAG_ENABLED,
            "documents": doc_count,
            "chunks": chunk_count,
            "embedded_chunks": embedded_count,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,
            "pgvector_enabled": self._pgvector_available(),
            "source_dir": settings.KB_SOURCE_DIR,
        }

    def _base_query(self, audience: Optional[str], category: Optional[str]):
        query = (
            self.db.query(KBChunk, KBDocument)
            .join(KBDocument, KBChunk.document_id == KBDocument.id)
            .filter(KBChunk.is_active.is_(True), KBDocument.is_active.is_(True))
        )
        if audience:
            audience_value = audience.lower()
            query = query.filter(func.lower(KBChunk.audience).like(f"%{audience_value}%"))
        if category:
            category_value = category.lower()
            query = query.filter(func.lower(KBChunk.category).like(f"%{category_value}%"))
        return query

    def _search_keyword(
        self,
        query: str,
        audience: Optional[str],
        category: Optional[str],
        limit: int,
    ) -> List[KBRetrievalResult]:
        tokens = [
            token
            for token in re.findall(r"[a-zA-Z0-9_]+", query.lower())
            if len(token) > 2 and token not in self.STOPWORDS
        ]
        if not tokens:
            return []
        db_query = self._base_query(audience, category)
        filters = []
        for token in tokens[:5]:
            like = f"%{token}%"
            filters.append(func.lower(KBChunk.content).like(like))
            filters.append(func.lower(KBChunk.heading_path).like(like))
            filters.append(func.lower(KBDocument.title).like(like))
        rows = db_query.filter(or_(*filters)).limit(limit * 4).all()
        results = []
        for chunk, document in rows:
            content_lower = (chunk.content or "").lower()
            heading_lower = (chunk.heading_path or "").lower()
            title_lower = (document.title or "").lower()
            content_hits = sum(1 for token in tokens if token in content_lower)
            heading_hits = sum(1 for token in tokens if token in heading_lower)
            title_hits = sum(1 for token in tokens if token in title_lower)
            score = min(1.0, (content_hits + heading_hits * 1.5 + title_hits * 2.0) / max(2.0, len(tokens) * 2.5))
            results.append(self._to_result(chunk, document, score, "keyword"))
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]

    def _search_pgvector(
        self,
        embedding: Sequence[float],
        audience: Optional[str],
        category: Optional[str],
        limit: int,
    ) -> List[KBRetrievalResult]:
        if not self._pgvector_available():
            return []
        vector_literal = "[" + ",".join(f"{float(v):.8f}" for v in embedding) + "]"
        where = [
            "c.is_active = TRUE",
            "d.is_active = TRUE",
            "c.embedding_vector IS NOT NULL",
        ]
        params: Dict[str, Any] = {"embedding": vector_literal, "limit": limit}
        if audience:
            where.append("LOWER(c.audience) LIKE :audience")
            params["audience"] = f"%{audience.lower()}%"
        if category:
            where.append("LOWER(c.category) LIKE :category")
            params["category"] = f"%{category.lower()}%"

        sql = f"""
            SELECT c.id AS chunk_id, c.document_id, d.doc_id, d.title, c.heading_path,
                   c.content, c.audience, c.category, c.tags, d.source_path,
                   1 - (c.embedding_vector <=> CAST(:embedding AS vector)) AS score
            FROM kb_chunks c
            JOIN kb_documents d ON d.id = c.document_id
            WHERE {' AND '.join(where)}
            ORDER BY c.embedding_vector <=> CAST(:embedding AS vector)
            LIMIT :limit
        """
        try:
            rows = self.db.execute(text(sql), params).mappings().all()
            return [
                KBRetrievalResult(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    doc_id=row["doc_id"],
                    title=row["title"],
                    heading_path=row["heading_path"] or "",
                    content=row["content"],
                    audience=row["audience"],
                    category=row["category"],
                    tags=_normalize_tags(row["tags"]),
                    score=max(0.0, float(row["score"] or 0.0)),
                    source_path=row["source_path"],
                    retrieval_method="pgvector",
                )
                for row in rows
            ]
        except Exception as exc:
            self.db.rollback()
            if settings.KB_PGVECTOR_REQUIRED:
                raise
            logger.debug("pgvector search unavailable: %s", str(exc)[:160])
            return []

    def _search_cosine(
        self,
        embedding: Sequence[float],
        audience: Optional[str],
        category: Optional[str],
        limit: int,
    ) -> List[KBRetrievalResult]:
        rows = self._base_query(audience, category).filter(KBChunk.embedding_json.isnot(None)).all()
        results = []
        for chunk, document in rows:
            score = self._cosine(embedding, chunk.embedding_json or [])
            if score > 0:
                results.append(self._to_result(chunk, document, score, "cosine"))
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        if not left or not right:
            return 0.0
        size = min(len(left), len(right))
        dot = sum(float(left[i]) * float(right[i]) for i in range(size))
        left_norm = math.sqrt(sum(float(left[i]) * float(left[i]) for i in range(size)))
        right_norm = math.sqrt(sum(float(right[i]) * float(right[i]) for i in range(size)))
        if left_norm <= 0 or right_norm <= 0:
            return 0.0
        return max(0.0, dot / (left_norm * right_norm))

    @staticmethod
    def _merge_results(
        keyword_results: List[KBRetrievalResult],
        vector_results: List[KBRetrievalResult],
        top_k: int,
        min_score: float,
    ) -> List[KBRetrievalResult]:
        merged: Dict[int, KBRetrievalResult] = {}
        for result in vector_results:
            merged[result.chunk_id] = result
        for result in keyword_results:
            if result.chunk_id in merged:
                existing = merged[result.chunk_id]
                existing.score = min(1.0, existing.score * 0.72 + result.score * 0.38)
                existing.retrieval_method = f"{existing.retrieval_method}+keyword"
            else:
                merged[result.chunk_id] = result
        final_results = [result for result in merged.values() if result.score >= min_score]
        final_results.sort(key=lambda item: item.score, reverse=True)
        return final_results[:top_k]

    @staticmethod
    def _to_result(chunk: KBChunk, document: KBDocument, score: float, method: str) -> KBRetrievalResult:
        return KBRetrievalResult(
            chunk_id=chunk.id,
            document_id=document.id,
            doc_id=document.doc_id,
            title=document.title,
            heading_path=chunk.heading_path or document.title,
            content=chunk.content,
            audience=chunk.audience,
            category=chunk.category,
            tags=_normalize_tags(chunk.tags),
            score=float(score),
            source_path=document.source_path,
            retrieval_method=method,
        )

    def _pgvector_available(self) -> bool:
        try:
            result = self.db.execute(text("SELECT to_regtype('vector') IS NOT NULL")).scalar()
            if not result:
                return False
            has_column = self.db.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'kb_chunks' AND column_name = 'embedding_vector'
                    )
                    """
                )
            ).scalar()
            return bool(has_column)
        except Exception:
            self.db.rollback()
            return False

    def _log_retrieval(
        self,
        query: str,
        audience: Optional[str],
        category: Optional[str],
        top_k: int,
        min_score: float,
        results: List[KBRetrievalResult],
        used_pgvector: bool,
        latency_ms: int,
    ):
        try:
            log = KBRetrievalLog(
                query=query,
                query_hash=_sha256(query.lower().strip()),
                audience=audience,
                category=category,
                top_k=top_k,
                min_score=min_score,
                result_count=len(results),
                top_score=results[0].score if results else 0.0,
                used_pgvector=used_pgvector,
                latency_ms=latency_ms,
                selected_chunk_ids=[result.chunk_id for result in results],
            )
            self.db.add(log)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.debug("Could not log KB retrieval: %s", str(exc)[:120])


class KnowledgeBaseContextBuilder:
    """Build compact, citation-aware RAG context for chatbot prompts."""

    def __init__(self, max_chars: Optional[int] = None):
        self.max_chars = int(max_chars or settings.KB_CONTEXT_MAX_CHARS)

    def build_context(self, results: Sequence[KBRetrievalResult]) -> str:
        parts: List[str] = []
        used_chars = 0
        for idx, result in enumerate(results, 1):
            snippet = result.content.strip()
            header = (
                f"[KB {idx}] source={result.doc_id}; title={result.title}; "
                f"section={result.heading_path}; score={result.score:.2f}; audience={result.audience}"
            )
            block = f"{header}\n{snippet}"
            if used_chars + len(block) > self.max_chars:
                remaining = self.max_chars - used_chars
                if remaining <= 300:
                    break
                block = block[:remaining].rsplit(" ", 1)[0]
            parts.append(block)
            used_chars += len(block)
            if used_chars >= self.max_chars:
                break
        return "\n\n".join(parts)

    def build_answer_prompt(self, user_question: str, results: Sequence[KBRetrievalResult]) -> str:
        context = self.build_context(results)
        return f"""You are TRAMOS AI Support Assistant.

Use ONLY the knowledge base context below to answer the user. If realtime vehicle data is not present, do not invent it. Never reveal passwords, tokens, API keys, or private credentials. Do not change task data. Do not create a ticket if the user says the problem is already solved.

Knowledge base context:
{context}

User question/problem:
{user_question}

Answer in Indonesian. Keep WhatsApp answers concise and operational. If this is troubleshooting, provide up to 5 safe steps. Do not ask the final "berhasil atau tidak" feedback question because the dialog flow will ask it after your answer. If the issue is unsafe or unresolved, say it should be escalated."""


def result_to_dict(result: KBRetrievalResult) -> Dict[str, Any]:
    return {
        "chunk_id": result.chunk_id,
        "document_id": result.document_id,
        "doc_id": result.doc_id,
        "title": result.title,
        "heading_path": result.heading_path,
        "content": result.content,
        "audience": result.audience,
        "category": result.category,
        "tags": result.tags,
        "score": result.score,
        "source_path": result.source_path,
        "retrieval_method": result.retrieval_method,
    }
