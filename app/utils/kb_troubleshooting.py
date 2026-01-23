"""
Knowledge Base - Troubleshooting Database
Comprehensive troubleshooting guides untuk fleet management issues
Diorganisir by category dengan dialog flow yang natural
"""

# Format: Setiap issue punya problem detection, troubleshooting steps, dan escalation triggers

KB_TROUBLESHOOTING = {
    # ========== GPS & TRACKING ISSUES ==========
    "gps": {
        "keywords": ["gps", "lokasi", "location", "tracking", "posisi", "signal", "sinyal", "gps mati", "gps error"],
        "title": "GPS & Tracking Issues",
        "symptoms": [
            "GPS tidak akurat",
            "Lokasi tidak update",
            "GPS signal lemah",
            "Device tidak terdeteksi",
        ],
        "first_response": (
            "Saya lihat ada masalah dengan GPS tracking. Mari kita selesaikan ini step by step. 🗺️\n\n"
            "Pertama, cek beberapa hal:\n"
            "1. Apakah device punya view ke langit (tidak tertutup atap/bangunan)?\n"
            "2. Pastikan GPS sudah aktif di device"
        ),
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Cek Physical Setup",
                "instructions": [
                    "Pastikan antenna GPS tidak tertutup",
                    "Device harus punya clear sky view (tidak dalam garasi/bangunan)",
                    "Tunggu 2-3 menit untuk akuisisi sinyal pertama (cold start)",
                ],
                "verification": "Apakah sinyal GPS sudah stabil sekarang?"
            },
            {
                "step": 2,
                "title": "Restart Device",
                "instructions": [
                    "Matikan device selama 30 detik",
                    "Nyalakan kembali",
                    "Tunggu hingga GPS lock (biasanya 1-2 menit)",
                ],
                "verification": "Apakah lokasi sudah terdeteksi?"
            },
            {
                "step": 3,
                "title": "Cek Koneksi Internet",
                "instructions": [
                    "Pastikan device terhubung ke internet (WiFi atau mobile data)",
                    "Coba ping ke server untuk test koneksi",
                    "Pastikan signal strength cukup (-120 dBm atau lebih baik)",
                ],
                "verification": "Apakah koneksi internet stabil?"
            },
        ],
        "escalation_triggers": [
            "Masih tidak ada sinyal setelah 5 menit di lokasi outdoor",
            "Device terus restart",
            "Lokasi selalu salah > 100 meter",
        ],
        "workaround": (
            "Sementara menunggu fix:\n"
            "• Update lokasi manual dari aplikasi\n"
            "• Gunakan checkpoint terdekat\n"
            "• Hubungi dispatch untuk tracking sementara"
        ),
    },

    # ========== CONNECTIVITY ISSUES ==========
    "connectivity": {
        "keywords": ["internet", "signal", "connection", "offline", "tidak connect", "connection failed", "koneksi", "jaringan"],
        "title": "Internet & Network Connectivity",
        "symptoms": [
            "Tidak bisa connect ke server",
            "Data tidak tersinkronisasi",
            "Signal lemah",
            "Timeout error",
        ],
        "first_response": (
            "Ada masalah koneksi network. Tidak khawatir, ini sering terjadi di jalan. 📡\n\n"
            "Mari cek koneksi kamu:\n"
            "1. Kamu sedang pakai WiFi atau mobile data?\n"
            "2. Berapa signal strength (jumlah bar)?"
        ),
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Check Network Status",
                "instructions": [
                    "Buka Settings → Network",
                    "Lihat tipe koneksi (WiFi/LTE/4G) dan signal strength",
                    "Catat signal dBm (lebih dari -100 dBm sudah cukup)",
                ],
                "verification": "Signal strength bagus (minimal -100 dBm)?"
            },
            {
                "step": 2,
                "title": "Switch Network Type",
                "instructions": [
                    "Coba switch dari WiFi ke mobile data atau sebaliknya",
                    "Tunggu 10 detik untuk reconnect",
                    "Coba open app lagi",
                ],
                "verification": "Apakah app sudah konek sekarang?"
            },
            {
                "step": 3,
                "title": "Airplane Mode Reset",
                "instructions": [
                    "Nyalakan Airplane Mode 5 detik",
                    "Matikan Airplane Mode",
                    "Tunggu 15 detik untuk reconnect semua network",
                ],
                "verification": "Apakah sudah connect ke server?"
            },
        ],
        "escalation_triggers": [
            "Signal bars penuh tapi tetap timeout",
            "Semua app lain bisa tapi app ini tidak",
            "Tidak ada improvement setelah 10 menit",
        ],
        "workaround": (
            "Jika tetap offline:\n"
            "• Gunakan offline mode jika tersedia\n"
            "• Queue data untuk sync nanti\n"
            "• Update status ke dispatch via SMS/call"
        ),
    },

    # ========== DEVICE ISSUES ==========
    "device": {
        "keywords": ["device", "crash", "freeze", "restart", "reboot", "boot", "not responding", "error", "device tidak mau"],
        "title": "Device Hardware & Software Issues",
        "symptoms": [
            "Device restart sendiri",
            "App freeze/hang",
            "Device sangat panas",
            "Battery cepat habis",
            "Storage penuh",
        ],
        "first_response": (
            "Device kamu sepertinya ada issue. Mari kita diagnosa. 🔧\n\n"
            "Pertama, coba jawab:\n"
            "1. Device panas? Atau normal temp?\n"
            "2. Berapa persen battery habis?\n"
            "3. Storage masih ada berapa GB?"
        ),
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Check Resource Usage",
                "instructions": [
                    "Buka Settings → Battery → Usage",
                    "Lihat aplikasi mana yang paling banyak use battery",
                    "Buka Settings → Storage untuk lihat free space",
                ],
                "verification": "Ada memory leak atau storage penuh?"
            },
            {
                "step": 2,
                "title": "Force Stop dan Clear Cache",
                "instructions": [
                    "Settings → Apps → [nama app]",
                    "Tap 'Force Stop'",
                    "Tap 'Storage' → 'Clear Cache'",
                    "Buka app lagi",
                ],
                "verification": "Apakah app jalan lebih smooth?"
            },
            {
                "step": 3,
                "title": "Soft Reboot Device",
                "instructions": [
                    "Matikan device (power off)",
                    "Tunggu 30 detik",
                    "Nyalakan kembali",
                    "Tunggu hingga system fully boot (2-3 menit)",
                ],
                "verification": "Apakah sudah normal?"
            },
        ],
        "escalation_triggers": [
            "Device terus restart dalam boot loop",
            "Storage 0 byte tersedia",
            "Device panas > 50°C bahkan saat idle",
            "Battery drain 1% per menit",
        ],
        "workaround": (
            "Sementara tunggu fix:\n"
            "• Uninstall app yang tidak perlu\n"
            "• Matikan background sync\n"
            "• Charge device lebih sering\n"
            "• Gunakan alternative device jika ada"
        ),
    },

    # ========== APP ISSUES ==========
    "app": {
        "keywords": ["app", "aplikasi", "crash", "error", "force close", "bug", "tidak jalan", "error code"],
        "title": "Application & Software Issues",
        "symptoms": [
            "App force close",
            "Can't login",
            "Data tidak tersimpan",
            "Feature tidak berfungsi",
            "Blank screen",
        ],
        "first_response": (
            "Sepertinya ada bug di app. Jangan khawatir, itu bisa di-fix. 🐛\n\n"
            "Tolong kasih info:\n"
            "1. Kapan mulai error (baru install, setelah update, atau sudah lama)?\n"
            "2. Error apa yang keluar (ada error message)?"
        ),
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Check App Version & Update",
                "instructions": [
                    "Buka PlayStore/AppStore",
                    "Cari app TRAMOS",
                    "Lihat ada update? Kalo ada, install update",
                    "Buka app setelah update",
                ],
                "verification": "Apakah sudah update ke versi terbaru?"
            },
            {
                "step": 2,
                "title": "Clear App Data",
                "instructions": [
                    "Settings → Apps → TRAMOS",
                    "Tap 'Storage' → 'Clear Data'",
                    "⚠️ WARNING: Ini akan hapus login, settings, cached data",
                    "Buka app, login lagi",
                ],
                "verification": "Apakah masalah sudah hilang?"
            },
            {
                "step": 3,
                "title": "Reinstall App",
                "instructions": [
                    "Uninstall app (Settings → Apps → Uninstall)",
                    "Restart device",
                    "Download dan install app dari PlayStore/AppStore lagi",
                    "Login dan setup ulang",
                ],
                "verification": "Apakah app normal sekarang?"
            },
        ],
        "escalation_triggers": [
            "Error masih terjadi setelah update dan reinstall",
            "Error code tertentu (contoh: ERR_001, ERR_500)",
            "Feature tertentu tidak pernah bisa diakses",
        ],
        "workaround": (
            "Jika tetap error:\n"
            "• Gunakan web version (browser)\n"
            "• Update status lewat SMS/call\n"
            "• Gunakan device lain sementara"
        ),
    },

    # ========== TICKET CREATION ISSUES ==========
    "ticket": {
        "keywords": ["tiket", "ticket", "create", "buat", "support", "issue", "lapor"],
        "title": "Ticket Creation & Support",
        "symptoms": [
            "Tidak bisa buat tiket",
            "Tiket tidak tersimpan",
            "Tiket tidak masuk ke system",
            "Attachment upload gagal",
        ],
        "first_response": (
            "Mau buat tiket support? Mari saya bantu. 📝\n\n"
            "Sebelum buat tiket, coba dulu:\n"
            "1. Pastikan sudah disconnect dari semua network (refresh)\n"
            "2. Coba refresh app"
        ),
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Prepare Tiket Info",
                "instructions": [
                    "Siapkan info berikut:\n"
                    "  • Nomor unit/vehicle ID\n"
                    "  • Deskripsi masalah (jelas dan ringkas)\n"
                    "  • Screenshot jika ada error message\n"
                    "  • Waktu masalah terjadi"
                ],
                "verification": "Semua info sudah siap?"
            },
            {
                "step": 2,
                "title": "Create Tiket via App",
                "instructions": [
                    "Buka app TRAMOS",
                    "Tap 'Support' atau 'Report Issue'",
                    "Isi form dengan detail:\n"
                    "  - Category: pilih yang sesuai\n"
                    "  - Description: jelaskan masalahnya\n"
                    "  - Attachment: upload screenshot jika ada",
                    "Tap 'Submit'",
                ],
                "verification": "Tiket berhasil tersubmit (ada confirmation)?"
            },
            {
                "step": 3,
                "title": "Confirm Tiket Masuk System",
                "instructions": [
                    "Cek email - harusnya ada confirmation email",
                    "Lihat nomor tiket di email tersebut",
                    "Save nomor tiket untuk tracking",
                ],
                "verification": "Sudah terima email confirmation?"
            },
        ],
        "escalation_triggers": [
            "Form tidak bisa di-submit (greyed out button)",
            "Submit tapi error, tidak ada confirmation",
            "Tidak terima email confirmation setelah 5 menit",
        ],
        "workaround": (
            "Jika app tidak bisa buat tiket:\n"
            "• Hubungi Dispatch via Phone\n"
            "• Send email ke support@tramos.io\n"
            "• Kirim SMS dengan keyword: TICKET [description]\n"
            "• Gunakan web portal (browser)"
        ),
    },
}

