#!/usr/bin/env python3
"""Preflight check untuk deployment VPS TRAMOS.

Jalankan setelah `.env.production` disiapkan dan service database/backend menyala.
Script ini tidak membuat tiket dan tidak mengirim WhatsApp; hanya validasi koneksi.
"""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database_models import DatabaseManager  # noqa: E402
from app.services.knowledge_base import KnowledgeBaseRetrievalService  # noqa: E402
from app.services.llm_client import create_llm_client  # noqa: E402
from app.services.osticket_service import osticket_service  # noqa: E402


def ok(label: str, detail: str = "") -> bool:
    print(f"[OK] {label}{': ' + detail if detail else ''}")
    return True


def fail(label: str, detail: str) -> bool:
    print(f"[FAIL] {label}: {detail}")
    return False


def check_tcp(url: str, label: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        return fail(label, f"URL invalid: {url}")
    try:
        with socket.create_connection((host, port), timeout=5):
            return ok(label, f"{host}:{port}")
    except Exception as exc:
        return fail(label, f"{host}:{port} {type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="TRAMOS VPS production preflight")
    parser.add_argument("--check-llm", action="store_true", help="Panggil provider LLM satu kali.")
    parser.add_argument("--check-embedding", action="store_true", help="Panggil endpoint embedding satu kali.")
    args = parser.parse_args()

    checks: list[bool] = []

    checks.append(ok("environment", settings.ENVIRONMENT))
    checks.append(ok("database_url_host", settings.DATABASE_URL.split("@")[-1].split("/")[0] if "@" in settings.DATABASE_URL else "configured"))

    try:
        manager = DatabaseManager(settings.DATABASE_URL)
        session = manager.get_session()
        try:
            session.execute(text("SELECT 1"))
            checks.append(ok("postgres", "SELECT 1"))
            kb_health = KnowledgeBaseRetrievalService(session).health()
            checks.append(
                ok(
                    "knowledge_base",
                    f"{kb_health['documents']} docs, {kb_health['chunks']} chunks, pgvector={kb_health['pgvector_enabled']}",
                )
            )
        finally:
            session.close()
    except Exception as exc:
        checks.append(fail("postgres/knowledge_base", str(exc)[:240]))

    if settings.OSTICKET_BASE_URL or settings.OSTICKET_API_URL:
        checks.append(check_tcp(settings.OSTICKET_BASE_URL or settings.OSTICKET_API_URL, "osticket_tcp"))
        checks.append(ok("osticket_api_key", "set" if osticket_service.api_key else "missing"))
    else:
        checks.append(fail("osticket", "OSTICKET_BASE_URL empty"))

    checks.append(ok("whatsapp_phone_id", "set" if settings.WHATSAPP_PHONE_ID else "missing"))
    checks.append(ok("whatsapp_token", "set" if settings.WHATSAPP_API_TOKEN else "missing"))
    checks.append(ok("webhook_verify_token", "set" if settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN else "missing"))

    if args.check_embedding:
        try:
            response = requests.post(
                f"{settings.EMBEDDING_OLLAMA_URL.rstrip('/')}/api/embed",
                json={"model": settings.EMBEDDING_MODEL, "input": "test tramos embedding"},
                timeout=settings.EMBEDDING_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            vector = data.get("embeddings", [[]])[0] if data.get("embeddings") else data.get("embedding", [])
            checks.append(ok("embedding", f"{settings.EMBEDDING_MODEL}, dim={len(vector)}"))
        except Exception as exc:
            checks.append(fail("embedding", str(exc)[:240]))

    if args.check_llm:
        try:
            client = create_llm_client("vps-preflight")
            if not client.available:
                checks.append(fail("llm", f"{client.provider} not available"))
            else:
                response = client.generate_content("Jawab singkat: TRAMOS production preflight OK.")
                checks.append(ok("llm", response.text[:120].replace("\n", " ")))
        except Exception as exc:
            checks.append(fail("llm", str(exc)[:240]))

    passed = all(checks)
    print("")
    print("RESULT:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
