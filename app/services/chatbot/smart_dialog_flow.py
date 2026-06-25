"""
Advanced Smart Dialog Flow Handler - WhatsApp Optimized
Ultra-smart conversation system with context awareness, problem analysis,
multi-turn dialogue, and natural language understanding
"""

import logging
import re
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime
from app.services.chatbot.session_manager import ConversationSession, DialogState
from app.utils.smart_response_system import smart_response_system, MessageType
from app.services.chatbot.solution_searcher import solution_searcher

logger = logging.getLogger(__name__)


class SmartDialogFlowHandler:
    """
    Ultra-smart dialog flow with:
    - Context awareness
    - Problem type-specific questions
    - Natural language understanding
    - WhatsApp optimization
    - Input validation & clarification
    - Multi-turn conversation
    """
    
    # Data patterns
    PHONE_PATTERN = re.compile(r'\b(?:\+?62|0)[0-9]{8,12}\b')
    TIME_PATTERN = re.compile(r'\b(?:[01]?[0-9]|2[0-3]):[0-5][0-9]\b')
    UNIT_PATTERN = re.compile(r'\b[A-Z]{0,4}-?\d{1,4}\b|\bTRAM[A-Z]?-?\d+\b')
    
    # Problem category keywords with better matching
    PROBLEM_KEYWORDS = {
        "Vehicle": {
            "keywords": ["mogok", "stall", "breakdown", "mesin mati", "mesin tidak hidup", "engine stop", "tidak hidup", "truk mogok", "mobil mogok"],
            "emoji": "🚗",
            "follow_up": ["Mesin bisa di-start?", "Ada warning light?", "Sudah coba apa?"],
        },
        "GPS": {
            "keywords": ["gps", "tracking", "lokasi", "signal", "koordinat", "tidak ketemu", "hilang", "sinyal", "map", "posisi", "track", "navigate"],
            "emoji": "🗺️",
            "follow_up": ["Device punya view ke langit?", "GPS sudah di-restart?", "Signal ada?"],
        },
        "Application": {
            "keywords": ["aplikasi", "application", "app", "blank screen", "layar kosong", "layar blank", "force close", "crash", "hang", "loading", "tidak bisa dibuka", "menu error", "report tidak muncul"],
            "emoji": "📱",
            "follow_up": ["Sudah force close aplikasi?", "Internet stabil?", "Sudah login ulang?"],
        },
        "Camera": {
            "keywords": ["kamera", "dashcam", "video", "rekam", "camera feed", "cam", "video hitam", "kamera hitam", "gambar hitam", "tidak jelas"],
            "emoji": "📹",
            "follow_up": ["Lensa bersih?", "Kabelnya terhubung?", "Power supply OK?"],
        },
        "Battery": {
            "keywords": ["baterai", "power", "charge", "listrik", "aki", "voltage", "mati", "habis", "Low battery", "tidak menyala", "charging"],
            "emoji": "🔋",
            "follow_up": ["Berapa persen battery?", "Sudah di-charge?", "Charger ada?"],
        },
        "Connectivity": {
            "keywords": ["internet", "koneksi", "network", "signal", "wifi", "offline", "disconnect", "putus", "no connection", "timeout", "sync", "lelet", "lambat", "slow", "lemot", "lag", "buffering", "loading"],
            "emoji": "📡",
            "follow_up": ["Pakai WiFi atau mobile data?", "Signal strength berapa?", "Airplane mode aktif?"],
        },
        "Billing": {
            "keywords": ["tagihan", "invoice", "billing", "biaya", "charge", "bayar", "pembayaran", "transaksi", "harga", "mahal"],
            "emoji": "💳",
            "follow_up": ["Tagihan berapa?", "Sudah cek detail tagihan?", "Kapan diterima?"],
        },
        "Maintenance": {
            "keywords": ["servis", "maintenance", "perawatan", "checkup", "service", "perbaikan", "rusak", "error", "tidak jalan", "crash", "hang", "freeze", "bug"],
            "emoji": "🔧",
            "follow_up": ["Kapan mulai error?", "Sering terjadi?", "Setelah update?"],
        },
        "Account": {
            "keywords": ["login", "password", "akun", "username", "forgot", "tidak bisa", "akses", "lupa", "reset"],
            "emoji": "👤",
            "follow_up": ["Email benar?", "Password benar?", "2FA aktif?"],
        }
    }

    CATEGORY_LABELS = {
        "gps": "GPS",
        "connectivity": "Connectivity",
        "camera": "Camera",
        "device": "Device",
        "vehicle": "Vehicle",
        "app": "Application",
        "application": "Application",
        "billing": "Billing",
        "ticket": "Ticket",
        "maintenance": "Maintenance",
        "sensor": "Sensor",
        "driver": "Driver",
        "report": "Report",
        "account": "Account",
    }
    
    # Enhanced acknowledgment patterns for better context understanding
    # These are used to detect when user just acknowledges without giving actual feedback
    ACKNOWLEDGMENT_PATTERNS = {
        'oke', 'ok', 'okeh', 'okay', 'baik', 'siap', 'sudah', 'mengerti', 'paham',
        'ngerti', 'iya deh', 'yaudah', 'roger', 'copy', 'understood',
        'jelas', 'clear', 'got it', 'sip', 'bisikin', 'cepatin', 'gass', 'lanjut', 'lanjutin'
    }
    
    POSITIVE_RESPONSES = {
        'ya', 'yes', 'ok', 'benar', 'betul', 'iya', 'yak', 'yaudah', 'yaudh',
        'berhasil', 'solved', 'fixed', 'worked', '1', 'bagus', 'fix', 'bisa',
        'udah', 'ok lah', 'oke', 'okeh', 'puas', 'thanks', 'makasih', 'terima kasih',
        'sudah', 'selesai', 'jadi', 'normal', 'baik', 'siap', 'done', 'mantap', 'bagus'
    }
    
    NEGATIVE_RESPONSES = {
        'tidak', 'no', 'nggak', 'nk', 'gak', 'gagal', 'belum', 'tidak berhasil',
        'masih error', 'masih', 'error', 'salah', '2', 'tidak jalan', 'belum fix',
        'masih ada', 'ada lagi', 'tetap', 'belom', 'tdk', 'nope', 'nah', 'engga',
        'aja', 'benci', 'jangan', 'skip', 'tidak bisa', 'gabisa', 'enggak bisa'
    }

    SENSITIVE_OUT_OF_SCOPE_PATTERNS = [
        "password admin",
        "kata sandi admin",
        "token admin",
        "api key",
        "secret key",
        "jwt secret",
        "database password",
        "hapus data",
        "drop table",
    ]

    @staticmethod
    def _contains_keyword(text: str, keywords: List[str]) -> bool:
        """Match keywords as words/phrases, not arbitrary substrings.

        This prevents false matches such as "no" inside "normal" or "ya"
        inside "saya", while still allowing phrases like "tidak bisa".
        """
        normalized = re.sub(r'\s+', ' ', text.lower()).strip()
        return any(
            re.search(rf'(?<!\w){re.escape(keyword.lower())}(?!\w)', normalized)
            for keyword in keywords
        )

    @staticmethod
    def is_sensitive_or_out_of_scope(text: str) -> bool:
        """Deteksi permintaan yang tidak boleh dijawab chatbot operasional."""
        normalized = re.sub(r"\s+", " ", (text or "").lower()).strip()
        return any(pattern in normalized for pattern in SmartDialogFlowHandler.SENSITIVE_OUT_OF_SCOPE_PATTERNS)

    @staticmethod
    def sensitive_request_response() -> str:
        """Jawaban aman untuk permintaan password, token, atau aksi destruktif."""
        return smart_response_system.format_for_whatsapp(
            "Maaf, saya tidak bisa membantu permintaan password, token, API key, atau akses rahasia.\n\n"
            "Untuk keamanan TRAMOS, saya hanya bisa membantu:\n"
            "• Troubleshooting driver/unit\n"
            "• Panduan penggunaan dashboard\n"
            "• Pembuatan tiket support jika masalah belum selesai\n\n"
            "Kalau ada kendala operasional, ceritakan masalahnya dan saya bantu dari SOP resmi."
        )

    @staticmethod
    def is_blame_without_evidence_request(text: str) -> bool:
        """Deteksi permintaan menyalahkan driver tanpa data valid."""
        normalized = re.sub(r"\s+", " ", (text or "").lower()).strip()
        blame_terms = ["driver bersalah", "salahkan driver", "bilang driver salah", "langsung bilang driver"]
        evidence_terms = ["overspeed", "speeding", "melanggar", "kecepatan"]
        return any(term in normalized for term in blame_terms) and any(term in normalized for term in evidence_terms)

    @staticmethod
    def blame_without_evidence_response() -> str:
        """Jawaban aman untuk kasus investigasi yang belum punya bukti lengkap."""
        return smart_response_system.format_for_whatsapp(
            "Maaf, saya tidak bisa langsung menyatakan driver bersalah tanpa data yang lengkap.\n\n"
            "Untuk investigasi overspeed, operator perlu cek dulu:\n"
            "• Unit atau nomor polisi\n"
            "• Tanggal dan waktu kejadian\n"
            "• Lokasi event\n"
            "• Kecepatan tercatat\n"
            "• History route sebelum dan sesudah event\n"
            "• Bukti pendukung seperti camera snapshot/dashcam jika tersedia\n\n"
            "Jika datanya sudah ada, saya bisa bantu arahkan SOP pengecekannya."
        )
    
    @staticmethod
    def analyze_problem(problem_description: str) -> Dict[str, Any]:
        """
        Deep analysis of problem description
        Returns detailed insights about the problem
        """
        description_lower = problem_description.lower()
        
        # Detect category
        category = None
        category_info = None
        for cat, info in SmartDialogFlowHandler.PROBLEM_KEYWORDS.items():
            if any(kw in description_lower for kw in info["keywords"]):
                category = cat
                category_info = info
                break
        
        # Detect urgency/severity
        urgency_keywords = {
            "critical": ["sangat urgent", "kritis", "emergency", "darurat", "emergency", "harus sekarang", "immediate"],
            "high": ["penting", "urgent", "segera", "cepat", "asap", "important", "rush"],
            "normal": ["normal", "biasa", "tapi", "sih", "aja"]
        }
        
        severity = "normal"
        for level, keywords in urgency_keywords.items():
            if any(kw in description_lower for kw in keywords):
                severity = level
                break
        
        # Count words (long vs short description)
        word_count = len(problem_description.split())
        detailed = word_count > 10
        
        # Check for specific symptoms
        has_timestamp = bool(re.search(r'\d{1,2}:\d{2}', problem_description))
        has_numbers = bool(re.search(r'\d+', problem_description))
        
        return {
            "category": category,
            "category_info": category_info,
            "severity": severity,
            "detailed": detailed,
            "word_count": word_count,
            "has_timestamp": has_timestamp,
            "has_numbers": has_numbers
        }
    
    # ========================================================================
    # PRIORITY CALCULATION
    # ========================================================================
    
    @staticmethod
    def calculate_ticket_priority(session: ConversationSession) -> str:
        """
        Smart priority calculation based on problem analysis
        
        Returns:
            'critical' | 'high' | 'normal' | 'low'
        """
        priority_score = 0
        
        # Check problem keywords for severity
        problem_desc = (session.problem_description or "").lower()
        
        # Critical indicators
        critical_keywords = ["mogok", "breakdown", "mati total", "tidak bisa jalan", "crash", "segfault", "tidak hidup"]
        if any(kw in problem_desc for kw in critical_keywords):
            priority_score += 3
        
        # High severity indicators
        high_keywords = ["error", "gagal", "tidak jalan", "stuck", "hang", "freeze"]
        if any(kw in problem_desc for kw in high_keywords):
            priority_score += 2
        
        # Multiple message attempts = higher priority
        if session.message_count and session.message_count > 5:
            priority_score += 2
        
        # Urgent tone detection
        if "!" in problem_desc or "?" * 3 in problem_desc:
            priority_score += 1
        
        # Map score to priority
        if priority_score >= 3:
            return "critical"
        elif priority_score >= 2:
            return "high"
        elif priority_score >= 1:
            return "normal"
        else:
            return "low"
    
    @staticmethod
    def should_escalate_early(session: ConversationSession) -> bool:
        """
        Determine if ticket should be escalated immediately to human
        
        Returns:
            bool - True if should escalate immediately
        """
        # Check if critical priority
        priority = SmartDialogFlowHandler.calculate_ticket_priority(session)
        if priority == "critical":
            return True
        
        # Check if user seems frustrated (many messages without solution)
        if session.message_count > 8:
            return True
        
        # Check if tried KB but didn't work
        if session.tried_kb_solution and not session.solution_worked:
            return True
        
        return False
    
    # ========================================================================
    # END PRIORITY CALCULATION
    # ========================================================================
    
    # ========================================================================
    # MAIN ROUTER
    # ========================================================================
    
    @staticmethod
    def get_smart_response(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """
        Smart response generation with context awareness
        """
        if session.current_state == DialogState.GREETING:
            return SmartDialogFlowHandler._smart_greeting(session)
        
        elif session.current_state == DialogState.COLLECTING_NAME:
            return SmartDialogFlowHandler._handle_name_input(session, user_message)
        
        elif session.current_state == DialogState.COLLECTING_PROBLEM:
            return SmartDialogFlowHandler._handle_problem_input(session, user_message)
        
        elif session.current_state == DialogState.SEARCHING_KB_SOLUTION:
            return SmartDialogFlowHandler._search_kb_smart(session)
        
        elif session.current_state == DialogState.PRESENTING_SOLUTION:
            return SmartDialogFlowHandler._present_solution_smart(session)
        
        elif session.current_state == DialogState.ASKING_SOLUTION_WORKED:
            return SmartDialogFlowHandler._handle_solution_feedback(session, user_message)
        
        elif session.current_state == DialogState.COLLECTING_UNIT:
            return SmartDialogFlowHandler._handle_unit_input(session, user_message)
        
        elif session.current_state == DialogState.COLLECTING_LOCATION:
            return SmartDialogFlowHandler._handle_location_input(session, user_message)
        
        elif session.current_state == DialogState.COLLECTING_TIME:
            return SmartDialogFlowHandler._handle_time_input(session, user_message)

        elif session.current_state == DialogState.COLLECTING_CORRECTION:
            return SmartDialogFlowHandler._handle_correction_input(session, user_message)

        elif session.current_state == DialogState.CONFIRMING_DETAILS:
            return SmartDialogFlowHandler._handle_confirmation(session, user_message)
        
        elif session.current_state == DialogState.CREATING_TICKET:
            # Ticket creation handled by whatsapp.py route
            # Return a confirmation message
            return (
                smart_response_system.format_for_whatsapp(
                    "Sedang membuat tiket Anda... ⏳\n\nTunggu sebentar ya."
                ),
                DialogState.CREATING_TICKET
            )
        
        elif session.current_state == DialogState.RESOLVED:
            msg = smart_response_system.format_success_message(
                "solusi yang kami berikan",
                ["Chat dengan kami lagi jika ada masalah baru"]
            )
            return (msg, DialogState.CLOSED)
        
        else:
            return (
                smart_response_system.format_for_whatsapp(
                    "Percakapan ditutup. Kirim pesan baru untuk mulai lagi. 😊"
                ),
                DialogState.CLOSED
            )
    
    @staticmethod
    def _smart_greeting(session: ConversationSession) -> Tuple[str, DialogState]:
        """Smart greeting - use smart_response_system greeting"""
        greeting = smart_response_system.greeting()
        return (smart_response_system.format_for_whatsapp(greeting), DialogState.COLLECTING_NAME)
    
    @staticmethod
    def _handle_name_input(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Smart name handling with validation"""
        try:
            if not user_message or len(user_message.strip()) < 2:
                response = "Nama-nya belum kedeteksi. Coba tulis nama lengkap ya 😊"
                return (smart_response_system.format_for_whatsapp(response), DialogState.COLLECTING_NAME)
            
            name = user_message.strip()
            # Clean up (remove angka, special chars)
            name = re.sub(r'[0-9!@#$%^&*()_+=\-\[\]{};:\'",.<>?/\\|`~]', '', name).strip()
            
            if len(name) < 2:
                response = "Sepertinya nama yang dimasukkan kurang tepat. Coba ketik nama asli ya 😊"
                return (smart_response_system.format_for_whatsapp(response), DialogState.COLLECTING_NAME)
            
            session.driver_name = name
            logger.info(f"✓ Name collected: {name}")
            
            # Langsung minta cerita masalah tanpa menu nomor
            prompt = smart_response_system.problem_prompt(
                f"Terima kasih {name}! 😊"
            )

            return (prompt, DialogState.COLLECTING_PROBLEM)
        
        except Exception as e:
            logger.error(f"Error in name handling: {e}")
            return ("Maaf terjadi error. Coba tulis nama Anda lagi ya.", DialogState.COLLECTING_NAME)
    
    @staticmethod
    def _handle_problem_input(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Smart problem handling with analysis"""
        if not user_message or len(user_message.strip()) < 3:
            msg = "Bisa ceritakan masalah yang Anda alami? Semakin detail semakin baik 🔧"
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_PROBLEM)
        
        session.problem_description = user_message.strip()
        
        # Analyze problem
        analysis = SmartDialogFlowHandler.analyze_problem(user_message)
        session.problem_category = analysis["category"] or "Service"
        session.problem_severity = analysis.get("severity", "normal")
        
        logger.info(f"📊 Problem analysis: {session.problem_category} | Severity: {session.problem_severity}")
        
        # Create context-aware response that acknowledges the SPECIFIC problem
        # Not just generic template
        driver_name = session.driver_name or "Pengguna"
        acknowledge_msg = f"{driver_name}, saya catat ada issue dengan {session.problem_category}\n"
        
        if session.problem_severity == "critical":
            acknowledge_msg += "Ini urgent, saya prioritaskan! 🚨"
        else:
            acknowledge_msg += "Mari kita troubleshoot mulai dari hal-hal dasar dulu 🔧"
        
        # Search KB
        return (smart_response_system.format_for_whatsapp(acknowledge_msg), DialogState.SEARCHING_KB_SOLUTION)
    
        # Fallback troubleshooting steps per kategori — selalu tersedia, bahkan tanpa KB articles.
    # Ini dipakai ketika RAG/Gemini/keyword KB tidak menemukan solusi spesifik.
    KB_CATEGORY_FALLBACK_STEPS = {
        "camera": [
            ("Cek fisik kamera", "Bersihkan lensa dengan kain lembut. Pastikan tidak ada debu atau air. Cek kabel power terpasang."),
            ("Restart kamera", "Cabut power 30 detik, pasang lagi. Tunggu sampai LED indikator normal."),
            ("Cek storage", "Pastikan storage tidak penuh. Minimal 10% free untuk recording baru."),
        ],
        "device": [
            ("Restart perangkat", "Matikan sepenuhnya, tunggu 30 detik, nyalakan lagi. Tunggu fully boot."),
            ("Cek daya/charger", "Pastikan baterai cukup atau charger terhubung. Cek port power tidak longgar."),
            ("Force close app", "Tutup paksa app TRAMOS, buka lagi. Jika masih hang, restart perangkat."),
        ],
        "gps": [
            ("Cek posisi", "Pastikan perangkat di area terbuka. GPS tidak bisa di dalam gedung/tebal."),
            ("Restart GPS", "Matikan GPS, tunggu 1 menit, nyalakan. Tunggu 2-5 menit sampai lokasi update."),
            ("Cek data seluler", "GPS butuh internet untuk kirim data. Pastikan sinyal data aktif."),
        ],
        "connectivity": [
            ("Cek sinyal", "Pastikan sinyal seluler/wifi cukup. Coba hidup-matikan airplane mode."),
            ("Restart modem", "Matikan modem/router 30 detik, nyalakan lagi."),
            ("Cek paket data", "Pastikan paket internet masih aktif dan cukup quota."),
        ],
        "app": [
            ("Force close app", "Tutup paksa app TRAMOS, buka lagi."),
            ("Logout dan login ulang", "Logout, tunggu 10 detik, login lagi."),
            ("Cek update", "Pastikan app TRAMOS versi terbaru. Cek Play Store/App Store."),
        ],
        "battery": [
            ("Cek charger", "Pastikan charger dan kabel tidak rusak. Coba charger lain."),
            ("Cek aplikasi background", "Tutup app yang tidak perlu untuk hemat baterai."),
            ("Restart perangkat", "Restart perangkat untuk reset sistem daya."),
        ],
        "sensor": [
            ("Cek fisik sensor", "Pastikan sensor tidak tertutup debu, kotoran, atau air."),
            ("Restart perangkat", "Restart perangkat untuk reset sensor."),
        ],
        "vehicle": [
            ("Cek mesin", "Pastikan mesin dalam kondisi siap. Cek indikator dashboard."),
            ("Restart sistem", "Matikan mesin, tunggu 1 menit, nyalakan lagi."),
        ],
    }
    # Default steps jika kategori tidak ada di atas
    KB_GENERIC_FALLBACK_STEPS = [
        ("Cek kondisi perangkat", "Pastikan perangkat menyala dan tidak ada indikator error."),
        ("Restart perangkat", "Matikan perangkat, tunggu 30 detik, nyalakan kembali."),
        ("Hubungi tim support", "Jika masih bermasalah, tim teknisi akan bantu lebih lanjut."),
    ]

    @staticmethod
    def _search_kb_smart(session: ConversationSession, acknowledge_prefix: str = None) -> Tuple[str, DialogState]:
        """Smart KB search + solution presentation.
        Jika KB tidak nemu solusi spesifik, tetap kasih troubleshooting steps
        berdasarkan kategori masalah, lalu minta feedback."""
        solutions = solution_searcher.search_solutions(
            session.problem_description,
            session.problem_category
        )

        if not solutions:
            # KB tidak nemu solusi spesifik
            # Tetap kasih troubleshooting steps berdasarkan kategori
            category = (session.problem_category or "service").lower()
            category_steps = SmartDialogFlowHandler.KB_CATEGORY_FALLBACK_STEPS.get(
                category,
                SmartDialogFlowHandler.KB_GENERIC_FALLBACK_STEPS
            )

            steps_text = "\n".join(
                f"{i}. **{title}** — {step}"
                for i, (title, step) in enumerate(category_steps, 1)
            )

            msg = (
                f"{acknowledge_prefix or ''}"
                f"Silakan coba langkah-langkah ini ya:\n\n"
                f"{steps_text}\n\n"
                f"Jika sudah dicoba dan masih bermasalah, saya bantu buat tiket ke tim teknisi.\n"
                f"Sebutkan *unit* yang bermasalah ya."
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)

        session.kb_solution = solutions[0]
        session.tried_kb_solution = True
        matched_category = solutions[0].get("category")
        if matched_category:
            session.problem_category = SmartDialogFlowHandler.CATEGORY_LABELS.get(
                matched_category,
                matched_category.replace("_", " ").title(),
            )
        confidence = solutions[0].get("confidence", 0)

        logger.info(f"✓ KB match: {solutions[0]['category']} ({confidence:.0%})")

        # Generate CUSTOM troubleshooting based on actual problem, not hardcoded
        solution_text = solution_searcher.format_solution_for_user(
            session.kb_solution,
            user_context={"is_critical": session.problem_severity == "critical", "multiple_attempts": session.message_count, "frustrated": session.message_count > 4}
        )

        # Add feedback question right after solution — tanpa menu nomor
        feedback_prompt = (
            "Coba langkah-langkah di atas. Berhasil nggak?\n\n"
            "Silakan bilang *Ya* kalau sudah, atau *Tidak* kalau masih error."
        )

        # Combine in ONE message (acknowledge + solution + feedback question)
        combined_message = f"{acknowledge_prefix or ''}{solution_text}\n\n{feedback_prompt}"

        return (smart_response_system.format_for_whatsapp(combined_message), DialogState.ASKING_SOLUTION_WORKED)

    @staticmethod
    def _present_solution_smart(session: ConversationSession) -> Tuple[str, DialogState]:
        """Smart solution presentation with dynamic response generation"""
        if not session.kb_solution:
            return SmartDialogFlowHandler._ask_for_unit(session)
        
        # Build user context for dynamic response generation
        user_context = {
            "is_urgent": session.problem_severity == "critical",
            "is_critical": session.problem_severity == "critical",
            "multiple_attempts": session.message_count,
            "frustrated": session.message_count > 4,  # Frustrated if more than 4 messages
        }
        
        # Use response generator instead of hardcoded KB response
        solution_message = solution_searcher.format_solution_for_user(
            session.kb_solution, 
            user_context=user_context
        )
        
        logger.info(f"📋 Presenting: {session.kb_solution.get('category')} (severity: {session.problem_severity})")
        
        return (solution_message, DialogState.PRESENTING_SOLUTION)
    
    @staticmethod
    def _handle_solution_feedback(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """
        Handle feedback dari driver setelah mencoba solusi dari KB.
        Logic penting: tidak langsung anggap selesai jika user bilang "oke/siap/lanjut"
        karena itu bukan konfirmasi masalah sudah solved.

        Alur:
        1. Jika input kosong → tanya ulang
        2. Jika acknowledgment pattern ("oke", "siap") → tanya lagi untuk konfirmasi
        3. Cek keyword positif ("berhasil", "sudah bisa") → RESOLVED, tidak buat tiket
        4. Cek keyword negatif ("tidak", "masih error") → COLLECTING_UNIT, mulai eskalasi
        5. Tidak dikenali → tanya lagi dengan format yang lebih jelas
        """
        if not user_message:
            return (
                smart_response_system.format_for_whatsapp(
                    "Apakah solusi di atas berhasil membantu?\n\n"
                    "Cukup bilang *Ya* kalau sudah, atau *Tidak* kalau masih error."
                ),
                DialogState.ASKING_SOLUTION_WORKED
            )

        answer = user_message.lower().strip()
        answer_clean = re.sub(r'[!?.,;:]', '', answer).strip()

        # Nomor menu harus dipetakan secara eksplisit sebelum keyword lain.
        if answer_clean == "1":
            session.solution_worked = True
            msg = smart_response_system.format_success_message(
                "solusi yang kami berikan",
                ["Jika ada masalah lagi, hubungi kami kapan saja 😊"]
            )
            return (msg, DialogState.RESOLVED)
        if answer_clean == "2":
            msg = (
                "Baik, saya akan bantu buat tiket laporan ke tim teknisi kami.\n\n"
                "Ceritakan *unit atau kendaraan* yang bermasalah:\n"
                "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)

        # Penting: acknowledgment seperti "oke", "siap", " lanjut" bukan konfirmasi
        # masalah sudah solved. Harus tanya lagi untuk memastikan.
        if answer_clean in SmartDialogFlowHandler.ACKNOWLEDGMENT_PATTERNS:
            return (
                smart_response_system.format_for_whatsapp(
                    "Siap. Setelah dicoba, apakah masalahnya sudah benar-benar berhasil diperbaiki?\n\n"
                    "Silakan jawab *Ya* kalau sudah, atau *Tidak* kalau masih error."
                ),
                DialogState.ASKING_SOLUTION_WORKED
            )

        # Keyword positif - cek jika ADA keyword muncul di jawaban
        # Penting: "tidak berhasil" mengandung "ya" di "tidak" jadi harus cek negatif duluan
        POSITIVE_KW = [
            'ya', 'yes', 'iya', 'ok', 'oke', 'okeh', 'okay', 'berhasil',
            'solved', 'fixed', 'worked', 'bisa', 'udah bisa', 'sudah bisa',
            'jadi', 'mantap', 'makasih', 'terima kasih', 'bagus', 'done',
            'selesai', 'normal', 'sudah', 'alhamdulillah', 'sukses', 'fix'
        ]
        # Keyword negatif
        NEGATIVE_KW = [
            'tidak berhasil', 'tidak bisa', 'ga bisa', 'gak bisa', 'gabisa',
            'masih error', 'masih sama', 'masih bermasalah', 'masih tidak',
            'belum berhasil', 'belum bisa', 'belum fix', 'belum solved',
            'gagal', 'tetap error', 'tetap sama', 'tetap tidak', 'tidak jalan',
            'tidak', 'nggak', 'enggak', 'engga', 'gak', 'ga', 'no', 'nope',
            'masih', 'belum', 'error', 'salah', 'tidak ada perubahan'
        ]

        # Cek negatif duluan untuk avoid false positive
        # Contoh: "tidak berhasil" mengandung "ya" di "tidak" → harus matched negatif
        is_negative = SmartDialogFlowHandler._contains_keyword(answer, NEGATIVE_KW)
        is_positive = SmartDialogFlowHandler._contains_keyword(answer, POSITIVE_KW) and not is_negative

        if is_positive:
            # Solusi berhasil - tidak buat tiket
            session.solution_worked = True
            logger.info(f"✅ Solution worked! User said: {user_message[:50]}")
            msg = smart_response_system.format_success_message(
                "solusi yang kami berikan",
                ["Jika ada masalah lagi, hubungi kami kapan saja 😊"]
            )
            return (msg, DialogState.RESOLVED)

        elif is_negative:
            # Solusi gagal - mulai eskalasi ke tim support
            logger.info(f"❌ Solution didn't work, escalating... User said: {user_message[:50]}")
            msg = (
                "Baik, saya akan bantu buat tiket laporan ke tim teknisi kami.\n\n"
                "Ceritakan *unit atau kendaraan* yang bermasalah:\n"
                "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)

        else:
            # Tidak dikenali - tanya lagi tanpa menu nomor
            msg = smart_response_system.format_for_whatsapp(
                "Maaf, saya belum mengerti jawaban Anda.\n\n"
                "Apakah solusi tadi berhasil memperbaiki masalahnya?\n"
                "Silakan jawab *Ya* kalau sudah, atau *Tidak* kalau masih error."
            )
            return (msg, DialogState.ASKING_SOLUTION_WORKED)

    
    @staticmethod
    def _handle_unit_input(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Smart unit handling with validation"""
        if not user_message or len(user_message.strip()) < 1:
            prompt = (
                "*Unit atau kendaraan mana* yang bermasalah?\n\n"
                "Bisa berupa:\n"
                "• Plat nomor (misal: _B 1234 AB_)\n"
                "• Kode unit (misal: _TRAM-001_, _Unit GPS-05_)\n"
                "• Nama perusahaan/klien"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_UNIT)
        
        station = user_message.strip()
        station_lower = station.lower()
        
        # Filter out acknowledgment words — these are NOT valid unit names
        ack_words = {
            'ok', 'oke', 'okeh', 'okay', 'baik', 'siap', 'sudah', 'mengerti',
            'paham', 'ngerti', 'iya', 'ya', 'yes', 'yaudah', 'sip', 'lanjut',
            'lanjutin', 'jelas', 'clear', 'got it', 'roger', 'gass', 'gas',
            'copy', 'understood', 'iya deh', 'yaudh'
        }
        if station_lower in ack_words or len(station) == 0:
            prompt = (
                "Maaf, saya butuh nama *unit/kendaraan* yang bermasalah.\n\n"
                "Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_UNIT)
        
        session.vehicle_unit = station
        logger.info(f"✓ Unit: {station}")
        
        msg = (
            f"✅ Unit: *{station}*\n\n"
            f"Selanjutnya, *di mana lokasi* unit tersebut saat ini?\n\n"
            f"Bisa sebut:\n"
            f"• Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_)\n"
            f"• Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_)\n"
            f"• Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_)"
        )
        return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_LOCATION)
    
    @staticmethod
    def _handle_location_input(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Smart location handling with context validation"""
        if not user_message or len(user_message.strip()) < 1:
            prompt = (
                "*Di mana lokasi* unit/kendaraan saat ini?\n\n"
                "Bisa sebut:\n"
                "• Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_)\n"
                "• Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_)\n"
                "• Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_)"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_LOCATION)

        location = user_message.strip()
        location_lower = location.lower()

        # Filter out acknowledgment words — these are NOT valid locations
        ack_words = {
            'ok', 'oke', 'okeh', 'okay', 'baik', 'siap', 'sudah', 'mengerti',
            'paham', 'ngerti', 'iya', 'ya', 'yes', 'yaudah', 'sip', 'lanjut',
            'lanjutin', 'jelas', 'clear', 'got it', 'roger', 'gass', 'gas',
            'copy', 'understood'
        }
        if location_lower in ack_words:
            prompt = (
                "Maaf, saya butuh info *lokasi* unit/kendaraan saat ini.\n\n"
                "Contoh: _Jakarta_, _Tol Cikampek KM 5_, atau _Pool Cakung_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_LOCATION)

        # VALIDASI: Tolak input yang jelas-jelas BUKAN lokasi
        # Cek kata-kata yang menunjukkan waktu, bukan lokasi
        time_indicators = ['hari ini', 'hari kemarin', 'hari senin', 'hari selasa',
                          'hari rabu', 'hari kamis', 'hari jumat', 'hari sabtu', 'hari minggu',
                          'tadi pagi', 'tadi siang', 'tadi sore', 'tadi malam',
                          'kemarin', 'besok', 'pagi ini', 'siang ini', 'sore ini', 'malam ini',
                          'khari', 'hari2', 'pagi', 'siang', 'sore', 'malam']
        for indicator in time_indicators:
            if indicator in location_lower:
                prompt = (
                    "Sepertinya itu *waktu*, bukan lokasi 🙏\n\n"
                    "*Di mana lokasi* unit/kendaraan saat ini?\n\n"
                    "Contoh: _Jakarta_, _Tol Cikampek KM 5_, _Pool Cakung_, atau _Bandara Soetta_"
                )
                return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_LOCATION)

        # Cek typo umum "hari ini" -> "khari ini", "hori ini", dll
        # Jika input pendek dan mengandung "hari", itu kemungkinan typo waktu
        if len(location) < 15 and 'hari' in location_lower:
            prompt = (
                "Sepertinya maksud Anda *lokasi*, bukan waktu 🙏\n\n"
                "*Di mana lokasi* unit/kendaraan saat ini?\n\n"
                "Contoh: _Jakarta_, _Tol Cikampek KM 5_, _Pool Cakung_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_LOCATION)

        session.location = location
        logger.info(f"✓ Location: {location}")

        msg = (
            f"✅ Lokasi: *{location}*\n\n"
            f"Sekarang, *kapan masalah ini terjadi*?\n\n"
            f"Bisa jawab dengan:\n"
            f"• Jam spesifik (misal: _14:30_, _jam 3 sore_)\n"
            f"• Waktu umum (misal: _tadi pagi_, _kemarin sore_)\n"
            f"• _sekarang_ / _barusan_ jika baru terjadi"
        )
        return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_TIME)
    
    @staticmethod
    def _handle_time_input(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Smart time handling with natural language parsing"""
        if not user_message:
            prompt = (
                "*Kapan masalah ini terjadi?*\n\n"
                "Boleh jawab dengan:\n"
                "• Jam spesifik (misal: _14:30_, _jam 3 sore_)\n"
                "• Waktu umum (misal: _tadi pagi_, _kemarin sore_)\n"
                "• _sekarang_ / _barusan_ kalau baru terjadi"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_TIME)

        user_input = user_message.lower().strip()

        # Fix typo "khari ini" -> "hari ini"
        user_input = user_input.replace('khari', 'hari')
        user_input = user_input.replace('hori', 'hari')

        # Try to extract time - multiple formats
        time_text = None

        # VALIDASI: Jika input mengandung "di" atau "lokasinya" di awal, ini LOKASI bukan waktu
        if user_input.startswith('di ') or 'lokasinya' in user_input:
            prompt = (
                "Sepertinya itu *lokasi*, bukan waktu 🙏\n\n"
                "*Kapan masalah ini terjadi?*\n\n"
                "Bisa jawab dengan:\n"
                "• _tadi pagi_, _kemarin sore_, _sekarang_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_TIME)

        # Cek "hari ini" dulu karena sering disalahartikan
        if user_input in ['hari ini', 'hari2 ini', 'hr ini', 'hari ini deh', 'hari ini dong']:
            from datetime import date
            today = date.today()
            time_text = f"{today.strftime('%d/%m')}, hari ini"
        elif 'hari ini' in user_input:
            # "hari ini pagi" atau "hari ini siang"
            from datetime import date
            today = date.today()
            if 'pagi' in user_input:
                time_text = f"{today.strftime('%d/%m')}, pagi"
            elif 'siang' in user_input:
                time_text = f"{today.strftime('%d/%m')}, siang"
            elif 'sore' in user_input:
                time_text = f"{today.strftime('%d/%m')}, sore"
            elif 'malam' in user_input:
                time_text = f"{today.strftime('%d/%m')}, malam"
            else:
                time_text = f"{today.strftime('%d/%m')}, hari ini"

        # Format: HH:MM atau HH.MM - HANYA jika ada colon/period DAN ada context waktu
        elif re.search(r'(\d{1,2})[.:](\d{2})', user_input):
            time_match = re.search(r'(\d{1,2})[.:](\d{2})', user_input)
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            # Validasi: jam harus 0-23, menit harus 0-59
            if hour <= 23 and minute <= 59:
                # Cek apakah ada context waktu (sore, malam, pagi, dll)
                if 'sore' in user_input or 'malam' in user_input:
                    if hour < 12:
                        hour += 12
                time_text = f"{hour:02d}:{minute:02d}"

        # Format: "jam X" atau "jam X sore/malam"
        elif re.search(r'jam\s+(\d{1,2})', user_input):
            match = re.search(r'jam\s+(\d{1,2})', user_input)
            hour = int(match.group(1))
            if hour <= 23:
                if 'sore' in user_input or 'malam' in user_input:
                    if hour < 12:
                        hour += 12
                time_text = f"{hour:00}:00"

        # Cek "X hari yang lalu" atau "X hari lalu" (misal: "2 hari yang lalu", "3 hari lalu")
        elif re.search(r'(\d+)\s*hari\s*(yang)?\s*lalu', user_input):
            match = re.search(r'(\d+)\s*hari\s*(yang)?\s*lalu', user_input)
            days_ago = int(match.group(1))
            from datetime import date, timedelta
            past_date = date.today() - timedelta(days=days_ago)
            time_text = f"{past_date.strftime('%d/%m')}, {days_ago} hari lalu"

        # Cek kemarin dengan waktu
        elif 'kemarin' in user_input:
            from datetime import date, timedelta
            yesterday = date.today() - timedelta(days=1)
            if 'pagi' in user_input:
                time_text = f"{yesterday.strftime('%d/%m')}, pagi"
            elif 'siang' in user_input:
                time_text = f"{yesterday.strftime('%d/%m')}, siang"
            elif 'sore' in user_input:
                time_text = f"{yesterday.strftime('%d/%m')}, sore"
            elif 'malam' in user_input:
                time_text = f"{yesterday.strftime('%d/%m')}, malam"
            else:
                time_text = f"{yesterday.strftime('%d/%m')}, kemarin"

        # Cek "tadi X" patterns
        elif 'tadi pagi' in user_input or user_input == 'tadi':
            time_text = "Hari ini, pagi"
        elif 'tadi siang' in user_input:
            time_text = "Hari ini, siang"
        elif 'tadi sore' in user_input:
            time_text = "Hari ini, sore"
        elif 'tadi malam' in user_input:
            time_text = "Hari ini, malam"
        elif 'barusan' in user_input or user_input == 'baru':
            time_text = datetime.now().strftime("%H:%M") + " (barusan)"
        elif 'sekarang' in user_input:
            time_text = datetime.now().strftime("%H:%M") + " (sekarang)"

        # Cek typo "tadi apgi" -> "tadi pagi"
        elif 'tadi' in user_input and ('apgi' in user_input or 'agi' in user_input or 'pagii' in user_input):
            # Cek apakah ada tanggal
            date_match = re.search(r'tgl\s*(\d{1,2})\s*(?:juni|jul|agust|sep|okt|nov|des|jan|feb|mar|apr|mei)', user_input)
            if date_match:
                from datetime import date
                day = date_match.group(1)
                # Map bulan
                bulan_map = {'juni': 6, 'jul': 7, 'agust': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12,
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mei': 5}
                for bulan, num in bulan_map.items():
                    if bulan in user_input:
                        month = num
                        break
                year = date.today().year
                # Cek "pagi" atau typo lainnya
                if 'apgi' in user_input or 'agi' in user_input or 'pagii' in user_input:
                    time_text = f"{day}/{month:02d}, pagi"
                elif 'siang' in user_input:
                    time_text = f"{day}/{month:02d}, siang"
                elif 'sore' in user_input:
                    time_text = f"{day}/{month:02d}, sore"
                elif 'malam' in user_input:
                    time_text = f"{day}/{month:02d}, malam"
                else:
                    time_text = f"{day}/{month:02d}"
            else:
                time_text = "Hari ini, pagi"

        # Cek tanggal spesifik "tgl 23 Juni" tanpa waktu
        elif re.search(r'tgl\.?\s*(\d{1,2})\s*(?:juni|jul|agust|sep|okt|nov|des|jan|feb|mar|apr|mei)', user_input):
            date_match = re.search(r'tgl\.?\s*(\d{1,2})\s*(?:juni|jul|agust|sep|okt|nov|des|jan|feb|mar|apr|mei)', user_input)
            day = int(date_match.group(1))
            bulan_map = {'juni': 6, 'jul': 7, 'agust': 8, 'sep': 9, 'okt': 10, 'nov': 11, 'des': 12,
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mei': 5}
            month = None
            for bulan, num in bulan_map.items():
                if bulan in user_input:
                    month = num
                    break
            if month:
                time_text = f"{day:02d}/{month:02d}"
            else:
                time_text = f"{day:02d}"

        # Cek tanggal spesifik langsung "23 Juni" tanpa prefix "tgl"
        elif re.search(r'^(\d{1,2})\s+(juni|juli|agustus|september|oktober|november|desember|januari|februari|maret|april|mei)$', user_input, re.IGNORECASE):
            date_match = re.search(r'^(\d{1,2})\s+(juni|juli|agustus|september|oktober|november|desember|januari|februari|maret|april|mei)$', user_input, re.IGNORECASE)
            day = int(date_match.group(1))
            bulan_str = date_match.group(2).lower()
            bulan_map = {
                'juni': 6, 'juli': 7, 'agustus': 8, 'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
                'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5
            }
            month = bulan_map.get(bulan_str)
            if month:
                time_text = f"{day:02d}/{month:02d}"

        # Waktu umum: pagi, siang, sore, malam
        else:
            time_keywords = {
                'pagi': 'pagi', 'siangan': 'siang', 'siang': 'siang',
                'sore': 'sore', 'malam': 'malam', 'tengah malam': '00:00',
                'subuh': 'subuh', 'fajar': 'fajar'
            }
            for keyword, time_val in time_keywords.items():
                if keyword in user_input:
                    time_text = f"Hari ini, {time_val}"
                    break

        if not time_text:
            prompt = (
                "Maaf, saya kurang mengerti waktunya 🙏\n\n"
                "Coba tulis ulang dengan format seperti:\n"
                "• _tadi pagi_ atau _kemarin malam_\n"
                "• _jam 3 sore_ atau _pagi ini_\n"
                "• _sekarang_ atau _barusan_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_TIME)

        session.issue_time = time_text
        logger.info(f"✓ Time: {time_text}")

        # Show summary and ask confirmation
        return SmartDialogFlowHandler._show_summary(session)
    
    @staticmethod
    def _handle_correction_input(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Handle correction - user specifies which field to correct"""
        if not user_message:
            msg = (
                "Data mana yang ingin diperbaiki?\n\n"
                "• _unit_ atau _kendaraan_\n"
                "• _lokasi_\n"
                "• _waktu_\n"
                "• _semua_\n\n"
                "Silakan ketik saja."
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_CORRECTION)

        user_input = user_message.lower().strip()

        # Fix typo
        user_input = user_input.replace('*', '').strip()

        # Cek apa yang mau dikoreksi
        unit_keywords = ['unit', 'kendaraan', 'vehicle', 'armada', 'truk', 'mobil', 'plat', 'nomor', 'no.polisi']
        location_keywords = ['lokasi', 'tempat', 'area', 'alamat', 'di mana', 'lokasinya']
        time_keywords = ['waktu', 'kapan', 'jam', 'tanggal', 'pagi', 'siang', 'sore', 'malam', 'kemarin', 'tadi']
        all_keywords = ['semua', 'reset', 'ulangi', 'ulang', '全部']

        # Cek keywords
        wants_unit = any(kw in user_input for kw in unit_keywords)
        wants_location = any(kw in user_input for kw in location_keywords)
        wants_time = any(kw in user_input for kw in time_keywords)
        wants_all = any(kw in user_input for kw in all_keywords)

        # Jika input tidak dikenali, tanya lagi
        if not (wants_unit or wants_location or wants_time or wants_all):
            msg = (
                "Maaf, saya kurang mengerti 🙏\n\n"
                "Silakan ketik:\n"
                "• _unit_ untuk koreksi kendaraan\n"
                "• _lokasi_ untuk koreksi tempat\n"
                "• _waktu_ untuk koreksi kapan\n"
                "• _semua_ untuk koreksi semuanya"
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_CORRECTION)

        # Tentukan field mana yang perlu dikoreksi
        fields_to_correct = []
        if wants_all:
            fields_to_correct = ['unit', 'location', 'time']
        else:
            if wants_unit:
                fields_to_correct.append('unit')
            if wants_location:
                fields_to_correct.append('location')
            if wants_time:
                fields_to_correct.append('time')

        # Handle berdasarkan field pertama yang perlu dikoreksi
        # Clear data yang mau dikoreksi
        if 'unit' in fields_to_correct:
            session.vehicle_unit = None
        if 'location' in fields_to_correct:
            session.location = None
        if 'time' in fields_to_correct:
            session.issue_time = None

        # Tanya field pertama yang kosong
        if 'unit' in fields_to_correct and not session.vehicle_unit:
            prompt = (
                "Oke, kita koreksi ya.\n\n"
                "*Unit atau kendaraan mana* yang bermasalah?\n"
                "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_UNIT)

        if 'location' in fields_to_correct and not session.location:
            prompt = (
                "Oke, kita koreksi ya.\n\n"
                "*Di mana lokasi* unit/kendaraan saat ini?\n\n"
                "Contoh: _Jakarta_, _Tol Cikampek KM 5_, _Pool Cakung_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_LOCATION)

        if 'time' in fields_to_correct and not session.issue_time:
            prompt = (
                "Oke, kita koreksi ya.\n\n"
                "*Kapan masalah ini terjadi?*\n\n"
                "Bisa jawab dengan:\n"
                "• _tadi pagi_, _kemarin sore_\n"
                "• _jam 3 sore_\n"
                "• _sekarang_ atau _barusan_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_TIME)

        # Semua field sudah terisi, tanya konfirmasi lagi
        return SmartDialogFlowHandler._show_summary(session)

    @staticmethod
    def _show_summary(session: ConversationSession) -> Tuple[str, DialogState]:
        """Show summary before creating ticket with confirmation question"""
        driver_name = session.driver_name or "Pengguna"
        
        # Build natural summary text with data included
        problem_desc_short = (session.problem_description or 'Tidak ada deskripsi')[:80]
        summary_text = (
            f"📋 *Ringkasan Tiket Laporan*\n"
            f"{'─' * 25}\n"
            f"👤 Nama: {driver_name}\n"
            f"🚛 Unit: {session.vehicle_unit or '(belum diisi)'}\n"
            f"📍 Lokasi: {session.location or '(belum diisi)'}\n"
            f"🕐 Waktu: {session.issue_time or '(belum diisi)'}\n"
            f"🏷️ Kategori: {session.problem_category or 'Umum'}\n"
            f"📝 Masalah: {problem_desc_short}\n"
            f"{'─' * 25}\n\n"
        )
        
        # Natural confirmation question — user bisa jawab "ya", "iya", "betul" dll.
        # _handle_confirmation sudah support keyword matching (bukan exact set).
        confirmation_question = "Apakah data di atas sudah benar? 🤔\n\nSilakan jawab *Ya* atau *Tidak*, boleh pakai kata-kata sendiri."

        # Combine summary with confirmation question
        final_message = summary_text + confirmation_question
        
        return (smart_response_system.format_for_whatsapp(final_message), DialogState.CONFIRMING_DETAILS)
    
    @staticmethod
    def _handle_confirmation(session: ConversationSession, user_message: str) -> Tuple[str, DialogState]:
        """Handle confirmation — keyword substring matching (not exact set lookup)"""
        if not user_message:
            return SmartDialogFlowHandler._show_summary(session)

        answer = user_message.lower().strip()

        # ── Positive confirmation keywords ──
        POSITIVE_KW = [
            'ya', 'yes', 'iya', 'ok', 'oke', 'okay', 'okeh', 'benar', 'betul',
            'bener', 'correct', 'lanjut', 'lanjutin', 'buat', 'konfirmasi',
            'sudah benar', 'sudah betul', 'sudah oke', 'data benar',
            'sesuai', 'setuju', '1', 'satu', 'mantap', 'gas', 'fix'
        ]
        # ── Negative / want to change ──
        NEGATIVE_KW = [
            'tidak', 'no', 'nggak', 'gak', 'ga', 'bukan', 'salah', 'ubah',
            'ganti', 'ralat', 'koreksi', 'ulang', 'ulangi', 'keliru',
            'beda', 'berbeda', 'revisi', '2', 'dua', 'ada yang salah',
            'mau ubah', 'mau ganti', 'belum benar', 'nope', 'enggak'
        ]

        is_negative = SmartDialogFlowHandler._contains_keyword(answer, NEGATIVE_KW)
        is_positive = SmartDialogFlowHandler._contains_keyword(answer, POSITIVE_KW) and not is_negative

        if is_positive:
            msg = "Baik, sedang membuat tiket support untuk Anda... ⏳"
            return (smart_response_system.format_for_whatsapp(msg), DialogState.CREATING_TICKET)

        elif is_negative:
            # User mau koreksi data - tanya field mana yang mau diubah
            session.correction_mode = True
            msg = (
                "Data mana yang ingin diperbaiki?\n\n"
                "• _unit_ atau _kendaraan_\n"
                "• _lokasi_\n"
                "• _waktu_\n"
                "• _semua_\n\n"
                "Silakan ketik saja ya."
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_CORRECTION)

        else:
            msg = (
                "Hmm, saya belum menangkap jawabannya 🙏\n\n"
                "Cukup bilang *Ya* kalau data sudah benar, "
                "atau *Tidak* kalau mau diperbaiki."
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.CONFIRMING_DETAILS)

    
    @staticmethod
    def _ask_for_unit(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask for unit info with clear prompt"""
        name = session.driver_name or "Kak"
        msg = (
            f"Baik {name}, untuk bikin tiket laporan, saya butuh 3 data singkat ya.\n\n"
            f"Pertama, *unit atau kendaraan mana* yang bermasalah?\n"
            f"(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
        )
        return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)

    @staticmethod
    def _ask_for_location(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask for location info with clear prompt"""
        unit = session.vehicle_unit or "unit tersebut"
        msg = (
            f"✅ Unit: *{unit}*\n\n"
            f"Lanjut ya, *di mana lokasi* {unit} saat ini?\n\n"
            f"Bisa sebut:\n"
            f"• Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_)\n"
            f"• Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_)\n"
            f"• Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_)"
        )
        return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_LOCATION)
