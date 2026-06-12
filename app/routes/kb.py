"""
Knowledge Base / RAG API routes.

Endpoints are intended for dashboard debugging, admin reindexing, and health checks.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.routes.auth import verify_token
from app.services.knowledge_base import (
    GeminiEmbeddingService,
    KnowledgeBaseContextBuilder,
    KnowledgeBaseIngestionService,
    KnowledgeBaseRetrievalService,
    result_to_dict,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])


def get_db():
    from main import db_manager

    if not db_manager:
        raise HTTPException(status_code=500, detail="Database not available")
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def require_admin(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Admin token required")
    token = authorization.split(" ", 1)[1].strip()
    payload = verify_token(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return payload


class KBSearchRequest(BaseModel):
    query: str
    audience: Optional[str] = None
    category: Optional[str] = None
    top_k: Optional[int] = None
    min_score: Optional[float] = None
    include_context: bool = False


class KBReindexRequest(BaseModel):
    source_dir: Optional[str] = None
    reindex: bool = True


@router.get("/health")
async def kb_health(db: Session = Depends(get_db)):
    retrieval = KnowledgeBaseRetrievalService(db)
    return retrieval.health()


@router.post("/search")
async def kb_search(request: KBSearchRequest, db: Session = Depends(get_db)):
    retrieval = KnowledgeBaseRetrievalService(db)
    results = retrieval.search(
        request.query,
        audience=request.audience,
        category=request.category,
        top_k=request.top_k,
        min_score=request.min_score,
    )
    response = {
        "query": request.query,
        "count": len(results),
        "results": [result_to_dict(result) for result in results],
    }
    if request.include_context:
        response["context"] = KnowledgeBaseContextBuilder().build_context(results)
    return response


@router.post("/reindex")
async def kb_reindex(
    request: KBReindexRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    source_dir = request.source_dir or settings.KB_SOURCE_DIR
    ingestion = KnowledgeBaseIngestionService(db, GeminiEmbeddingService())
    return ingestion.ingest_folder(source_dir, reindex=request.reindex)
