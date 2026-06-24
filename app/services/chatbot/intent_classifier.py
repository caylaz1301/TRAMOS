"""Klasifikasi intent deterministik untuk menjaga dialog flow tetap terarah."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ConversationIntent(str, Enum):
    TROUBLESHOOTING = "troubleshooting"
    INFORMATIONAL = "informational"
    EMERGENCY = "emergency"
    REALTIME_REQUEST = "realtime_request"
    TICKET_REQUEST = "ticket_request"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass(frozen=True)
class IntentResult:
    intent: ConversationIntent
    normalized_text: str
    matched_terms: tuple[str, ...] = ()
    is_in_scope: bool = True  # True jika input masih dalam scope TRAMOS


class TramosIntentClassifier:
    """Classifier berbasis domain allowlist agar topik umum tidak masuk RAG."""

    MENU_PROBLEMS = {
        "1": "GPS tidak berfungsi atau lokasi kendaraan tidak update",
        "2": "Kamera atau dashcam mengalami error",
        "3": "Baterai perangkat cepat habis atau perangkat tidak menyala",
        "4": "Koneksi perangkat terputus atau unit tampil offline",
    }

    # Kata-kata yang PASTI OUT OF SCOPE - tidak ada hubungannya dengan TRAMOS
    OUT_OF_SCOPE_TERMS = (
        # Politik & pemerintahan
        "presiden", "gubernur", "walikota", "menteri", "partai", "pemilu",
        "pilpres", "pilkada", "demo", "protest", "rezim", "korupsi pemerintah",
        # Entertainment & umum
        "nonton film", "makanan enak", "resep", "kesehatan", "obat", "rumah sakit",
        "chat gpt", "openai", "gemini ai", "claude", "bot ai", "weather", "cuaca",
        "berita hari ini", "news", "infotainment", "artis", "selebriti", "bollywood",
        # E-commerce & lainnya
        "jual", "beli", "shopee", "tokopedia", "lazada", "gojek", "grab",
        "makanan", "warung", "restoran", "hotel", "travel", "penerbangan",
        # Lainnya
        "password facebook", "hack", "crack", "ilegal", "penipuan online",
        "bitcoin", "crypto", "investation", "forex", "saham",
    )

    # Kata-kata yang menunjukkan masalah/issue kendaraan/perangkat
    PROBLEM_MARKERS = (
        "error", "gagal", "tidak bisa", "gabisa", "nggak bisa", "ga bisa",
        "tidak update", "mati", "hilang", "offline", "putus", "blank",
        "hitam", "lambat", "lemot", "rusak", "mogok", "pecah", "panas",
        "habis", "bermasalah", "tidak muncul", "tidak berfungsi", "tidak jalan",
        "ngak bisa", "problem", "issue", "kejang", "overheat", "glitch",
        "lag", "restart", "loading", "not responding", "force close", "crash",
        "hang", "freeze", "blackscreen", "black screen", "tidak bisa nyala",
        "tidak bisa start", "susah nyala", "sulit start", "mau hidup",
        "keluar jalur", "lupa rute", "rute hilang", "arah hilang", "tersesat",
        "ban bocor", "oli bocor", "mesin bunyi", "bunyi aneh", "getaran",
        "goyang", "oleng", "susah steered", "rem blong", "brebet", "berasap",
        # Pertanyaan tentang masalah
        "kenapa", "mengapa", "penyebab", "solusi", "perbaiki", "benerin",
        "service", "servis", "perawatan", "check", "cek", "diagnosis",
    )

    # Pertanyaan informational (butuh panduan/bantuan info)
    INFORMATIONAL_MARKERS = (
        "apa itu", "apa fungsi", "bagaimana cara", "cara ", "panduan",
        "jelaskan", "penjelasan", "sop", "prosedur", "dimana menu", "di mana menu",
        "fungsi ", "tutorial", "guide", "petunjuk", "langkah", "step by step",
    )

    # Istilah TRAMOS yang menunjukkan input masih dalam scope
    IN_SCOPE_TERMS = (
        # Core TRAMOS
        "tramos", "tracking", "monitoring", "fleet", "gps", "unit", "kendaraan",
        "mobil", "truk", "truck", "driver", "pengemudi", "operator", "kamera",
        "camera", "dashcam", "sensor", "geofence", "report", "laporan", "task",
        "trip", "route", "rute", "aplikasi", "dashboard", "login", "akun",
        # Masalah teknis
        "koneksi", "internet", "baterai", "aki", "device", "perangkat", "mesin",
        "ban", "rem", "kecelakaan", "accident", "mogok", "overspeed", "speeding",
        "fatigue", "fuel", "bahan bakar", "suhu", "cargo", "tiket", "ticket",
        "helpdesk", "service", "servis", "maintenance", "safety", "keselamatan",
        "jalan", "lokasi", "posisi", "sinyal", "video", "rekaman", "nyala",
        # Chat user natural language
        "masalah", "kendala", "gangguan", "issue", "problem", "trouble",
        "gimana", "begimana", "cara nya", "caranya", "gimana sih", "kenapa ya",
        # Pertanyaan bantuan
        "bisa bantu", "tolong", "bantuin", "minta tolong", "mau tanya",
        "ada yang", "ada yang bisa", "bisa gak", "bisa gak sih", "help",
        # Kondisi jalan
        "jalur", "arah", "jalan", "tol", "highway", "pantura", "arteri",
        "pool", "depo", "garasi", "terminal", "stasiun", "bandara",
        # Keadaan darurat
        "darurat", "emergency", "urgent", "segera", "kritis", "bahaya",
    )

    EMERGENCY_TERMS = (
        "kecelakaan", "accident", "tabrakan", "rem blong", "kendaraan terbakar",
        "truk terbakar", "kebakaran", "ban pecah", "terguling", "korban",
        "darurat", "emergency", "bahaya",
    )

    REALTIME_TERMS = (
        "lokasi realtime", "lokasi real time", "posisi realtime", "posisi real time",
        "lokasi sekarang", "posisi sekarang", "cek kendaraan sekarang", "tracking sekarang",
    )

    TICKET_TERMS = (
        "buat tiket", "buatkan tiket", "bikin tiket", "laporkan ke teknisi",
        "eskalasi ke teknisi", "hubungi teknisi",
    )

    @classmethod
    def is_out_of_scope(cls, text: str) -> bool:
        """
        Smart check: True jika input jelas OUT OF SCOPE (tidak ada hubungannya sama TRAMOS).
        False jika masih dalam scope (meskipun belum tentu ada solusinya).
        """
        normalized = cls.normalize(text)

        # Check OUT OF SCOPE terms FIRST - kalau ada, langsung tolak
        for term in cls.OUT_OF_SCOPE_TERMS:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized):
                return True

        # Check IN SCOPE terms - kalau ada, berarti masih dalam scope
        for term in cls.IN_SCOPE_TERMS:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized):
                return False

        # Check if it's a question about help/support
        help_patterns = (
            r"\bbisa\b.*\bantu\b",  # "bisa bantu"
            r"\btolong\b",  # "tolong"
            r"\bmau\s+tanya\b",  # "mau tanya"
            r"\bminta\s+bantu\b",  # "minta bantu"
            r"\bhelp\b.*\bme\b",  # "help me"
        )
        for pattern in help_patterns:
            if re.search(pattern, normalized):
                return False

        # Check if it's a problem description
        for term in cls.PROBLEM_MARKERS:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized):
                return False

        # Kalau tidak ada OUT OF SCOPE dan tidak ada IN SCOPE → default ke IN SCCOPE
        # Ini mencegah bot menolak input yang mungkin valid tapi tidak ada dalam list
        # User akan tetap diminta deskripsi masalah

        return False  # Default: assume in-scope, minta detail

    @classmethod
    def classify(cls, text: str) -> IntentResult:
        normalized = cls.normalize(text)

        # OUT OF SCOPE check FIRST
        if cls.is_out_of_scope(text):
            return IntentResult(
                ConversationIntent.OUT_OF_SCOPE,
                normalized,
                is_in_scope=False
            )

        # Emergency check
        if cls._matched(normalized, cls.EMERGENCY_TERMS):
            return IntentResult(
                ConversationIntent.EMERGENCY,
                normalized,
                cls._matched(normalized, cls.EMERGENCY_TERMS),
                is_in_scope=True
            )

        # Realtime request check
        if cls._matched(normalized, cls.REALTIME_TERMS):
            return IntentResult(
                ConversationIntent.REALTIME_REQUEST,
                normalized,
                cls._matched(normalized, cls.REALTIME_TERMS),
                is_in_scope=True
            )

        # Ticket request check
        if cls._matched(normalized, cls.TICKET_TERMS):
            return IntentResult(
                ConversationIntent.TICKET_REQUEST,
                normalized,
                cls._matched(normalized, cls.TICKET_TERMS),
                is_in_scope=True
            )

        # Informational check FIRST - "bagaimana cara..." harus dianggap informational
        # meskipun ada kata "cek" yang mirip problem marker
        informational = cls._matched(normalized, cls.INFORMATIONAL_MARKERS)
        if informational:
            return IntentResult(
                ConversationIntent.INFORMATIONAL,
                normalized,
                informational,
                is_in_scope=True
            )

        # Problem markers found → troubleshooting
        problem_markers = cls._matched(normalized, cls.PROBLEM_MARKERS)
        if problem_markers:
            return IntentResult(
                ConversationIntent.TROUBLESHOOTING,
                normalized,
                problem_markers,
                is_in_scope=True
            )

        # In scope terms but no specific intent → troubleshooting (but need more info)
        in_scope = cls._matched(normalized, cls.IN_SCOPE_TERMS)
        if in_scope:
            return IntentResult(
                ConversationIntent.TROUBLESHOOTING,
                normalized,
                in_scope,
                is_in_scope=True
            )

        # Default: assume troubleshooting (user butuh help), minta detail masalah
        return IntentResult(
            ConversationIntent.TROUBLESHOOTING,
            normalized,
            is_in_scope=True
        )

    @staticmethod
    def normalize(text: str) -> str:
        value = re.sub(r"[^\w\s:+-]", " ", (text or "").lower())
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _matched(text: str, terms: tuple[str, ...]) -> tuple[str, ...]:
        matches = []
        for term in terms:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text):
                matches.append(term)
        return tuple(matches)
