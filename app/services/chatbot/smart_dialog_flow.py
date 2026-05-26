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
        "Camera": {
            "keywords": ["kamera", "video", "rekam", "dashboard", "feed", "tampilan", "screen", "display", "cam", "video hitam", "tidak jelas"],
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
            
            # Ask for problem with clear options
            prompt = f"Terima kasih {name}! 😊\n\n"
            prompt += smart_response_system.format_question(
                "Ceritakan masalah yang Anda alami",
                options=["GPS tidak berfungsi", "Kamera error", "Baterai cepat habis", "Masalah koneksi"]
            )
            
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_PROBLEM)
        
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
    
    @staticmethod
    def _search_kb_smart(session: ConversationSession) -> Tuple[str, DialogState]:
        """Smart KB search + solution presentation - custom steps based on actual problem"""
        solutions = solution_searcher.search_solutions(
            session.problem_description,
            session.problem_category
        )
        
        if not solutions:
            logger.warning("No KB solution found")
            # No solution found - escalate with clear hardcoded message
            name = session.driver_name or "Kak"
            category = session.problem_category or "masalah Anda"
            msg = (
                f"{name}, sayangnya saya belum punya solusi otomatis untuk masalah *{category}* ini.\n\n"
                f"Tapi tenang, saya akan buatkan tiket laporan ke tim teknisi kami supaya bisa ditangani langsung. 💪\n\n"
                f"Saya butuh 3 informasi singkat:\n"
                f"1️⃣ Nama unit/kendaraan\n"
                f"2️⃣ Lokasi saat ini\n"
                f"3️⃣ Waktu kejadian\n\n"
                f"Pertama, *unit atau kendaraan mana* yang bermasalah?\n"
                f"(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
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
        custom_steps = f"""{session.driver_name}, ini solusi untuk masalah {session.problem_category} Anda:\n\n{solution_searcher.format_solution_for_user(
            session.kb_solution,
            user_context={"is_critical": session.problem_severity == "critical", "multiple_attempts": session.message_count, "frustrated": session.message_count > 4}
        )}"""
        
        # Add feedback question right after solution
        feedback_prompt = smart_response_system.format_question(
            "Coba langkah-langkah di atas. Berhasil nggak?",
            ["✅ Ya, berhasil!", "❌ Tidak, masih error"]
        )
        
        # Combine in ONE message (solution + feedback question)
        combined_message = f"{custom_steps}\n\n{feedback_prompt}"
        
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
        """Smart feedback handling — uses keyword search in full sentence, not exact match"""
        if not user_message:
            return (
                smart_response_system.format_question(
                    "Apakah solusi di atas berhasil membantu?",
                    ["Ya, berhasil!", "Tidak, masih error"]
                ),
                DialogState.ASKING_SOLUTION_WORKED
            )

        answer = user_message.lower().strip()
        answer_clean = re.sub(r'[!?.,;:]', '', answer).strip()

        # Short acknowledgements are not proof that the issue is fixed.
        # Ask once more so "oke/siap/lanjut" does not close the case too early.
        if answer_clean in SmartDialogFlowHandler.ACKNOWLEDGMENT_PATTERNS:
            return (
                smart_response_system.format_question(
                    "Siap. Setelah dicoba, apakah masalahnya sudah benar-benar berhasil diperbaiki?",
                    ["Ya, berhasil", "Tidak, masih error"]
                ),
                DialogState.ASKING_SOLUTION_WORKED
            )

        # ── Positive keywords — check if ANY appear in the full answer ──
        POSITIVE_KW = [
            'ya', 'yes', 'iya', 'ok', 'oke', 'okeh', 'okay', 'berhasil',
            'solved', 'fixed', 'worked', 'bisa', 'udah bisa', 'sudah bisa',
            'jadi', 'mantap', 'makasih', 'terima kasih', 'bagus', 'done',
            'selesai', 'normal', 'sudah', 'alhamdulillah', 'sukses', 'fix'
        ]
        # ── Negative keywords ──
        NEGATIVE_KW = [
            'tidak berhasil', 'tidak bisa', 'ga bisa', 'gak bisa', 'gabisa',
            'masih error', 'masih sama', 'masih bermasalah', 'masih tidak',
            'belum berhasil', 'belum bisa', 'belum fix', 'belum solved',
            'gagal', 'tetap error', 'tetap sama', 'tetap tidak', 'tidak jalan',
            'tidak', 'nggak', 'enggak', 'engga', 'gak', 'ga', 'no', 'nope',
            'masih', 'belum', 'error', 'salah', 'tidak ada perubahan'
        ]

        # Check negative FIRST (more specific) to avoid false positives like
        # "tidak berhasil" matching the "ya" in "saya" etc.
        is_negative = SmartDialogFlowHandler._contains_keyword(answer, NEGATIVE_KW)
        is_positive = SmartDialogFlowHandler._contains_keyword(answer, POSITIVE_KW) and not is_negative

        if is_positive:
            session.solution_worked = True
            logger.info(f"✅ Solution worked! User said: {user_message[:50]}")
            msg = smart_response_system.format_success_message(
                "solusi yang kami berikan",
                ["Jika ada masalah lagi, hubungi kami kapan saja 😊"]
            )
            return (msg, DialogState.RESOLVED)

        elif is_negative:
            logger.info(f"❌ Solution didn't work, escalating... User said: {user_message[:50]}")
            msg = (
                "Baik, saya akan eskalasi ke tim teknisi kami.\n\n"
                "Untuk membuat tiket laporan, saya butuh 3 informasi singkat:\n"
                "1️⃣ Nama unit/kendaraan\n"
                "2️⃣ Lokasi saat ini\n"
                "3️⃣ Waktu kejadian\n\n"
                "Pertama, *unit atau kendaraan mana* yang bermasalah?\n"
                "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)

        else:
            # Truly unrecognized — ask once more with clearer framing
            msg = smart_response_system.format_question(
                "Maaf, saya belum mengerti jawaban Anda.\nApakah solusi tadi berhasil memperbaiki masalahnya?",
                ["✅ Ya, berhasil!", "❌ Tidak, masih error"]
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
                "Terima kasih 😊 Tapi saya butuh nama *unit/kendaraan* yang bermasalah ya.\n\n"
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
        """Smart location handling"""
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
                "Terima kasih 😊 Tapi saya butuh info *lokasi* unit/kendaraan saat ini ya.\n\n"
                "Contoh: _Jakarta_, _Tol Cikampek KM 5_, atau _Pool Cakung_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_LOCATION)
        
        session.location = location
        logger.info(f"✓ Location: {location}")
        
        msg = (
            f"✅ Lokasi: *{location}*\n\n"
            f"Terakhir, *kapan masalah ini terjadi*?\n\n"
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
                "Bisa jawab dengan:\n"
                "• Jam spesifik (misal: _14:30_, _jam 3 sore_)\n"
                "• Waktu umum (misal: _tadi pagi_, _kemarin sore_)\n"
                "• _sekarang_ / _barusan_ jika baru terjadi"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_TIME)
        
        user_input = user_message.lower().strip()
        
        # Try to extract time - multiple formats
        time_text = None
        
        # Format: HH:MM
        time_match = re.search(r'(\d{1,2}):(\d{2})', user_input)
        if time_match:
            time_text = f"{time_match.group(1)}:{time_match.group(2)}"
        # Format: "jam 3", "jam 3 sore", "3 sore", "3 jam", etc
        elif re.search(r'(jam\s+)?(\d{1,2})', user_input):
            match = re.search(r'(jam\s+)?(\d{1,2})', user_input)
            hour = int(match.group(2))
            # Check if afternoon/evening mentioned
            if 'sore' in user_input or 'malam' in user_input:
                if hour < 12:
                    hour += 12
            time_text = f"{hour}:00"
        elif 'sekarang' in user_input or 'baru' in user_input:
            time_text = datetime.now().strftime("%H:%M")
        elif 'tadi' in user_input or 'barusan' in user_input:
            time_text = "~15 menit yang lalu"
        else:
            # Try to parse natural language time
            time_keywords = {
                'pagi': '09:00', 'siangan': '12:00', 'siang': '12:00',
                'sore': '15:00', 'malam': '19:00', 'tengah malam': '00:00',
                'subuh': '05:30', 'fajar': '05:30'
            }
            for keyword, default_time in time_keywords.items():
                if keyword in user_input:
                    time_text = default_time
                    break
        
        if not time_text:
            prompt = (
                "Maaf, saya kurang mengerti waktunya 🙏\n\n"
                "Coba tulis ulang dengan format seperti:\n"
                "• _14:30_ atau _jam 3 sore_\n"
                "• _tadi pagi_ atau _kemarin malam_\n"
                "• _sekarang_ atau _barusan_"
            )
            return (smart_response_system.format_for_whatsapp(prompt), DialogState.COLLECTING_TIME)
        
        session.issue_time = time_text
        logger.info(f"✓ Time: {time_text}")
        
        # Show summary and ask confirmation
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
        
        # Use hardcoded confirmation question (not AI - too error-prone)
        confirmation_question = "Apakah data di atas sudah benar? 🤔\n\n1️⃣ *Ya*, lanjutkan buat tiket\n2️⃣ *Tidak*, saya mau perbaiki"
        
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
            session.vehicle_unit = None
            session.location = None
            session.issue_time = None
            msg = (
                "Baik, kita ulangi datanya ya.\n\n"
                "*Unit atau kendaraan mana* yang bermasalah?\n"
                "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
            )
            return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)

        else:
            msg = "Mohon pilih salah satu ya:\n\n1️⃣ Ya, data sudah benar\n2️⃣ Tidak, saya mau ubah\n\n(Kirim 1 atau 2)"
            return (smart_response_system.format_for_whatsapp(msg), DialogState.CONFIRMING_DETAILS)

    
    @staticmethod
    def _ask_for_unit(session: ConversationSession) -> Tuple[str, DialogState]:
        """Ask for unit info with clear prompt"""
        name = session.driver_name or "Kak"
        msg = (
            f"Baik {name}, untuk membuat tiket laporan, saya butuh 3 data singkat.\n\n"
            f"Pertama, *unit atau kendaraan mana* yang bermasalah?\n"
            f"(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
        )
        return (smart_response_system.format_for_whatsapp(msg), DialogState.COLLECTING_UNIT)
