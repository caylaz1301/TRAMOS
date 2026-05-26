"""
Knowledge Base - Troubleshooting Database (COMPLETE)

This KB now contains FULL troubleshooting content per category:
- first_response: Initial acknowledgment message
- troubleshooting_steps: Step-by-step solution guide
- workaround: Temporary fix if main steps fail
- escalation_triggers: When to escalate to human support

The AI system uses these as fallback when Ollama/LLM is unavailable,
and as context-enrichment when LLM IS available.
"""

from typing import Optional, List

KB_TROUBLESHOOTING = {
    # ========== GPS & TRACKING ISSUES ==========
    "gps": {
        "category_id": "gps",
        "title": "GPS & Tracking Issues",
        "keywords": [
            "gps", "lokasi", "location", "tracking", "posisi", "signal",
            "sinyal", "gps mati", "gps error", "positioning", "peta",
            "map", "koordinat", "navigate", "track", "tidak ketemu",
            "hilang", "loss", "gps ga akurat", "posisi salah", "titik",
            "maps", "geolocation", "lat", "lng", "longitude", "latitude",
            "arah", "heading", "jalur", "rute", "route", "geser",
            "meleset", "ga muncul", "tidak muncul di peta", "blank map",
            "tidak terlacak", "ga ketemu lokasinya", "dimana", "ga nyala gps"
        ],
        "description": "Device GPS signal, location accuracy, and real-time tracking issues",
        "symptoms": [
            "GPS tidak akurat",
            "Lokasi tidak update",
            "GPS signal lemah",
            "Device tidak terdeteksi",
            "Heading incorrect",
            "Signal loss",
        ],
        "first_response": "Baik, saya lihat ada masalah dengan GPS/tracking. Mari kita coba perbaiki step by step 📍",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Cek posisi device",
                "instruction": "Pastikan device GPS berada di area terbuka (outdoor). Sinyal GPS tidak bisa menembus gedung atau atap tebal. Pindahkan ke area yang bisa 'melihat langit' langsung.",
                "verification": "Tunggu 2-3 menit. Cek apakah indikator GPS sudah menunjukkan sinyal (biasanya ada ikon satelit).",
            },
            {
                "step": 2,
                "title": "Restart device tracking",
                "instruction": "Matikan device GPS sepenuhnya. Tunggu 30 detik. Nyalakan kembali dan tunggu hingga boot sempurna (biasanya 1-2 menit).",
                "verification": "Setelah restart, cek apakah lokasi di app TRAMOS sudah terupdate dengan benar.",
            },
            {
                "step": 3,
                "title": "Cek koneksi internet device",
                "instruction": "GPS butuh internet untuk mengirim data lokasi ke server. Pastikan SIM card aktif dan ada sinyal data (4G/3G). Coba buka browser di device untuk tes koneksi.",
                "verification": "Jika internet OK tapi lokasi tetap tidak update, masalahnya di modul GPS hardware.",
            },
            {
                "step": 4,
                "title": "Reset lokasi di aplikasi",
                "instruction": "Buka aplikasi TRAMOS → Settings → Location → Reset GPS. Atau coba logout dan login ulang dari aplikasi.",
                "verification": "Setelah reset, lokasi seharusnya terupdate dalam 2-5 menit.",
            },
        ],
        "workaround": "Jika semua langkah gagal, catat koordinat secara manual dan laporkan ke tim support untuk pengecekan hardware GPS.",
        "escalation_triggers": [
            "GPS antenna hardware rusak",
            "Setelah restart sinyal tetap 0",
            "Lokasi selalu salah lebih dari 500 meter",
        ],
        "metadata": {
            "typical_resolution_time": "10-15 minutes",
            "technical_difficulty": "medium",
            "common_root_causes": ["hardware_antenna", "software_config", "environmental", "network"],
            "requires_hardware_access": True,
            "data_loss_risk": False,
        },
    },

    # ========== CONNECTIVITY ISSUES ==========
    "connectivity": {
        "category_id": "connectivity",
        "title": "Internet & Network Connectivity",
        "keywords": [
            "internet", "signal", "connection", "offline", "tidak connect",
            "connection failed", "koneksi", "jaringan", "network", "wifi",
            "putus", "disconnect", "timeout", "sync", "lelet", "lambat",
            "slow", "lemot", "lag", "buffering", "loading", "no connection"
        ],
        "description": "Device internet connectivity, mobile data, and server communication issues",
        "symptoms": [
            "Tidak bisa connect ke server",
            "Data tidak tersinkronisasi",
            "Signal lemah",
            "Timeout error",
            "Intermittent connection",
        ],
        "first_response": "Saya paham koneksi bermasalah. Mari kita diagnosa dan perbaiki koneksinya 📡",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Cek kualitas sinyal",
                "instruction": "Lihat indikator sinyal di device. Minimal 2 bar untuk koneksi data yang stabil. Jika kurang, coba pindah ke lokasi dengan sinyal lebih baik.",
                "verification": "Sinyal minimal 2 bar dan stabil (tidak naik-turun terus).",
            },
            {
                "step": 2,
                "title": "Toggle mode pesawat",
                "instruction": "Aktifkan mode pesawat (Airplane Mode) selama 10 detik, lalu matikan kembali. Ini akan mereset koneksi jaringan.",
                "verification": "Setelah toggle, device harusnya reconnect ke jaringan dalam 15-30 detik.",
            },
            {
                "step": 3,
                "title": "Restart koneksi data",
                "instruction": "Matikan WiFi dan Mobile Data. Tunggu 10 detik. Nyalakan Mobile Data kembali. Jika pakai WiFi, lupakan jaringan WiFi lalu connect ulang.",
                "verification": "Coba buka browser atau app TRAMOS untuk test koneksi.",
            },
            {
                "step": 4,
                "title": "Cek pengaturan APN",
                "instruction": "Buka Settings → Mobile Network → APN. Pastikan APN sesuai provider (contoh: Telkomsel=internet, XL=internet, Indosat=indosatooredoo). Reset ke default jika ragu.",
                "verification": "Setelah set APN, restart device dan tes koneksi.",
            },
        ],
        "workaround": "Jika internet device bermasalah, coba tethering/hotspot dari HP pribadi untuk sementara.",
        "escalation_triggers": [
            "SIM card tidak terdeteksi",
            "Semua APN sudah dicoba tapi tetap tidak connect",
            "Server TRAMOS down (semua user mengalami masalah)",
        ],
        "metadata": {
            "typical_resolution_time": "5-10 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["network_config", "signal_strength", "server_issue", "device_settings"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== CAMERA ISSUES ==========
    "camera": {
        "category_id": "camera",
        "title": "Camera & Video Recording Issues",
        "keywords": [
            "kamera", "camera", "video", "rekam", "recording", "feed",
            "video feed", "display", "preview", "black screen", "blur",
            "fokus", "exposure", "dashcam", "cctv", "cam", "tidak jelas",
            "video hitam", "tampilan", "screen"
        ],
        "description": "Device camera hardware issues, video recording failures, live streaming problems",
        "symptoms": [
            "Kamera tidak berfungsi",
            "Video blur/tidak jelas",
            "Gambar hitam atau tidak ada feed",
            "Recording gagal",
            "Fokus tidak berfungsi",
            "Camera crash",
        ],
        "first_response": "Ada masalah dengan kamera/recording. Mari kita cek satu-satu 📹",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Periksa fisik kamera",
                "instruction": "Bersihkan lensa kamera dengan kain lembut. Pastikan tidak ada debu, air, atau noda yang menghalangi. Cek apakah kabel power kamera terhubung dengan baik.",
                "verification": "Lensa bersih dan kabel terpasang kuat.",
            },
            {
                "step": 2,
                "title": "Power cycle kamera",
                "instruction": "Cabut kabel power kamera selama 1-2 menit. Pasang kembali dengan hati-hati. Tunggu sampai kamera fully boot (LED indikator menyala normal).",
                "verification": "LED kamera menyala normal (biasanya hijau = OK, merah = error).",
            },
            {
                "step": 3,
                "title": "Cek storage dan permission",
                "instruction": "Pastikan storage device masih cukup (minimal 10% free). Cek apakah permission kamera sudah diberikan di app settings.",
                "verification": "Coba record video pendek (30 detik) dan playback hasilnya.",
            },
            {
                "step": 4,
                "title": "Reset pengaturan kamera",
                "instruction": "Buka Settings → Camera/Video → Reset to Default. Ini akan mengembalikan semua pengaturan kamera ke bawaan pabrik.",
                "verification": "Setelah reset, tes record video lagi.",
            },
        ],
        "workaround": "Jika kamera utama bermasalah dan ada kamera cadangan, gunakan kamera cadangan sambil menunggu perbaikan.",
        "escalation_triggers": [
            "Kamera tidak terdeteksi sama sekali setelah restart",
            "Hardware kamera fisik rusak (retak, pecah)",
            "Semua langkah troubleshooting gagal",
        ],
        "metadata": {
            "typical_resolution_time": "10-20 minutes",
            "technical_difficulty": "medium",
            "common_root_causes": ["lens_dirty", "app_bug", "permission_denied", "hardware_failure"],
            "requires_hardware_access": True,
            "data_loss_risk": False,
        },
    },

    # ========== DEVICE ISSUES ==========
    "device": {
        "category_id": "device",
        "title": "Device Hardware & Software Issues",
        "keywords": [
            "device", "crash", "freeze", "restart", "reboot", "boot",
            "not responding", "error", "device tidak mau", "panas",
            "overheat", "hang", "lemot", "lag", "mati", "hardware",
            "baterai", "battery", "power", "charge", "listrik", "aki",
            "voltage", "habis", "tidak menyala", "charging"
        ],
        "description": "Device hardware failures, software crashes, battery and power issues",
        "symptoms": [
            "Device restart sendiri",
            "App freeze/hang",
            "Device sangat panas",
            "Battery cepat habis",
            "Storage penuh",
            "Not responding",
        ],
        "first_response": "Saya catat ada masalah dengan device. Mari kita troubleshoot 🔧",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Restart device sepenuhnya",
                "instruction": "Matikan device sepenuhnya (bukan sleep). Tunggu 1 menit penuh. Nyalakan kembali. Tunggu sampai fully booted sebelum melakukan apapun.",
                "verification": "Setelah restart, cek apakah masalah masih terjadi.",
            },
            {
                "step": 2,
                "title": "Cek status baterai",
                "instruction": "Lihat persentase baterai. Jika di bawah 20%, charge dulu sebelum troubleshoot lebih lanjut. Pastikan charger yang digunakan original atau kompatibel.",
                "verification": "Baterai minimal 20% dan charging indicator muncul saat di-charge.",
            },
            {
                "step": 3,
                "title": "Bersihkan storage dan cache",
                "instruction": "Buka Settings → Storage. Hapus file/cache yang tidak perlu. Minimal tersisa 10% storage. Clear cache aplikasi TRAMOS: Settings → Apps → TRAMOS → Clear Cache.",
                "verification": "Storage tersisa minimal 10% dari total.",
            },
            {
                "step": 4,
                "title": "Cek suhu device",
                "instruction": "Jika device terasa panas, matikan dan biarkan dingin selama 10-15 menit. Jauhkan dari sinar matahari langsung. Lepas casing jika ada.",
                "verification": "Device terasa normal (tidak panas) saat dihidupkan ulang.",
            },
        ],
        "workaround": "Jika device bermasalah parah, gunakan HP pribadi untuk melaporkan status ke dispatch center sementara.",
        "escalation_triggers": [
            "Device sama sekali tidak mau nyala",
            "Layar rusak/retak",
            "Device overheat berulang kali",
            "Baterai kembung/bengkak",
        ],
        "metadata": {
            "typical_resolution_time": "15-20 minutes",
            "technical_difficulty": "medium",
            "common_root_causes": ["memory_leak", "storage_full", "thermal_issue", "software_bug"],
            "requires_hardware_access": True,
            "data_loss_risk": True,
        },
    },

    # ========== VEHICLE BREAKDOWN ISSUES ==========
    "vehicle": {
        "category_id": "vehicle",
        "title": "Vehicle Breakdown & Engine Issues",
        "keywords": [
            "mogok", "stall", "breakdown", "mesin mati", "mesin tidak hidup",
            "engine stop", "tidak mau hidup", "mobil mogok", "truk mogok",
            "engine", "kendaraan", "ban", "rem", "oli", "bensin", "solar"
        ],
        "description": "Vehicle mechanical failures, engine issues, breakdown on road",
        "symptoms": [
            "Kendaraan mogok/stall di jalan",
            "Mesin mati tiba-tiba",
            "Mesin tidak bisa di-start",
            "Performa mesin menurun",
            "Suara mesin aneh",
            "Smoke atau leak",
        ],
        "first_response": "Kendaraan mogok bisa berbahaya! Pastikan Anda sudah aman dulu, lalu kita bantu 🚗",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Pastikan keselamatan",
                "instruction": "⚠️ PENTING: Nyalakan lampu hazard. Jika di jalan, pindahkan kendaraan ke bahu jalan atau area aman. Pasang segitiga pengaman jika ada. Jangan keluar kendaraan di jalan tol.",
                "verification": "Kendaraan sudah di posisi aman dan lampu hazard menyala.",
            },
            {
                "step": 2,
                "title": "Cek indikator dashboard",
                "instruction": "Lihat warning light di dashboard. Catat lampu apa saja yang menyala (merah = kritis, kuning = peringatan). Cek indikator bahan bakar, suhu mesin, dan tekanan oli.",
                "verification": "Apakah ada warning light yang menyala? Bahan bakar masih ada?",
            },
            {
                "step": 3,
                "title": "Coba start ulang mesin",
                "instruction": "Matikan semua aksesoris (AC, radio, lampu). Tunggu 30 detik. Coba start mesin. Jika mesin bersuara tapi tidak hidup, mungkin masalah bahan bakar. Jika tidak bersuara sama sekali, kemungkinan aki/starter.",
                "verification": "Mesin berhasil hidup atau tidak? Jika hidup, biarkan idle 2-3 menit.",
            },
            {
                "step": 4,
                "title": "Cek dasar-dasar mesin",
                "instruction": "Buka kap mesin (hati-hati jika masih panas). Cek: (1) Level air radiator, (2) Level oli mesin, (3) Kondisi aki (terminal kencang?), (4) Ada kebocoran cairan?",
                "verification": "Semua level cairan normal dan tidak ada kebocoran.",
            },
            {
                "step": 5,
                "title": "Hubungi derek/mekanik",
                "instruction": "Jika langkah di atas tidak berhasil, segera hubungi layanan derek atau mekanik terdekat. Catat lokasi persis kendaraan dan nomor plat untuk mempermudah evakuasi.",
                "verification": "Derek/mekanik sudah dihubungi dan sedang menuju lokasi.",
            },
        ],
        "workaround": "Jangan paksa menghidupkan mesin berulang kali jika tidak berhasil — bisa merusak starter. Hubungi dispatch center untuk bantuan evakuasi.",
        "escalation_triggers": [
            "Kendaraan di jalan tol tanpa bahu jalan",
            "Ada asap atau api dari mesin",
            "Kondisi darurat keselamatan",
            "Kendaraan bermuatan barang berharga",
        ],
        "metadata": {
            "typical_resolution_time": "30-60 minutes",
            "technical_difficulty": "high",
            "common_root_causes": ["fuel_issue", "battery_dead", "engine_failure", "transmission"],
            "requires_hardware_access": True,
            "data_loss_risk": False,
            "critical": True,
        },
    },

    # ========== APP ISSUES ==========
    "app": {
        "category_id": "app",
        "title": "Application & Software Issues",
        "keywords": [
            "app", "aplikasi", "crash", "error", "force close", "bug",
            "tidak jalan", "error code", "login", "blank screen", "update",
            "software", "hang", "freeze"
        ],
        "description": "Application crashes, login failures, feature bugs, data sync issues",
        "symptoms": [
            "App force close",
            "Can't login",
            "Data tidak tersimpan",
            "Feature tidak berfungsi",
            "Blank screen",
            "Connection error",
        ],
        "first_response": "Ada masalah dengan aplikasi. Mari kita perbaiki 📱",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Force close dan buka ulang",
                "instruction": "Tutup aplikasi sepenuhnya (swipe up dari recent apps, jangan hanya tekan back). Tunggu 5 detik. Buka lagi aplikasi TRAMOS.",
                "verification": "Apakah app sudah bisa dibuka normal tanpa crash?",
            },
            {
                "step": 2,
                "title": "Clear cache aplikasi",
                "instruction": "Buka Settings → Apps → TRAMOS → Storage → Clear Cache (BUKAN Clear Data). Ini menghapus file sementara tanpa menghapus data penting.",
                "verification": "Buka app lagi, cek apakah masalah masih ada.",
            },
            {
                "step": 3,
                "title": "Cek update aplikasi",
                "instruction": "Buka Play Store/App Store → cari TRAMOS → cek apakah ada update tersedia. Jika ada, update ke versi terbaru.",
                "verification": "Versi aplikasi sudah yang terbaru.",
            },
            {
                "step": 4,
                "title": "Reinstall aplikasi",
                "instruction": "Jika semua langkah gagal, uninstall aplikasi TRAMOS. Install ulang dari Play Store/App Store. Login kembali dengan akun yang sama.",
                "verification": "App terinstall fresh dan bisa login normal.",
            },
        ],
        "workaround": "Jika app masih bermasalah setelah reinstall, coba akses TRAMOS lewat browser (web version) sebagai alternatif.",
        "escalation_triggers": [
            "Error code spesifik yang tidak dikenal",
            "Masalah hanya terjadi pada akun tertentu",
            "Bug pada fitur yang baru di-update",
        ],
        "metadata": {
            "typical_resolution_time": "5-15 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["app_bug", "outdated_version", "corrupted_cache", "server_issue"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== BILLING ISSUES ==========
    "billing": {
        "category_id": "billing",
        "title": "Billing & Payment Issues",
        "keywords": [
            "tagihan", "invoice", "billing", "biaya", "charge", "bayar",
            "pembayaran", "transaksi", "harga", "mahal", "payment"
        ],
        "description": "Issues related to billing, invoices, and payment processing",
        "symptoms": [
            "Tagihan tidak sesuai",
            "Invoice tidak diterima",
            "Pembayaran gagal",
            "Double charge",
        ],
        "first_response": "Saya bantu terkait masalah billing/tagihan. Mari kita cek 💳",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Cek detail tagihan",
                "instruction": "Buka menu Billing/Tagihan di app atau portal TRAMOS. Periksa periode tagihan, item yang dicharge, dan total amount. Screenshot jika ada ketidaksesuaian.",
                "verification": "Sudah bisa melihat detail tagihan yang bermasalah?",
            },
            {
                "step": 2,
                "title": "Bandingkan dengan kontrak",
                "instruction": "Cek kembali kontrak/perjanjian layanan Anda. Bandingkan tarif yang tertera di kontrak dengan tagihan aktual.",
                "verification": "Apakah ada perbedaan antara tarif kontrak dan tagihan?",
            },
            {
                "step": 3,
                "title": "Laporkan ke finance team",
                "instruction": "Jika ada ketidaksesuaian, siapkan bukti (screenshot tagihan + kontrak). Tim finance akan kami hubungi untuk pengecekan.",
                "verification": "Bukti siap untuk dilampirkan ke laporan.",
            },
        ],
        "workaround": "Sementara menunggu pengecekan billing, layanan Anda tetap aktif. Tidak ada pemblokiran selama proses dispute.",
        "escalation_triggers": [
            "Double charge confirmed",
            "Tagihan sangat berbeda dari kontrak",
            "Layanan diblokir karena billing issue",
        ],
        "metadata": {
            "typical_resolution_time": "1-2 business days",
            "technical_difficulty": "easy",
            "common_root_causes": ["system_error", "contract_mismatch", "proration", "duplicate_charge"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== TICKET/SUPPORT ISSUES ==========
    "ticket": {
        "category_id": "ticket",
        "title": "Ticket Creation & Support",
        "keywords": [
            "tiket", "ticket", "create", "buat", "support", "issue",
            "lapor", "report", "help", "bantuan"
        ],
        "description": "Assistance with creating support tickets and getting help",
        "symptoms": [
            "Tidak bisa buat tiket",
            "Tiket tidak tersimpan",
            "Tiket tidak masuk ke system",
            "Support tidak respond",
        ],
        "first_response": "Saya bantu buatkan tiket support. Saya butuh beberapa informasi dari Anda 📝",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Kumpulkan informasi",
                "instruction": "Siapkan: (1) Deskripsi masalah yang jelas, (2) Nama unit/kendaraan, (3) Lokasi saat ini, (4) Waktu kejadian.",
                "verification": "Semua informasi sudah lengkap.",
            },
            {
                "step": 2,
                "title": "Buat tiket via chatbot",
                "instruction": "Ikuti panduan chatbot TRAMOS untuk membuat tiket. Jawab setiap pertanyaan dengan lengkap agar tim support bisa membantu lebih cepat.",
                "verification": "Tiket berhasil dibuat dan Anda mendapat nomor tiket.",
            },
        ],
        "workaround": "Jika chatbot bermasalah, kirim email ke support@tramos.id dengan detail masalah Anda.",
        "escalation_triggers": [
            "System tiket down",
            "Tiket urgent tidak direspon lebih dari 2 jam",
        ],
        "metadata": {
            "typical_resolution_time": "5 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["form_error", "network_issue", "server_maintenance"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== MAINTENANCE / PERAWATAN RUTIN ==========
    "maintenance": {
        "category_id": "maintenance",
        "title": "Pemeliharaan & Perawatan Rutin",
        "keywords": [
            "maintenance", "perawatan", "servis", "service", "jadwal",
            "berkala", "oli", "ban", "tire", "rutin", "inspeksi",
            "tune up", "km", "kilometer", "jarak tempuh", "reminder",
            "pengingat", "cek rutin", "schedule", "jadwal servis",
            "ganti oli", "filter", "radiator", "coolant", "rem", "brake",
            "wiper", "lampu", "light", "aki", "battery", "accu"
        ],
        "description": "Jadwal perawatan kendaraan, servis berkala, dan reminder maintenance",
        "symptoms": [
            "Jadwal servis terlewat",
            "Reminder maintenance tidak muncul",
            "Tidak tahu kapan servis berikutnya",
            "Odometer tidak terupdate",
            "Riwayat servis hilang",
        ],
        "first_response": "Baik, saya bantu terkait perawatan kendaraan. Mari kita cek jadwal dan kebutuhan maintenance-nya 🔧",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Cek jadwal servis di sistem",
                "instruction": "Buka aplikasi TRAMOS → Menu Kendaraan → Pilih unit → Tab 'Maintenance'. Lihat jadwal servis berikutnya berdasarkan kilometer atau waktu.",
                "verification": "Jadwal servis terbaru terlihat di layar.",
            },
            {
                "step": 2,
                "title": "Perbarui data odometer",
                "instruction": "Jika jarak tempuh tidak otomatis terupdate dari GPS, input manual: Kendaraan → Update Odometer → Masukkan km terbaru.",
                "verification": "Angka km di sistem sudah sesuai dengan speedometer kendaraan.",
            },
            {
                "step": 3,
                "title": "Aktifkan reminder otomatis",
                "instruction": "Masuk ke Settings → Notifications → Aktifkan 'Maintenance Reminder'. Set interval pengingat: 7 hari, 3 hari, dan 1 hari sebelum jadwal.",
                "verification": "Notifikasi test diterima di WhatsApp.",
            },
            {
                "step": 4,
                "title": "Catat riwayat servis terbaru",
                "instruction": "Setelah servis selesai, input di TRAMOS: Kendaraan → Riwayat Servis → Tambah Record. Isi: tanggal, jenis servis, biaya, bengkel.",
                "verification": "Record servis muncul di riwayat kendaraan.",
            },
        ],
        "workaround": "Catat jadwal servis secara manual dan hubungi koordinator fleet untuk penjadwalan ulang.",
        "escalation_triggers": [
            "Kendaraan sudah sangat overdue servis (>2000 km dari jadwal)",
            "Ada bunyi tidak normal dari mesin/rem",
            "Warning light menyala di dashboard kendaraan",
        ],
        "metadata": {
            "typical_resolution_time": "5-10 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["missed_schedule", "odometer_error", "notification_off"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== SENSOR & IoT DEVICE ISSUES ==========
    "sensor": {
        "category_id": "sensor",
        "title": "Sensor & IoT Device",
        "keywords": [
            "sensor", "iot", "suhu", "temperature", "fuel", "bbm",
            "bensin", "solar", "bahan bakar", "level", "tangki", "tank",
            "odometer", "speed", "kecepatan", "rpm", "door",
            "pintu", "segel", "seal", "geofence", "geo fence", "zona",
            "alert", "notifikasi", "alarm", "buzzer", "panic", "sos",
            "ibutton", "rfid", "driver id", "accelerometer", "getaran",
            "vibration", "tilt", "kemiringan"
        ],
        "description": "Sensor IoT pada kendaraan: fuel sensor, temperature, door, geofence, dll",
        "symptoms": [
            "Sensor fuel tidak akurat",
            "Data suhu tidak muncul",
            "Alert geofence tidak berfungsi",
            "Sensor pintu selalu open/close",
            "Driver ID tidak terdeteksi",
            "Alarm tidak berbunyi",
        ],
        "first_response": "Saya bantu troubleshoot masalah sensor. Mari kita identifikasi dan perbaiki 📊",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Identifikasi sensor bermasalah",
                "instruction": "Buka TRAMOS → Kendaraan → Detail Unit → Tab 'Sensor'. Cek status setiap sensor: Hijau (OK), Kuning (Warning), Merah (Error).",
                "verification": "Sensor yang bermasalah sudah teridentifikasi dari indikator warna.",
            },
            {
                "step": 2,
                "title": "Cek koneksi fisik sensor",
                "instruction": "Pastikan kabel sensor terpasang dengan baik ke terminal device. Cek apakah ada kabel yang longgar, terputus, atau teroksidasi (berkarat).",
                "verification": "Koneksi kabel sudah kencang dan bersih.",
            },
            {
                "step": 3,
                "title": "Kalibrasi ulang sensor",
                "instruction": "Untuk fuel sensor: isi tangki penuh → catat pembacaan → kuras sebagian → catat lagi. Kirim data kalibrasi ke tim teknis. Untuk sensor lain: restart device dan tunggu 5 menit.",
                "verification": "Pembacaan sensor sudah mendekati nilai aktual (toleransi ±5%).",
            },
            {
                "step": 4,
                "title": "Reset konfigurasi sensor di server",
                "instruction": "Hubungi admin untuk reset parameter sensor dari server. Berikan info: ID kendaraan, jenis sensor, dan gejala masalah.",
                "verification": "Data sensor sudah terupdate dan akurat di dashboard.",
            },
        ],
        "workaround": "Gunakan metode manual (stik ukur untuk fuel, thermometer untuk suhu) sambil menunggu perbaikan sensor.",
        "escalation_triggers": [
            "Sensor fisik rusak/pecah",
            "Kabel terputus tidak bisa disambung",
            "Butuh penggantian hardware sensor",
            "Data sensor sangat jauh dari realita (>20% deviasi)",
        ],
        "metadata": {
            "typical_resolution_time": "15-30 minutes",
            "technical_difficulty": "high",
            "common_root_causes": ["wiring", "calibration", "hardware_failure", "water_damage"],
            "requires_hardware_access": True,
            "data_loss_risk": False,
        },
    },

    # ========== DRIVER BEHAVIOR & MANAGEMENT ==========
    "driver": {
        "category_id": "driver",
        "title": "Driver & Perilaku Pengemudi",
        "keywords": [
            "driver", "pengemudi", "sopir", "supir", "perilaku", "behavior",
            "ngebut", "speeding", "harsh", "braking", "rem mendadak",
            "belok tajam", "cornering", "idle", "diam", "parkir lama",
            "sim", "lisensi", "licence", "skor", "score", "rating",
            "pelanggaran", "violation", "fatigue", "ngantuk", "capek",
            "lelah", "jam kerja", "overtime", "shift", "jadwal driver",
            "absen", "kehadiran", "attendance", "ibutton", "rfid"
        ],
        "description": "Monitoring perilaku pengemudi, skor keselamatan, dan manajemen shift driver",
        "symptoms": [
            "Skor driver turun drastis",
            "Alert speeding terus menerus",
            "Driver ID tidak terdeteksi",
            "Jam kerja melebihi batas",
            "Riwayat pelanggaran tidak muncul",
        ],
        "first_response": "Baik, saya bantu terkait manajemen driver dan perilaku pengemudi. Mari kita cek data yang tersedia 🚗",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Cek profil driver di sistem",
                "instruction": "Buka TRAMOS → Menu Driver → Cari nama driver. Lihat skor keselamatan, jumlah pelanggaran, dan status SIM.",
                "verification": "Profil driver muncul dengan data lengkap.",
            },
            {
                "step": 2,
                "title": "Review riwayat pelanggaran",
                "instruction": "Di profil driver, buka tab 'Pelanggaran'. Filter berdasarkan tanggal. Cek jenis pelanggaran: speeding, harsh braking, idle time berlebihan.",
                "verification": "Daftar pelanggaran terlihat dengan detail waktu dan lokasi.",
            },
            {
                "step": 3,
                "title": "Cek konfigurasi alert",
                "instruction": "Masuk ke Settings → Alert Rules → Driver. Pastikan threshold sudah benar: batas kecepatan, durasi idle, jam kerja maksimal.",
                "verification": "Alert threshold sesuai dengan kebijakan perusahaan.",
            },
            {
                "step": 4,
                "title": "Verifikasi device identifikasi driver",
                "instruction": "Pastikan iButton/RFID driver terdaftar di sistem. Cek di Kendaraan → Driver Assignment → Test scan iButton.",
                "verification": "Driver ID terdeteksi dan terhubung ke profil yang benar.",
            },
        ],
        "workaround": "Catat pelanggaran secara manual dari laporan harian sambil menunggu konfigurasi sistem diperbaiki.",
        "escalation_triggers": [
            "Driver terlibat kecelakaan",
            "Jam kerja melebihi regulasi (>12 jam)",
            "Skor keselamatan di bawah 40%",
        ],
        "metadata": {
            "typical_resolution_time": "5-10 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["config_threshold", "driver_id_unregistered", "device_malfunction"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== REPORT & DATA EXPORT ==========
    "report": {
        "category_id": "report",
        "title": "Laporan & Export Data",
        "keywords": [
            "laporan", "report", "export", "download", "unduh", "pdf",
            "excel", "csv", "print", "cetak", "riwayat", "history",
            "log", "data", "statistik", "grafik", "chart", "analisis",
            "ringkasan", "summary", "rekapitulasi", "rekap", "bulanan",
            "mingguan", "harian", "daily", "weekly", "monthly",
            "kilometer", "perjalanan", "trip", "journey", "fuel report"
        ],
        "description": "Pembuatan laporan, export data, dan analisis riwayat perjalanan",
        "symptoms": [
            "Laporan tidak bisa di-download",
            "Data di laporan tidak akurat",
            "Export ke Excel gagal",
            "Grafik tidak muncul",
            "Filter tanggal tidak berfungsi",
        ],
        "first_response": "Saya bantu terkait laporan dan export data. Mari kita cek kebutuhannya 📋",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Pilih jenis laporan",
                "instruction": "Buka TRAMOS → Menu Laporan. Pilih jenis: Trip Report, Fuel Report, Driver Report, atau Summary Report. Tentukan periode tanggal yang diinginkan.",
                "verification": "Halaman laporan terbuka dengan filter yang benar.",
            },
            {
                "step": 2,
                "title": "Generate laporan",
                "instruction": "Setelah filter diisi, klik 'Generate'. Tunggu proses pengambilan data (bisa 10-30 detik untuk data besar). Jika timeout, perkecil range tanggal.",
                "verification": "Data laporan muncul di layar dalam format tabel.",
            },
            {
                "step": 3,
                "title": "Export ke format yang diinginkan",
                "instruction": "Klik tombol Export → pilih format (PDF, Excel, CSV). Untuk PDF pastikan browser mengizinkan popup. Untuk Excel pastikan ukuran file tidak terlalu besar (<50MB).",
                "verification": "File berhasil ter-download ke komputer.",
            },
            {
                "step": 4,
                "title": "Validasi data laporan",
                "instruction": "Buka file yang sudah di-download. Cross-check beberapa data sample dengan data live di aplikasi. Pastikan kolom dan angka sesuai.",
                "verification": "Data di file export cocok dengan data di aplikasi.",
            },
        ],
        "workaround": "Screenshot data dari layar atau copy-paste ke spreadsheet secara manual jika export tidak berfungsi.",
        "escalation_triggers": [
            "Data hilang dari laporan (gap data >1 jam)",
            "Server timeout saat generate laporan besar",
            "Data laporan sangat berbeda dengan kenyataan",
        ],
        "metadata": {
            "typical_resolution_time": "5-10 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["browser_popup_blocked", "large_data_range", "server_timeout"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },

    # ========== ACCOUNT & ACCESS ==========
    "account": {
        "category_id": "account",
        "title": "Akun & Akses",
        "keywords": [
            "login", "password", "kata sandi", "sandi", "akun", "account",
            "masuk", "daftar", "register", "lupa password", "reset",
            "ganti password", "profil", "profile", "hak akses", "permission",
            "role", "admin", "user", "operator", "logout", "keluar",
            "session", "expired", "kadaluarsa", "token", "otentikasi",
            "otp", "verifikasi", "email", "aktivasi", "blocked", "diblokir"
        ],
        "description": "Manajemen akun pengguna, login, password, dan hak akses",
        "symptoms": [
            "Tidak bisa login",
            "Password lupa",
            "Akun terkunci/blocked",
            "Session expired terus",
            "Tidak punya akses ke fitur tertentu",
        ],
        "first_response": "Saya bantu terkait akun dan akses. Mari kita selesaikan masalahnya 🔐",
        "troubleshooting_steps": [
            {
                "step": 1,
                "title": "Verifikasi kredensial login",
                "instruction": "Pastikan username dan password diketik dengan benar. Cek Caps Lock mati. Username biasanya format: nama.belakang atau email.",
                "verification": "Login berhasil setelah memasukkan kredensial yang benar.",
            },
            {
                "step": 2,
                "title": "Reset password",
                "instruction": "Jika lupa password: Klik 'Lupa Password' di halaman login → masukkan email terdaftar → cek inbox (dan spam folder) → ikuti link reset → buat password baru minimal 8 karakter.",
                "verification": "Password berhasil di-reset dan bisa login dengan password baru.",
            },
            {
                "step": 3,
                "title": "Cek status akun",
                "instruction": "Hubungi admin untuk cek apakah akun masih aktif. Akun bisa di-nonaktifkan jika: terlalu banyak salah login (>5x), masa kontrak habis, atau dihapus admin.",
                "verification": "Admin mengkonfirmasi status akun aktif.",
            },
            {
                "step": 4,
                "title": "Periksa hak akses",
                "instruction": "Jika bisa login tapi fitur terbatas, cek role di profil. Minta admin menambah permission jika diperlukan: Settings → Users → Edit Role.",
                "verification": "Semua fitur yang dibutuhkan sudah bisa diakses.",
            },
        ],
        "workaround": "Gunakan akun rekan kerja sementara atau hubungi admin langsung via WhatsApp/telepon untuk reset darurat.",
        "escalation_triggers": [
            "Akun admin utama terkunci",
            "Dugaan akses tidak sah (hacking)",
            "Semua user tidak bisa login (masalah server)",
        ],
        "metadata": {
            "typical_resolution_time": "5 minutes",
            "technical_difficulty": "easy",
            "common_root_causes": ["forgotten_password", "account_locked", "permission_issue"],
            "requires_hardware_access": False,
            "data_loss_risk": False,
        },
    },
}


