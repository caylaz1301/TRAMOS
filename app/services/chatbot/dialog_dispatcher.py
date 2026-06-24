"""Dispatcher tunggal untuk seluruh transisi dialog WhatsApp TRAMOS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.services.chatbot.intent_classifier import (
    ConversationIntent,
    TramosIntentClassifier,
)
from app.services.chatbot.session_manager import ConversationSession, DialogState
from app.services.chatbot.smart_dialog_flow import SmartDialogFlowHandler
from app.services.chatbot.solution_searcher import solution_searcher
from app.utils.smart_response_system import smart_response_system


@dataclass(frozen=True)
class DialogTurnResult:
    """Hasil satu turn yang kemudian dipersist dan dilacak oleh route."""

    response: str
    next_state: DialogState
    intent: str
    category: Optional[str] = None
    action: Optional[str] = None
    solution_outcome: Optional[str] = None
    thinking_message: Optional[str] = None  # Pesan "⏳ Sebentar..." sebelum response utama


class DialogFlowDispatcher:
    """Menjaga validasi dan transisi state berada di satu tempat."""

    FIELD_CHOICES = {
        # Problem
        "1": "problem",
        "masalah": "problem",
        "masalah nya": "problem",
        "deskripsi": "problem",
        "deskripsi masalah": "problem",
        # Unit
        "2": "unit",
        "unit": "unit",
        "unit/kendaraan": "unit",
        "kendaraan": "unit",
        "armada": "unit",
        # Location
        "3": "location",
        "lokasi": "location",
        "lokasinya": "location",
        "tempat": "location",
        # Time
        "4": "time",
        "waktu": "time",
        "waktu kejadian": "time",
        "jam": "time",
        "tanggal": "time",
        "pagi": "time",
        "siang": "time",
        "sore": "time",
        "malam": "time",
        # All
        "semua": "all",
        "reset": "all",
        "ulangi": "all",
        "ulang": "all",
    }
    MENU_PROBLEMS = {
        "1": "GPS tidak berfungsi atau lokasi kendaraan tidak update",
        "2": "Kamera atau dashcam mengalami error",
        "3": "Baterai perangkat cepat habis atau perangkat tidak menyala",
        "4": "Koneksi perangkat terputus atau unit tampil offline",
    }
    INVALID_DATA_ANSWERS = {
        "1",
        "2",
        "ya",
        "iya",
        "yes",
        "tidak",
        "enggak",
        "nggak",
        "gak",
        "ga",
        "oke",
        "ok",
        "siap",
        "lanjut",
        "tidak masih error",
        "masih error",
        "belum berhasil",
    }
    UNKNOWN_DATA_ANSWERS = {
        "tidak tahu",
        "tidak tau",
        "gak tahu",
        "ga tahu",
        "nggak tahu",
        "enggak tahu",
        "tidak ada",
        "skip",
    }

    @classmethod
    def dispatch(
        cls,
        session: ConversationSession,
        user_message: str,
    ) -> DialogTurnResult:
        state = session.current_state
        clean = TramosIntentClassifier.normalize(user_message)

        if state == DialogState.GREETING:
            return DialogTurnResult(
                response=smart_response_system.format_for_whatsapp(
                    smart_response_system.greeting()
                ),
                next_state=DialogState.COLLECTING_NAME,
                intent="greeting",
            )

        if state == DialogState.COLLECTING_NAME:
            response, next_state = SmartDialogFlowHandler._handle_name_input(
                session,
                user_message,
            )
            return DialogTurnResult(response, next_state, "data_collection")

        if state == DialogState.COLLECTING_PROBLEM:
            # Nomor menu 1-4 diperlakukan sebagai pilihan masalah yang valid.
            if clean in cls.MENU_PROBLEMS:
                return cls._handle_problem(session, cls.MENU_PROBLEMS[clean])
            return cls._handle_problem(session, user_message)

        if state == DialogState.ASKING_SOLUTION_WORKED:
            # ── Feedback shortcut: short responses like "2", "tidak", "1" → direct routing ──
            # Only apply when a KB solution was actually presented to the user.
            # If session has no kb_solution, these short inputs are NOT feedback.
            clean = TramosIntentClassifier.normalize(user_message)
            has_kb_solution = bool(getattr(session, 'kb_solution', None))
            positive_exact = {"1", "ya", "iya", "yes", "berhasil", "sudah", "oke", "ok", "fix", "bisa"}
            negative_exact = {"2", "tidak", "nggak", "gak", "ga", "engga", "enggak", "nope",
                              "tdk", "gabisa"}
            if clean in negative_exact and has_kb_solution:
                return DialogTurnResult(
                    smart_response_system.format_for_whatsapp(
                        "Baik, saya akan bantu buat tiket laporan ke tim teknisi.\n\n"
                        "Sebutkan *unit atau kendaraan* yang bermasalah:\n"
                        "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
                    ),
                    DialogState.COLLECTING_UNIT,
                    "solution_feedback",
                    session.problem_category,
                    solution_outcome="escalated",
                )
            if clean in positive_exact and has_kb_solution:
                return DialogTurnResult(
                    smart_response_system.format_for_whatsapp(
                        "Alhamdulillah masalahnya sudah terselesaikan! 😊\n\n"
                        "Kalau ada kendala lain, langsung hubungi kami ya.\n"
                        "Selalu jaga keselamatan di jalan! 🚛"
                    ),
                    DialogState.CLOSED,
                    "resolution",
                    session.problem_category,
                    solution_outcome="worked",
                )

            response, next_state = SmartDialogFlowHandler._handle_solution_feedback(
                session,
                user_message,
            )
            outcome = None
            if next_state == DialogState.RESOLVED:
                outcome = "worked"
            elif next_state == DialogState.COLLECTING_UNIT:
                outcome = "escalated"
            return DialogTurnResult(
                response,
                next_state,
                "solution_feedback",
                session.problem_category,
                solution_outcome=outcome,
            )

        if state == DialogState.COLLECTING_UNIT:
            return cls._handle_unit(session, user_message, clean)

        if state == DialogState.COLLECTING_LOCATION:
            return cls._handle_location(session, user_message, clean)

        if state == DialogState.COLLECTING_TIME:
            return cls._handle_time(session, user_message, clean)

        if state == DialogState.COLLECTING_REALTIME_REFERENCE:
            return cls._handle_realtime_reference(session, user_message, clean)

        if state == DialogState.CONFIRMING_DETAILS:
            return cls._handle_confirmation(session, user_message)

        if state == DialogState.CORRECTING_DETAILS:
            return cls._handle_correction_choice(session, clean)

        if state == DialogState.CREATING_TICKET:
            return DialogTurnResult(
                "Laporan sedang diproses ya, tunggu sebentar ya.",
                DialogState.CREATING_TICKET,
                "waiting",
                session.problem_category,
            )

        return DialogTurnResult(
            "Percakapan sebelumnya sudah selesai. Kirim *menu* untuk memulai laporan baru.",
            state,
            "closed",
            session.problem_category,
        )

    @classmethod
    def _handle_problem(
        cls,
        session: ConversationSession,
        user_message: str,
    ) -> DialogTurnResult:
        text = user_message.strip()
        normalized = TramosIntentClassifier.normalize(text)

        # Waktu tanpa konteks masalah belum cukup untuk membuat laporan.
        if cls._looks_like_time(normalized):
            return DialogTurnResult(
                cls.problem_prompt("Tunggu dulu, saya perlu tahu dulu masalahnya."),
                DialogState.COLLECTING_PROBLEM,
                "clarification",
            )

        if SmartDialogFlowHandler.is_sensitive_or_out_of_scope(text):
            return DialogTurnResult(
                SmartDialogFlowHandler.sensitive_request_response(),
                DialogState.COLLECTING_PROBLEM,
                ConversationIntent.OUT_OF_SCOPE.value,
            )
        if SmartDialogFlowHandler.is_blame_without_evidence_request(text):
            return DialogTurnResult(
                SmartDialogFlowHandler.blame_without_evidence_response(),
                DialogState.COLLECTING_PROBLEM,
                "policy_guardrail",
                "Driver",
            )

        # Smart check: jika input jelas OUT OF SCOPE, tolak langsung
        if TramosIntentClassifier.is_out_of_scope(text):
            return DialogTurnResult(
                cls.out_of_scope_response(),
                DialogState.COLLECTING_PROBLEM,
                ConversationIntent.OUT_OF_SCOPE.value,
            )

        intent = TramosIntentClassifier.classify(text)
        session.last_intent = intent.intent.value
        session.interaction_mode = intent.intent.value

        if session.correction_target == "problem":
            analysis = SmartDialogFlowHandler.analyze_problem(text)
            session.problem_description = text
            session.problem_category = analysis.get("category") or "Service"
            session.problem_severity = analysis.get("severity", "normal")
            session.correction_target = None
            response, state = SmartDialogFlowHandler._show_summary(session)
            return DialogTurnResult(
                response,
                state,
                "correction",
                session.problem_category,
            )

        session.problem_description = text

        if intent.intent == ConversationIntent.INFORMATIONAL:
            return cls._answer_information(session)

        if intent.intent == ConversationIntent.EMERGENCY:
            session.problem_category = "Emergency"
            session.problem_severity = "critical"
            response = (
                "Utamakan keselamatan terlebih dahulu:\n"
                "• Hentikan kendaraan di tempat aman jika memungkinkan\n"
                "• Nyalakan lampu hazard dan pasang tanda pengaman\n"
                "• Jika ada korban atau bahaya langsung, hubungi layanan darurat setempat\n\n"
                "Saya bantu catat laporan ini sebagai prioritas tinggi ya.\n\n"
                "Sebutkan *unit atau kendaraan* yang mengalami kejadian."
            )
            return DialogTurnResult(
                smart_response_system.format_for_whatsapp(response),
                DialogState.COLLECTING_UNIT,
                intent.intent.value,
                "Emergency",
            )

        if intent.intent == ConversationIntent.REALTIME_REQUEST:
            session.problem_category = "Tracking"
            response = (
                "Untuk mengecek posisi kendaraan, saya perlu nomor polisi, kode unit, "
                "atau referensi task terlebih dahulu.\n\n"
                "Unit mana yang ingin dicek?"
            )
            return DialogTurnResult(
                smart_response_system.format_for_whatsapp(response),
                DialogState.COLLECTING_REALTIME_REFERENCE,
                intent.intent.value,
                "Tracking",
            )

        if intent.intent == ConversationIntent.TICKET_REQUEST:
            session.problem_category = "Service"
            session.problem_severity = "medium"
            response, state = SmartDialogFlowHandler._ask_for_unit(session)
            return DialogTurnResult(
                response,
                state,
                intent.intent.value,
                session.problem_category,
            )

        analysis = SmartDialogFlowHandler.analyze_problem(text)
        session.problem_category = analysis.get("category") or "Service"
        session.problem_severity = analysis.get("severity", "normal")

        # Siapkan thinking message untuk dikirim duluan SEBELUM AI search
        driver_name = session.driver_name or "Kak"
        category_label = session.problem_category or "perangkat tersebut"

        if session.problem_severity == "critical":
            thinking_msg = "⏳ Tunggu sebentar, saya cari solusinya dulu untuk Anda..."
        else:
            thinking_msg = "⏳ Sebentar ya, saya cari solusinya dulu..."

        # Greeting message untuk solusi
        greeting_msg = f"{driver_name}, saya bantu untuk masalah {category_label} ya.\n\n"

        # Cari solusi di KB - INI BISA LAMA KARENA AI SEARCH
        response, next_state = SmartDialogFlowHandler._search_kb_smart(
            session,
            acknowledge_prefix=greeting_msg
        )

        # Jika tidak ada solusi di KB, langsung arahkan ke pembuatan tiket
        if not session.kb_solution or not response:
            escalation_msg = (
                f"{driver_name}, saya bantu untuk masalah {category_label} ya.\n\n"
                f"Karena masalah ini perlu ditindaklanjuti oleh tim teknisi, "
                f"saya bantu buatkan tiket laporan ya.\n\n"
                f"Sebutkan *unit atau kendaraan* yang bermasalah:\n"
                "(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)"
            )
            return DialogTurnResult(
                smart_response_system.format_for_whatsapp(escalation_msg),
                DialogState.COLLECTING_UNIT,
                "troubleshooting",
                session.problem_category,
                thinking_message=thinking_msg,
            )

        return DialogTurnResult(
            response,
            next_state,
            ConversationIntent.TROUBLESHOOTING.value,
            session.problem_category,
            thinking_message=thinking_msg,
        )

    @classmethod
    def _answer_information(cls, session: ConversationSession) -> DialogTurnResult:
        solutions = solution_searcher.search_solutions(
            session.problem_description,
            session.problem_category,
        )
        if solutions:
            session.kb_solution = solutions[0]
            response = solution_searcher.format_solution_for_user(
                solutions[0],
                user_context={"multiple_attempts": session.message_count},
            )
            response += "\n\nAda pertanyaan lain seputar TRAMOS?"
        else:
            response = (
                "Maaf, saya belum menemukan panduan yang sesuai di knowledge base TRAMOS.\n\n"
                "Coba tuliskan nama fitur atau proses yang ingin diketahui dengan lebih spesifik."
            )
        return DialogTurnResult(
            smart_response_system.format_for_whatsapp(response),
            DialogState.COLLECTING_PROBLEM,
            ConversationIntent.INFORMATIONAL.value,
            session.problem_category,
        )

    @classmethod
    def _handle_unit(
        cls,
        session: ConversationSession,
        user_message: str,
        clean: str,
    ) -> DialogTurnResult:
        if cls._invalid_required_value(clean) or cls._looks_like_time(clean):
            return DialogTurnResult(
                cls.required_field_prompt("unit/kendaraan", "B 1234 AB atau TRAM-001"),
                DialogState.COLLECTING_UNIT,
                "clarification",
                session.problem_category,
            )

        response, next_state = SmartDialogFlowHandler._handle_unit_input(
            session,
            user_message,
        )
        if session.correction_target == "unit" and next_state == DialogState.COLLECTING_LOCATION:
            session.correction_target = None
            response, next_state = SmartDialogFlowHandler._show_summary(session)
        return DialogTurnResult(
            response,
            next_state,
            "data_collection",
            session.problem_category,
        )

    @classmethod
    def _handle_location(
        cls,
        session: ConversationSession,
        user_message: str,
        clean: str,
    ) -> DialogTurnResult:
        if cls._invalid_required_value(clean) or cls._looks_like_time(clean):
            return DialogTurnResult(
                cls.required_field_prompt(
                    "lokasi unit saat ini",
                    "Tol Cikampek KM 42 atau Pool Cakung",
                ),
                DialogState.COLLECTING_LOCATION,
                "clarification",
                session.problem_category,
            )

        response, next_state = SmartDialogFlowHandler._handle_location_input(
            session,
            user_message,
        )
        if session.correction_target == "location" and next_state == DialogState.COLLECTING_TIME:
            session.correction_target = None
            response, next_state = SmartDialogFlowHandler._show_summary(session)
        return DialogTurnResult(
            response,
            next_state,
            "data_collection",
            session.problem_category,
        )

    @classmethod
    def _handle_time(
        cls,
        session: ConversationSession,
        user_message: str,
        clean: str,
    ) -> DialogTurnResult:
        if cls._invalid_required_value(clean):
            return DialogTurnResult(
                cls.required_field_prompt("waktu kejadian", "14:30 atau kemarin malam"),
                DialogState.COLLECTING_TIME,
                "clarification",
                session.problem_category,
            )
        response, next_state = SmartDialogFlowHandler._handle_time_input(
            session,
            user_message,
        )
        if next_state == DialogState.CONFIRMING_DETAILS:
            session.correction_target = None
        return DialogTurnResult(
            response,
            next_state,
            "data_collection",
            session.problem_category,
        )

    @classmethod
    def _handle_confirmation(
        cls,
        session: ConversationSession,
        user_message: str,
    ) -> DialogTurnResult:
        clean = TramosIntentClassifier.normalize(user_message)
        positive = {"1", "ya", "iya", "yes", "benar", "betul", "lanjut", "buat tiket"}
        negative = {"2", "tidak", "nggak", "gak", "ga", "salah", "ubah", "koreksi"}

        if clean in positive:
            # Langsung transition ke CREATING_TICKET tanpa kirim pesan.
            # _process_message_turn akan skip result.response dan langsung
            # panggil _create_ticket_from_session → kirim tiket sebagai SATU-SATUNYA pesan.
            return DialogTurnResult(
                response="",  # NO intermediate message — ticket response only
                next_state=DialogState.CREATING_TICKET,
                intent="confirmation",
                category=session.problem_category,
                action="create_ticket",
            )
        if clean in negative or SmartDialogFlowHandler._contains_keyword(
            clean,
            list(negative),
        ):
            return DialogTurnResult(
                cls.correction_menu(),
                DialogState.CORRECTING_DETAILS,
                "correction",
                session.problem_category,
            )
        response, state = SmartDialogFlowHandler._show_summary(session)
        return DialogTurnResult(
            response,
            state,
            "clarification",
            session.problem_category,
        )

    @classmethod
    def _handle_correction_choice(
        cls,
        session: ConversationSession,
        clean: str,
    ) -> DialogTurnResult:
        target = cls.FIELD_CHOICES.get(clean)
        if target is None:
            return DialogTurnResult(
                cls.correction_menu("Maaf, saya kurang mengerti 🙏"),
                DialogState.CORRECTING_DETAILS,
                "clarification",
                session.problem_category,
            )

        # Handle "all" - ask for each field one by one
        if target == "all":
            session.vehicle_unit = None
            session.location = None
            session.issue_time = None
            return DialogTurnResult(
                smart_response_system.format_for_whatsapp(
                    "Oke, kita koreksi satu-satu ya.\n\n"
                    "*Unit atau kendaraan mana* yang bermasalah?"
                ),
                DialogState.COLLECTING_UNIT,
                "correction",
                session.problem_category,
            )

        session.correction_target = target
        prompts = {
            "problem": (
                "Tuliskan deskripsi masalah yang benar.",
                DialogState.COLLECTING_PROBLEM,
            ),
            "unit": (
                "Tuliskan unit atau kendaraan yang benar.",
                DialogState.COLLECTING_UNIT,
            ),
            "location": (
                "Tuliskan lokasi unit yang benar.",
                DialogState.COLLECTING_LOCATION,
            ),
            "time": (
                "Tuliskan waktu kejadian yang benar.",
                DialogState.COLLECTING_TIME,
            ),
        }
        response, next_state = prompts[target]
        return DialogTurnResult(
            smart_response_system.format_for_whatsapp(response),
            next_state,
            "correction",
            session.problem_category,
        )

    @classmethod
    def _handle_realtime_reference(
        cls,
        session: ConversationSession,
        user_message: str,
        clean: str,
    ) -> DialogTurnResult:
        if cls._invalid_required_value(clean) or len(clean) < 3:
            return DialogTurnResult(
                "Boleh kirim nomor polisi, kode unit, atau referensi task yang ingin dicek?",
                DialogState.COLLECTING_REALTIME_REFERENCE,
                "clarification",
                "Tracking",
            )

        response = (
            f"Oke, saya catat referensinya: *{user_message.strip()}*.\n\n"
            "Untuk cek posisi kendaraan secara live, operator bisa bantu lewat menu "
            "*Realtime Monitor* di dashboard TRAMOS ya.\n\n"
            "Ada pertanyaan lain seputar TRAMOS?"
        )
        session.clear_issue_data()
        return DialogTurnResult(
            smart_response_system.format_for_whatsapp(response),
            DialogState.COLLECTING_PROBLEM,
            ConversationIntent.REALTIME_REQUEST.value,
            "Tracking",
        )

    @classmethod
    def _invalid_required_value(cls, clean: str) -> bool:
        return (
            not clean
            or clean in cls.INVALID_DATA_ANSWERS
            or clean in cls.UNKNOWN_DATA_ANSWERS
        )

    @staticmethod
    def _looks_like_time(clean: str) -> bool:
        """Check if the message is primarily a TIME reference, not just contains time words."""
        time_terms = {
            "tadi pagi",
            "tadi siang",
            "tadi sore",
            "tadi malam",
            "kemarin",
            "kemarin pagi",
            "kemarin siang",
            "kemarin sore",
            "kemarin malam",
            "sekarang",
            "barusan",
            "baru saja",
            "pagi",
            "siang",
            "sore",
            "malam",
        }
        # Exact match (the entire input should be a time reference)
        if clean in time_terms:
            return True
        # Starts with "jam " (e.g., "jam 3", "jam 3 sore")
        if clean.startswith("jam "):
            return True
        # Time pattern like "14:30"
        import re
        if re.match(r"^\d{1,2}:\d{2}$", clean):
            return True
        # Common time phrases as full phrase
        full_time_phrases = {
            "tadi",  # just "tadi" by itself
            "nanti",  # just "nanti" by itself
            "nanti sore",
            "nanti malam",
            "nanti pagi",
        }
        if clean in full_time_phrases:
            return True
        return False

    @staticmethod
    def out_of_scope_response() -> str:
        return smart_response_system.format_for_whatsapp(
            "Maaf, untuk saat ini saya hanya bisa bantu hal yang berkaitan dengan TRAMOS, seperti:\n"
            "• Tracking dan monitoring kendaraan\n"
            "• Safety, driver, unit, dan kendala di jalan\n"
            "• GPS, kamera, sensor, koneksi, dan aplikasi\n"
            "• SOP, dashboard, laporan, serta tiket support\n\n"
            "Silakan ceritakan pertanyaan atau kendala TRAMOS Anda."
        )

    @staticmethod
    def problem_prompt(prefix: str = "") -> str:
        message = ""
        if prefix:
            message += f"{prefix}\n\n"
        message += (
            "Ceritakan kendala yang dialami unit Anda.\n\n"
            "Boleh pakai kata-kata sendiri, tidak perlu format khusus.\n"
            "Contoh:\n"
            '• "GPS tidak update lokasi"\n'
            '• "Kamera mati di Unit B 1234"\n'
            '• "Kendaraan oli rem bocor di Tol Cipularang"\n'
            '• "Aplikasi error saat buka menu laporan"\n\n'
            "Silakan langsung ketik saja ya."
        )
        return smart_response_system.format_for_whatsapp(message)

    @staticmethod
    def required_field_prompt(field: str, example: str) -> str:
        return smart_response_system.format_for_whatsapp(
            f"Data *{field}* perlu diisi ya, biar laporan bisa dibuat.\n\n"
            f"Contoh: _{example}_"
        )

    @staticmethod
    def correction_menu(prefix: str = "") -> str:
        message = ""
        if prefix:
            message += f"{prefix}\n\n"
        message += (
            "Data mana yang ingin diperbaiki?\n\n"
            "• Deskripsi masalah\n"
            "• Unit/kendaraan\n"
            "• Lokasi\n"
            "• Waktu kejadian\n\n"
            "Silakan langsung sebutkan saja ya."
        )
        return smart_response_system.format_for_whatsapp(message)