# Escalation decision tree
ESCALATION_RULES = {
    "immediate_escalate": [
        "Device terus restart (boot loop)",
        "Tidak bisa login sama sekali",
        "Data hilang",
        "Security issue atau hack",
        "Vehicle stopped (GPS stationary > 2 jam di middle of nowhere)",
    ],
    "escalate_if_unresolved": [
        "Masalah persist > 30 menit setelah troubleshooting",
        "User sudah coba semua steps, masih error",
        "Multiple systems affected",
    ],
    "low_priority": [
        "UI cosmetic issues",
        "Minor feature not working",
        "Slow performance (but functional)",
    ],
}

# Natural language response templates
DIALOG_TEMPLATES = {
    "greeting": [
        "Halo 👋 Ada apa kami bisa bantu?",
        "Selamat pagi! Apa yang perlu kami bantu?",
        "Hi! Cerita dong, ada masalah apa?",
    ],
    "understanding": [
        "Saya mengerti, ini pasti frustasi. Mari kita selesaikan step by step. ✅",
        "Oke, saya paham. Jangan khawatir, ini umum terjadi. 💪",
        "Gotcha! Ini bisa kita fix. Ikuti langkah-langkah ini:",
    ],
    "progress": [
        "Bagus! Ini sudah langkah maju. Lanjut ke step berikutnya...",
        "Perfect! Step pertama berhasil. Sekarang coba ini:",
        "Excellent! Kita sudah maju. Mari lanjut...",
    ],
    "success": [
        "Yay! Masalah sudah selesai! 🎉 Terima kasih sudah sabar.",
        "Perfect! Semuanya normal sekarang. Jika ada pertanyaan, tanya saja!",
        "Berhasil! Masalah sudah solved. Keep safe on the road! 🚗",
    ],
    "escalation": [
        "Saya lihat ini butuh bantuan lebih lanjut. Saya hubungi tim support untuk kamu. Tunggu sebentar ya...",
        "Ini di luar troubleshooting standar. Aku connect kamu sama tech team. Hold on...",
        "Oke, ini case yang butuh expert. Aku forward ke senior support sekarang.",
    ],
}


def get_kb_category(keywords: list) -> dict:
    """Find KB category based on keywords"""
    for category, kb_data in KB_TROUBLESHOOTING.items():
        if any(kw in keywords for kw in kb_data["keywords"]):
            return {"category": category, **kb_data}
    return None


def get_escalation_status(symptoms: list) -> str:
    """Determine if issue needs escalation"""
    for symptom in symptoms:
        if symptom in ESCALATION_RULES["immediate_escalate"]:
            return "IMMEDIATE"
        if symptom in ESCALATION_RULES["escalate_if_unresolved"]:
            return "PENDING"
    return "STANDARD"