# ============================================================================
# KB UTILITY FUNCTIONS
# ============================================================================

def get_kb_category(keywords: list) -> Optional[dict]:
    """Find best-matching KB category based on keywords.
    Uses keyword hit counting for smarter matching instead of first-match.
    """
    if not keywords:
        return None
    
    search_text = ' '.join(keywords).lower()
    best_match = None
    best_score = 0
    
    for category, kb_data in KB_TROUBLESHOOTING.items():
        score = sum(1 for kw in kb_data["keywords"] if kw.lower() in search_text)
        if score > best_score:
            best_score = score
            best_match = {"category": category, "confidence": min(1.0, score / 3.0), **kb_data}
    
    return best_match


def get_category_by_id(category_id: str) -> Optional[dict]:
    """Get KB category metadata by ID"""
    return KB_TROUBLESHOOTING.get(category_id)


def get_troubleshooting_steps(category_id: str) -> list:
    """Get troubleshooting steps for a category"""
    kb = KB_TROUBLESHOOTING.get(category_id)
    if kb:
        return kb.get("troubleshooting_steps", [])
    return []


def get_first_response(category_id: str) -> str:
    """Get initial response for a category"""
    kb = KB_TROUBLESHOOTING.get(category_id)
    if kb:
        return kb.get("first_response", "Saya akan bantu masalah Anda.")
    return "Saya akan bantu masalah Anda."


