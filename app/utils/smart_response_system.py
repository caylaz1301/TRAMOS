"""
Smart Response System - Unified & Consolidated
Combines intelligent response generation with professional formatting
Dynamic, context-aware, NOT hardcoded templates
Complete solution: generation + formatting + utilities
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseStyle(Enum):
    """Response generation styles"""
    DIAGNOSTIC = "diagnostic"         # Asking clarifying questions
    INSTRUCTIONAL = "instructional"   # Step-by-step guidance
    EMPATHETIC = "empathetic"         # Understanding user frustration
    REASSURING = "reassuring"         # Building confidence
    URGENT = "urgent"                 # Critical issues
    PROFESSIONAL = "professional"     # Formal but friendly


class MessageType(Enum):
    """Message types for formatting"""
    GREETING = "greeting"
    QUESTION = "question"
    SOLUTION = "solution"
    CONFIRMATION = "confirmation"
    ESCALATION = "escalation"
    RESOLUTION = "resolution"
    ERROR = "error"
    NOTIFICATION = "notification"
    STATUS = "status"


class SmartResponseSystem:
    """
    Unified system untuk generate + format responses
    - Dynamic questions based on problem type
    - Smart troubleshooting steps
    - Professional formatting dengan spacing
    - Empathetic + reassuring tone
    - Complete messaging utilities
    - NOT hardcoded templates
    """
    
    # ========== EMOJI & FORMATTING CONSTANTS ==========
    EMOJI_SUCCESS = "✅"
    EMOJI_THINKING = "🤔"
    EMOJI_WARNING = "⚠️"
    EMOJI_URGENT = "🚨"
    EMOJI_INFO = "ℹ️"
    EMOJI_HELP = "🆘"
    EMOJI_TECH = "🔧"
    EMOJI_VEHICLE = "🚗"
    EMOJI_CHECK = "👍"
    EMOJI_PHONE = "📞"
    EMOJI_ERROR = "❌"
    EMOJI_FIRE = "🔥"
    
    DIVIDER_LIGHT = "─" * 35
    DIVIDER_HEAVY = "═" * 35
    
    EMOJIS = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "help": "🆘",
        "thinking": "🤔",
        "phone": "📱",
        "ticket": "🎫",
        "tool": "🛠️",
        "vehicle": "🚗",
        "camera": "📹",
        "battery": "🔋",
        "connectivity": "📡",
        "billing": "💳",
        "clock": "🕐",
        "thumbsup": "👍",
    }
    
    def __init__(self):
        """Initialize response system"""
        self.logger = logging.getLogger(__name__)
    
    # ========== DIAGNOSTIC QUESTIONS (Dynamic, not hardcoded) ==========
    
    def generate_diagnostic_questions(self, problem_category: str, severity: str) -> str:
        """
        Generate smart diagnostic questions based on problem type
        Dynamically created per category
        """
        
        context = ""
        questions = []
        
        # Dynamic question generation based on problem category
        category_lower = problem_category.lower()
        
        if category_lower in ["vehicle", "engine", "stall", "breakdown"]:
            context = "kendaraan/mesin"
            questions = [
                "Apakah kendaraan masih bisa di-start atau mati total?",
                "Ada warning light atau tanda error di dashboard?",
                "Kapan masalah ini mulai terjadi?",
            ]
        
        elif category_lower in ["gps", "tracking", "location"]:
            context = "tracking GPS"
            questions = [
                "Apakah device bisa menerima sinyal satelit?",
                "Lokasi masih terupdate atau benar-benar mati?",
                "Sudah coba restart device atau cek koneksi internet?",
            ]
        
        elif category_lower in ["camera", "video", "recording"]:
            context = "kamera/recording"
            questions = [
                "Apakah kamera sama sekali tidak rekam atau gambar blurry?",
                "Kabel power dan datanya sudah dicek?",
                "Berapa lama masalah ini berlangsung?",
            ]
        
        elif category_lower in ["battery", "power", "charger"]:
            context = "daya/charging"
            questions = [
                "Berapa persen battery dan apakah bisa tercharge?",
                "Sudah coba charger berbeda atau cek kabel?",
                "Apakah device panas waktu charging?",
            ]
        
        elif category_lower in ["connectivity", "network", "internet"]:
            context = "koneksi internet"
            questions = [
                "Apakah ada koneksi sama sekali atau putus-putus?",
                "Provider signal apa yang dipakai (4G/WiFi)?",
                "Sudah coba restart modem atau ganti network?",
            ]
        
        elif category_lower in ["app", "software", "crash"]:
            context = "aplikasi"
            questions = [
                "Aplikasi crash saat startup atau random waktu?",
                "Sudah coba uninstall/reinstall atau clear cache?",
                "Ada update terbaru yang diinstall sebelum masalah?",
            ]
        
        else:
            context = "masalahmu"
            questions = [
                "Kapan masalah ini pertama kali terjadi?",
                "Apa yang berubah sebelum masalah muncul?",
                "Sudah coba reset atau restart?",
            ]
        
        # Format with proper spacing
        response = f"Oke, saya paham ada masalah dengan {context}. 🔍\n\n"
        response += "Mari kita diagnosa step by step:\n\n"
        
        for i, q in enumerate(questions[:3], 1):
            response += f"{i}. {q}\n"
        
        response += "\nJawab saja yang bisa kamu jawab dulu ya, nanti kita selesaikan 💪"
        
        return response
    
    # ========== TROUBLESHOOTING STEPS (Dynamic, context-aware) ==========
    
    def generate_troubleshooting_steps(self, problem_category: str, severity: str) -> str:
        """
        Generate contextual troubleshooting steps - natural and conversational
        """
        
        response = "Ini langkah-langkahnya:\n\n"
        
        steps = []
        category_lower = problem_category.lower()
        
        if category_lower in ["gps", "tracking"]:
            steps = [
                ("Cek kondisi lokasi", [
                    "Sudah outdoor? Kalau masih dalam gedung, sinyal gak bakal dapat",
                    "Lihat ke langit, pastikan tidak ada penghalang",
                    "Beri waktu 2-3 menit untuk akuisisi sinyal"
                ]),
                ("Restart device tracking", [
                    "Matikan full sepenuhnya, tunggu 30 detik",
                    "Nyalakan ulang, tunggu sampai full boot",
                    "Cek apakah sinyal sudah kembali"
                ]),
                ("Verifikasi koneksi internet", [
                    "Pastikan internet device aktif",
                    "Coba reset lokasi di app settings",
                    "Kalau masih bermasalah, lanjut ke support"
                ])
            ]
        
        elif category_lower in ["camera", "video"]:
            steps = [
                ("Pemeriksaan fisik", [
                    "Lensa bersih? Cek apakah ada debu/noda",
                    "Kabel power tersambung dengan baik?",
                    "Storage device masih banyak?"
                ]),
                ("Power cycle kamera", [
                    "Lepas power selama 1-2 menit",
                    "Pasang kembali dengan hati-hati",
                    "Tunggu sampai fully boot sebelum test"
                ]),
                ("Test recording", [
                    "Coba record video pendek sekitar 30 detik",
                    "Lihat kualitas video normal atau masih error?",
                    "Kalau OK, masalah sudah solved"
                ])
            ]
        
        elif category_lower in ["battery", "power"]:
            steps = [
                ("Cek status baterai", [
                    "Lihat persentase battery sekarang berapa?",
                    "Baterai bisa di-charge atau emang tidak bisa charge?",
                    "Charger yang digunakan original atau compatible?"
                ]),
                ("Reset baterai", [
                    "Lepas baterai selama 2 menit (kalau bisa di-remove)",
                    "Pasang kembali dengan benar",
                    "Coba charge full dari 0%"
                ]),
                ("Verifikasi fungsi", [
                    "Nyalakan device dan lihat apakah baterai meningkat saat charging",
                    "Gunakan device normal dan lihat durasi battery",
                    "Kalau masih cepat habis, mungkin perlu ganti unit"
                ])
            ]
        
        elif category_lower in ["connectivity", "network"]:
            steps = [
                ("Cek kualitas sinyal", [
                    "Berapa bar sinyal sekarang? Minimal 2 bar untuk data",
                    "WiFi atau mobile data yang error?",
                    "Signal stabil atau sering putus-putus?"
                ]),
                ("Restart koneksi", [
                    "Matikan WiFi/data selama 10 detik",
                    "Nyalakan kembali dan tunggu reconnect",
                    "Lihat apakah sinyal sudah stabil"
                ]),
                ("Uji coba koneksi", [
                    "Coba buka app untuk test koneksi",
                    "Lihat apakah data flowing normal",
                    "Kalau stabil, masalah solved"
                ])
            ]
        
        else:
            # Generic
            steps = [
                ("Restart perangkat", [
                    "Matikan sepenuhnya, tunggu 1 menit",
                    "Nyalakan kembali dengan normal",
                    "Tunggu sampai fully booted sebelum test"
                ]),
                ("Cek kondisi dasar", [
                    "Koneksi internet masih OK?",
                    "Battery masih cukup?",
                    "Storage tidak penuh?"
                ]),
                ("Test fungsi bermasalah", [
                    "Coba feature yang tadinya error",
                    "Dokumentasikan apa yang terjadi",
                    "Apakah masalah masih konsisten atau sudah hilang?"
                ])
            ]
        
        # Format steps cleaner dan lebih natural
        for i, (step_title, instructions) in enumerate(steps, 1):
            response += f"{i}. {step_title}:\n"
            for instruction in instructions:
                response += f"   • {instruction}\n"
            response += "\n"
        
        response = response.strip()
        
        return response
    
    # ========== EMPATHETIC OPENING ==========
    
    def generate_empathetic_opening(self, problem_category: str, user_frustration: bool = False) -> str:
        """
        Generate empathetic opening acknowledging user's situation
        """
        
        empathy_map = {
            "vehicle": "Kendaraan mogok itu benar-benar mengganggu operasional 🚗",
            "gps": "Tracking hilang berarti monitoring jadi blind spot 📍",
            "camera": "Recording error, bisa jadi dokumentasi perjalanan berantakan 📹",
            "battery": "Daya yang cepat habis pasti bikin khawatir di jalan 🔋",
            "connectivity": "Koneksi putus-putus itu yang paling menjengkelkan saat op 📡",
            "app": "App yang error bisa bikin sistem seolah offline 😞",
        }
        
        category_lower = problem_category.lower()
        line = empathy_map.get(category_lower, "Ada masalah yang mengganggu, saya bantu cari solusinya 💪")
        
        if user_frustration:
            line += " Jangan khawatir, kita handle ini bareng-bareng."
        
        return line + "\n"
    
    # ========== ESCALATION DETECTION ==========
    
    @staticmethod
    def should_escalate(problem_category: str, symptoms: List[str], attempts: int = 0) -> Tuple[bool, str]:
        """
        Smart decision: should we escalate to human?
        Returns: (should_escalate, reason)
        """
        
        critical_symptoms = [
            "tidak bisa hidup", "smoke", "api", "panas berlebihan",
            "bocor", "accident", "emergency", "semua sistem mati"
        ]
        
        # Check if critical
        for symptom in symptoms:
            if any(crit in symptom.lower() for crit in critical_symptoms):
                return True, "KRITIS: Butuh immediate help"
        
        # If user has tried multiple times
        if attempts >= 3:
            return True, "Sudah coba berkali-kali, butuh expert"
        
        # Vehicle issues usually need escalation after attempts
        if problem_category.lower() in ["vehicle", "engine"] and attempts >= 2:
            return True, "Masalah kendaraan persisten, butuh mechanic"
        
        return False, ""
    
    # ========== REASSURANCE MESSAGE ==========
    
    @staticmethod
    def generate_reassurance(resolution_likelihood: float) -> str:
        """
        Generate reassuring message based on likelihood of resolution
        """
        
        if resolution_likelihood >= 0.8:
            return "Ini masalah common dan biasanya bisa di-fix dengan langkah-langkah tadi. Semoga cepat selesai 🤞"
        elif resolution_likelihood >= 0.5:
            return "Ada kemungkinan besar langkah-langkah ini bisa membantu. Tapi jika masih tidak bisa, kita akan eskalasi 👍"
        else:
            return "Ini mungkin butuh bantuan teknis lebih dalam. Jangan khawatir, tim expert siap membantu 💪"
    
    # ========== FORMATTING METHODS ==========
    
    def format_escalation_message(self, reason: str, ticket_id: Optional[str] = None, estimated_time: str = "1-2 jam") -> str:
        """
        Format professional escalation message
        """
        
        response = f"{self.EMOJI_TECH} Escalation ke Tim Expert\n"
        response += self.DIVIDER_HEAVY + "\n\n"
        
        response += f"Kami lihat ini butuh bantuan lebih dalam.\n\n"
        response += f"📋 Alasan: {reason}\n"
        
        if ticket_id:
            response += f"🎫 Ticket ID: {ticket_id}\n"
        
        response += f"\n⏱️ Tim expert akan kontak kamu dalam ~{estimated_time}\n"
        response += "\nTerima kasih atas kesabaran mu 🙏"
        
        return response
    
    def format_success_message(self, solution_applied: str, tips: Optional[List[str]] = None) -> str:
        """
        Format success/resolution message
        """
        
        response = f"{self.EMOJI_SUCCESS} Problem Teratasi!\n\n"
        response += f"Senang mendengar {solution_applied} sudah fixed! 🎉\n\n"
        
        if tips:
            response += "Tips untuk ke depannya:\n"
            for tip in tips[:3]:
                response += f"  • {tip}\n"
            response += "\n"
        
        response += "Jika ada masalah lagi, langsung hubungi kami ya 👍\n"
        response += "Stay safe on the road! 🚗"
        
        return response
    
    def format_error_recovery(self, error_message: str, suggested_action: str) -> str:
        """
        Format error message with helpful suggestion
        """
        
        response = f"{self.EMOJI_WARNING} Ada Kendala\n\n"
        response += f"Masalah: {error_message}\n\n"
        response += f"Coba: {suggested_action}\n\n"
        response += "Jika masih tidak bisa, kami siap membantu lebih lanjut 💪"
        
        return response
    
    def format_status_update(self, status: str, details: str, next_step: Optional[str] = None) -> str:
        """
        Format status update message
        """
        
        response = f"{self.EMOJI_INFO} Status Update\n"
        response += self.DIVIDER_LIGHT + "\n\n"
        
        response += f"Status: {status}\n"
        response += f"Detail: {details}\n"
        
        if next_step:
            response += f"\n📌 Langkah berikutnya: {next_step}"
        
        return response
    
    def format_contact_message(self, reason: str, contact_type: str = "phone", contact_info: Optional[str] = None) -> str:
        """
        Format contact/escalation message
        """
        
        response = f"{self.EMOJI_PHONE} Hubungi Tim Support\n"
        response += self.DIVIDER_LIGHT + "\n\n"
        
        response += f"Alasan: {reason}\n\n"
        
        if contact_type == "phone":
            response += f"{self.EMOJI_HELP} Call: "
        elif contact_type == "chat":
            response += f"💬 Chat/WA: "
        
        response += contact_info or "Tim kami siap membantu\n"
        
        return response
    
    # ========== UTILITY METHODS (from whatsapp_formatter) ==========
    
    def greeting(self, name: str = None) -> str:
        """Format greeting message with time-based salutation"""
        hour = datetime.now().hour
        time_greeting = (
            "Pagi" if hour < 12 else
            "Siang" if hour < 17 else
            "Sore" if hour < 19 else
            "Malam"
        )
        
        message = f"Selamat {time_greeting}! 👋\n\n"
        
        if name:
            message += f"Halo {name}! "
            message += "Kami TRAMOS Support Bot 🤖\n\n"
            message += "Siap membantu masalahmu 24/7 ✨"
        else:
            # First greeting - just ask for name
            message += "Kami TRAMOS Support Bot 🤖\n\n"
            message += "Siapa nama Anda?"
        
        return message
    
    def format_professional_header(self) -> str:
        """Add professional header"""
        return (
            "╔═══════════════════════════════╗\n"
            "║  🤖 TRAMOS Support Bot 24/7  ║\n"
            "║  Siap membantu masalahmu!    ║\n"
            "╚═══════════════════════════════╝"
        )
    
    def format_divider(self, style: str = "─") -> str:
        """Format visual divider"""
        return "─" * 35
    
    def add_footer(self, message: str, include_hours: bool = False) -> str:
        """Add professional footer to message"""
        footer = "\n\n" + self.format_divider()
        footer += "\n⏱️ *Jam Operasional:* 06:00 - 22:00 (WIB)" if include_hours else ""
        footer += "\n📧 *Email:* support@tramos.id"
        footer += "\n☎️ *Hotline:* +62-800-1234567"
        footer += "\n\nTerima kasih! 🙏"
        
        return message + footer
    
    def format_list(self, title: str, items: List[str], bullet_style: str = "•") -> str:
        """Format list of items"""
        message = f"\n*{title}*\n\n"
        
        for item in items:
            message += f"{bullet_style} {item}\n"
        
        return message.strip()
    
    def format_question(self, question: str, options: Optional[List[str]] = None, example: str = None) -> str:
        """Format question with options"""
        message = f"🤔 {question}\n\n"
        
        if options:
            for i, option in enumerate(options, 1):
                message += f"{i}️⃣ {option}\n"
            message += "\n(Kirim nomor atau jawab langsung)"
        elif example:
            message += f"Contoh: {example}\n"
        
        return message.strip()
    
    def format_confirmation(self, title: str, details: Dict[str, str], action: str = "Konfirmasi") -> str:
        """Format confirmation message"""
        message = f"\n*{title}*\n\n"
        
        message += "━━━━━━━━━━━━━━━\n"
        for key, value in details.items():
            message += f"{key}: {value}\n"
        message += "━━━━━━━━━━━━━━━\n\n"
        
        message += f"Apakah data di atas sudah benar? (ya/tidak)"
        
        return message.strip()
    
    def format_timeout_notice(self, time_remaining: int, session_id: str) -> str:
        """Format session timeout warning"""
        message = (
            f"⏰ *Perhatian: Session Akan Berakhir*\n\n"
            f"Waktu tersisa: {time_remaining} detik\n"
            f"Session ID: {session_id}\n\n"
            f"Balas pesan ini untuk melanjutkan percakapan.\n"
            f"Jika tidak ada respons, session akan ditutup otomatis."
        )
        
        return message.strip()
    
    def format_session_closed(self, session_id: str, reason: str, duration_seconds: int) -> str:
        """Format session closed message"""
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        
        message = (
            f"{self.EMOJI_ERROR} *Session Ditutup*\n\n"
            f"Session ID: {session_id}\n"
            f"Durasi: {minutes}m {seconds}s\n"
            f"Alasan: {reason}\n\n"
            f"Kirim pesan baru untuk memulai percakapan lagi. 😊"
        )
        
        return message.strip()
    
    def wrap_solution_steps(self, problem_type: str, steps: List[str], kb_id: str = None) -> str:
        """
        Wrap solution steps professionally
        """
        emoji_map = {
            "vehicle": "🚗",
            "gps": "🗺️",
            "camera": "📹",
            "battery": "🔋",
            "connectivity": "📡",
            "app": "📱",
        }
        
        emoji = emoji_map.get(problem_type.lower(), "🛠️")
        
        message = f"{emoji} *Solusi untuk {problem_type}*\n\n"
        
        for i, step in enumerate(steps, 1):
            message += f"*Step {i}:* {step}\n"
        
        message += "\n" + "─" * 35 + "\n"
        message += "Coba langkah-langkah di atas 💪\n"
        message += "Apakah sudah berhasil? (ya/tidak)"
        
        if kb_id:
            message += f"\n\nReference: {kb_id}"
        
        return message
    
    def format_for_whatsapp(self, message: str, message_type: MessageType = MessageType.NOTIFICATION, add_footer: bool = False) -> str:
        """
        Final formatting for WhatsApp
        - Ensures optimal length
        - Adds proper emojis and formatting
        - Validates format
        """
        # Clean message
        message = message.strip()
        
        # Ensure length is reasonable (WhatsApp has soft limits)
        if len(message) > 1000:
            self.logger.warning(f"Message too long ({len(message)} chars), truncating")
            message = message[:997] + "..."
        
        # Add footer if requested
        if add_footer and message_type != MessageType.CONFIRMATION:
            message = self.add_footer(message)
        
        return message


# Singleton instance
smart_response_system = SmartResponseSystem()
