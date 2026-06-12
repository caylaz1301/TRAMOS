"""Adapter LLM TRAMOS.

File ini menyatukan cara panggil Gemini dan Claude agar service chatbot tidak
perlu tahu detail SDK masing-masing provider. Bentuk response dibuat mirip
Gemini (`response.text`) supaya kode lama tetap kompatibel.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMTextResponse:
    """Response sederhana yang kompatibel dengan pola `gemini_response.text`."""

    text: str


class UnifiedLLMClient:
    """Client terpadu untuk Gemini dan Anthropic Claude.

    Provider dipilih dari `LLM_PROVIDER`:
    - `gemini`: memakai `GEMINI_API_KEY` dan `GEMINI_MODEL`.
    - `anthropic`: memakai `ANTHROPIC_API_KEY` dan `ANTHROPIC_MODEL`.
    """

    def __init__(self, purpose: str = "chatbot"):
        self.purpose = purpose
        self.provider = (settings.LLM_PROVIDER or "gemini").strip().lower()
        self.model = ""
        self.available = False
        self._client: Optional[Any] = None

        if self.provider == "anthropic":
            self._init_anthropic()
        else:
            self.provider = "gemini"
            self._init_gemini()

    def _init_gemini(self) -> None:
        """Inisialisasi Gemini jika API key tersedia."""
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini API key kosong; LLM fallback akan dipakai.")
            return
        try:
            self.model = settings.GEMINI_MODEL
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._client = genai.GenerativeModel(self.model)
            self.available = True
            logger.info("✅ LLM %s initialized with Gemini model %s", self.purpose, self.model)
        except Exception as exc:
            logger.error("❌ Gemini init failed: %s", str(exc)[:160])

    def _init_anthropic(self) -> None:
        """Inisialisasi Anthropic Claude jika API key tersedia."""
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("Anthropic API key kosong; LLM fallback akan dipakai.")
            return
        try:
            from anthropic import Anthropic

            kwargs = {"api_key": settings.ANTHROPIC_API_KEY}
            if settings.ANTHROPIC_BASE_URL:
                kwargs["base_url"] = settings.ANTHROPIC_BASE_URL
            kwargs["timeout"] = settings.LLM_REQUEST_TIMEOUT_SECONDS

            self.model = settings.ANTHROPIC_MODEL
            self._client = Anthropic(**kwargs)
            self.available = True
            logger.info("✅ LLM %s initialized with Anthropic model %s", self.purpose, self.model)
        except Exception as exc:
            logger.error("❌ Anthropic init failed: %s", str(exc)[:160])

    def generate_content(self, prompt: str, generation_config: Optional[Any] = None) -> LLMTextResponse:
        """Generate teks dari provider aktif.

        Parameter `generation_config` sengaja menerima object bebas agar bisa
        langsung dipakai oleh pemanggil lama yang masih membuat config Gemini.
        """
        if not self.available or self._client is None:
            raise RuntimeError(f"LLM provider {self.provider} is not available")

        if self.provider == "anthropic":
            return self._generate_anthropic(prompt, generation_config)

        response = self._client.generate_content(prompt, generation_config=generation_config)
        return LLMTextResponse(text=(getattr(response, "text", "") or "").strip())

    def _generate_anthropic(self, prompt: str, generation_config: Optional[Any]) -> LLMTextResponse:
        """Generate teks dengan Claude Messages API."""
        max_tokens = int(getattr(generation_config, "max_output_tokens", 700) or 700)
        temperature = float(getattr(generation_config, "temperature", 0.3) or 0.3)

        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        parts = []
        for block in getattr(message, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return LLMTextResponse(text="\n".join(parts).strip())


def create_llm_client(purpose: str = "chatbot") -> UnifiedLLMClient:
    """Factory kecil agar service lain tidak perlu tahu class detailnya."""
    return UnifiedLLMClient(purpose=purpose)