def search_kb_symptoms(symptoms: list) -> list:
    """Search KB for matching categories based on symptoms"""
    matches = []
    for category, kb_data in KB_TROUBLESHOOTING.items():
        kb_symptoms = kb_data.get("symptoms", [])
        match_count = sum(1 for sym in symptoms if sym in kb_symptoms)
        if match_count > 0:
            similarity = match_count / max(len(symptoms), len(kb_symptoms))
            matches.append({
                "category": category,
                "match_count": match_count,
                "similarity_score": similarity,
                "metadata": kb_data,
            })
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    return matches


def get_all_keywords() -> set:
    """Get all keywords from KB for indexing/search"""
    all_keywords = set()
    for kb_data in KB_TROUBLESHOOTING.values():
        all_keywords.update(kb_data.get("keywords", []))
    return all_keywords


def get_all_categories() -> list:
    """Get list of all categories for UI dropdown/selection"""
    return [
        {
            "id": kb_data["category_id"],
            "title": kb_data["title"],
            "difficulty": kb_data["metadata"].get("technical_difficulty", "unknown"),
            "typical_time": kb_data["metadata"].get("typical_resolution_time", "unknown"),
        }
        for kb_data in KB_TROUBLESHOOTING.values()
    ]


if __name__ == "__main__":
    """Test KB index"""
    print("✅ KB Troubleshooting Loaded")
    print(f"   Total categories: {len(KB_TROUBLESHOOTING)}")
    print(f"   Total keywords: {len(get_all_keywords())}")
    print(f"\n📚 Available categories:")
    for cat in get_all_categories():
        print(f"   - {cat['id']}: {cat['title']} (Difficulty: {cat['difficulty']})")
    
    print(f"\n📋 Sample troubleshooting (GPS):")
    for step in get_troubleshooting_steps("gps"):
        print(f"   Step {step['step']}: {step['title']}")
