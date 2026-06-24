"""Koordinasi pemrosesan percakapan WhatsApp lintas worker.

Redis menjadi mekanisme utama untuk lock per nomor dan deduplikasi message ID.
Fallback lokal tetap tersedia untuk development, tetapi production sebaiknya
selalu menjalankan Redis.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class ConversationCoordinator:
    """Menjamin satu nomor WhatsApp diproses berurutan dan idempotent."""

    _RELEASE_LOCK_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    end
    return 0
    """

    def __init__(self) -> None:
        self._redis = None
        self._redis_checked = False
        self._local_locks: dict[str, asyncio.Lock] = {}
        self._local_locks_guard = asyncio.Lock()
        self._local_message_ids: dict[str, float] = {}
        self._local_dedup_guard = asyncio.Lock()

    async def initialize(self) -> bool:
        """Hubungkan Redis secara lazy agar aplikasi tetap bisa hidup saat lokal."""
        if self._redis_checked:
            return self._redis is not None

        self._redis_checked = True
        if not settings.REDIS_URL:
            return False

        try:
            from redis.asyncio import Redis

            client = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3,
                health_check_interval=30,
            )
            await client.ping()
            self._redis = client
            logger.info("Redis conversation coordinator connected")
            return True
        except Exception as exc:
            logger.warning(
                "Redis coordinator unavailable; using process-local fallback: %s",
                str(exc)[:160],
            )
            self._redis = None
            return False

    async def close(self) -> None:
        """Tutup koneksi Redis saat backend berhenti."""
        if self._redis is not None:
            await self._redis.aclose()
        self._redis = None
        self._redis_checked = False

    async def health(self) -> dict:
        """Status aman untuk endpoint health/readiness."""
        available = await self.initialize()
        if not available:
            return {"status": "fallback_local", "distributed": False}
        try:
            await self._redis.ping()
            return {"status": "connected", "distributed": True}
        except Exception as exc:
            return {
                "status": f"error: {str(exc)[:80]}",
                "distributed": False,
            }

    async def claim_message(self, message_id: str) -> bool:
        """Klaim message ID sekali saja. False berarti webhook duplikat."""
        if not message_id:
            return True

        if await self.initialize():
            key = f"tramos:whatsapp:message:{message_id}"
            claimed = await self._redis.set(
                key,
                "processing",
                ex=settings.WHATSAPP_DEDUP_TTL_SECONDS,
                nx=True,
            )
            return bool(claimed)

        async with self._local_dedup_guard:
            now = time.monotonic()
            ttl = settings.WHATSAPP_DEDUP_TTL_SECONDS
            expired = [
                key for key, timestamp in self._local_message_ids.items()
                if now - timestamp >= ttl
            ]
            for key in expired:
                self._local_message_ids.pop(key, None)

            if message_id in self._local_message_ids:
                return False
            self._local_message_ids[message_id] = now
            return True

    async def release_message(self, message_id: str) -> None:
        """Lepaskan klaim jika pemrosesan gagal sebelum menghasilkan respons."""
        if not message_id:
            return
        if await self.initialize():
            await self._redis.delete(f"tramos:whatsapp:message:{message_id}")
            return
        async with self._local_dedup_guard:
            self._local_message_ids.pop(message_id, None)

    @asynccontextmanager
    async def turn_lock(self, phone_number: str) -> AsyncIterator[None]:
        """Lock per nomor agar state tidak ditimpa request yang datang berdekatan."""
        if await self.initialize():
            token = uuid.uuid4().hex
            key = f"tramos:whatsapp:turn-lock:{phone_number}"
            deadline = time.monotonic() + settings.WHATSAPP_TURN_LOCK_TIMEOUT_SECONDS

            while time.monotonic() < deadline:
                acquired = await self._redis.set(
                    key,
                    token,
                    px=settings.WHATSAPP_TURN_LOCK_TTL_SECONDS * 1000,
                    nx=True,
                )
                if acquired:
                    try:
                        yield
                    finally:
                        try:
                            await self._redis.eval(
                                self._RELEASE_LOCK_SCRIPT,
                                1,
                                key,
                                token,
                            )
                        except Exception as exc:
                            logger.warning("Could not release Redis turn lock: %s", exc)
                    return
                await asyncio.sleep(0.05)

            raise TimeoutError(
                f"Percakapan {phone_number} masih diproses oleh request sebelumnya"
            )

        lock = await self._get_local_lock(phone_number)
        async with lock:
            yield

    async def _get_local_lock(self, phone_number: str) -> asyncio.Lock:
        async with self._local_locks_guard:
            lock = self._local_locks.get(phone_number)
            if lock is None:
                lock = asyncio.Lock()
                self._local_locks[phone_number] = lock
            return lock


conversation_coordinator = ConversationCoordinator()
