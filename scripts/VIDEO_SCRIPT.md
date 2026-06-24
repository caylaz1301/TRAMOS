# 📹 NASKAH VIDEO DEMONSTRASI CAPSTONE
## Design and Development of a WhatsApp-Based Issue Reporting System for TRAMOS Web

**Durasi Target: 10-12 menit**
**Pembicara: Ivander Johana Pratama**

---

## SEBELUM REKAM

### Alat yang Dibutuhkan
- Laptop dengan VS Code terbuka di folder TRAMOS
- Terminal yang bersih
- Browser terbuka di dashboard (sudah running)
- VPS sudah running

### Checklist Pra-Rekaman
- [ ] VPS container sudah running: `docker ps` (tramos-backend, postgres, redis, dashboard, ollama, osticket)
- [ ] WhatsApp HP pribadi/dummy sudah bisa kirim pesan ke bot
- [ ] Dashboard sudah terbuka di browser: `helpdesk.tramos.systems/dashboard`
- [ ] VS Code terbuka di folder TRAMOS
- [ ] Git repository clean / siap shown
- [ ] Lampu ruangan cukup terang
- [ ] Mic external / headset sudah colok

---

## BAGIAN 1 — BUILD SYSTEM (5-7 MENIT)

> *Pembicara: "Saya akan tunjukkan bagaimana sistem ini dibangun dari nol."*

### SCENE 1.1 — Struktur Project (1 menit)

**Tunjukkin layar VS Code / Finder:**

> "Ini struktur project TRAMOS yang sudah saya bangun selama pengembangan Capstone."

Tunjukkin folder-folder ini di layar:
```
TRAMOS/
├── app/                    → Backend FastAPI (AI chatbot, routes, services)
├── dashboard/               → Frontend React + Vite
├── deploy/                  → Docker Compose production
├── knowledge_base/           → Dokumen troubleshooting KB
└── scripts/                 → Automation scripts
```

> "Saya pakai VS Code sebagai IDE utama. Struktur ini memisahkan backend dan frontend secara jelas."

---

### SCENE 1.2 — WhatsApp Webhook (1.5 menit)

**Buka file `app/routes/whatsapp.py`:**

> "Ini file utama yang menerima pesan dari WhatsApp Gateway Meta. Setiap pesan masuk diproses di sini."

Scroll pelan, tunjukin bagian-bagian pentingnya:

```
• GET /webhook/whatsapp     → Verifikasi webhook Meta
• POST /webhook/whatsapp   → Terima pesan masuk
• Dedup message ID         → Cegah pesan duplikat
• Session manager          → Kelola state percakapan
```

> "Kode ini menangani semua pesan WhatsApp masuk, deduplikasi, dan passing ke dialog flow."

---

### SCENE 1.3 — AI Dialog Flow (1.5 menit)

**Buka folder `app/services/chatbot/`:**

> "Ini engine AI-nya. Dialog flow chatbot saya bangun secara modular."

Buka file per file (scroll cepat, gak perlu baca satu-satu):

| File | Fungsi |
|------|---------|
| `dialog_dispatcher.py` | Router utama — tentukan intent, state, response |
| `smart_dialog_flow.py` | Logika transisi state dan KB fallback |
| `intent_classifier.py` | Klasifikasi intent: troubleshooting, emergency, out-of-scope |
| `session_manager.py` | Menyimpan data sesi pengguna di Redis + PostgreSQL |
| `solution_searcher.py` | Cari solusi dari Knowledge Base |

> "Setiap pesan dari pengguna masuk ke dispatcher, diklasifikasi intentnya, diproses sesuai state, lalu dibalas. State machine-nya 13 state — mulai dari greeting sampai ticket created."

---

### SCENE 1.4 — Knowledge Base Fallback (1 menit)

**Buka `app/utils/kb_troubleshooting.py`:**

> "Ini Knowledge Base troubleshooting untuk 11 kategori masalah: GPS, kamera, connectivity, device, app, vehicle, dan lainnya."

Scroll pelan menunjukkan categories:
- GPS, Connectivity, Camera, Device, Vehicle, App, Billing, Ticket, Maintenance, Sensor, Driver, Report, Account

> "Kalau RAG dan AI semantic tidak menemukan solusi, sistem fallback ke langkah troubleshooting statis per kategori ini. Jadi bot selalu bisa jawab."

---

### SCENE 1.5 — Dashboard Analytics (1 menit)

**Buka folder `dashboard/src/`:**

> "Frontend dashboard analytics ini saya bangun dengan React dan Vite."

```
pages/
├── OverviewPage.tsx    → Ringkasan statistik utama
├── InsightsPage.tsx   → Insight tren dan pattern
└── PerformancePage.tsx  → Visualisasi data performa
```

> "Dashboard menampilkan data yang dikumpulkan dari setiap percakapan WhatsApp: jenis masalah, frekuensi, trend, dan performa resolusi."

---

### SCENE 1.6 — Build Process (1 menit)

**Di terminal, jalankan:**

```bash
cd dashboard
npm run build
```

> "Build dashboard ini otomatis menghasilkan static files yang di-serve container Nginx."

Lihat hasilnya: `dist/` → `assets/`, `index.html`.

---

## BAGIAN 2 — INSTALL & DEPLOY (3-5 MENIT)

> *Pembicara: "Sekarang saya tunjukin cara deploy ke VPS."*

### SCENE 2.1 — VPS Connection (1 menit)

**Di terminal, jalankan:**

```bash
ssh ivander@202.83.120.98 -p 22028
```

> "Saya login ke VPS menggunakan SSH di port 22028 yang sudah dikonfigurasi."

---

### SCENE 2.2 — Docker Container Running (1 menit)

```bash
docker ps
```

> "Di VPS, Docker container sudah running dengan compose ini:"

| Container | Fungsi |
|-----------|---------|
| tramos-backend | FastAPI + AI chatbot + Dialog flow |
| tramos-postgres | Database PostgreSQL |
| tramos-redis | Session cache |
| tramos-ollama | AI embedding model |
| tramos-dashboard | Frontend analytics |
| osticket | Ticket management system |

---

### SCENE 2.3 — Live Dashboard (1 menit)

**Buka browser, show `helpdesk.tramos.systems/dashboard/`:**

> "Ini dashboard analytics yang sudah running 24/7 di VPS."

Scroll pelan menunjukkan:
- Overview statistics
- Charts dan grafik
- Filter date range

---

### SCENE 2.4 — Konfirmasi Deployment (1 menit)

```bash
docker compose -f docker-compose.prod.yml logs --tail=10 backend
```

> "Ini log backend terakhir. Bisa lihat aktivitas real-time chatbot."

---

## BAGIAN 3 — USE (4-5 MENIT)

> *Pembicara: "Sekarang saya demo cara user pakai sistem dari WhatsApp."*

### SCENE 3.1 — WhatsApp: Greeting (30 detik)

**HP/dummy WhatsApp terbuka di chat TRAMOS:**

> "User kirim pesan 'halo' ke nomor WhatsApp Business."

Kirim: `halo`

> "Bot otomatis greet dan minta nama."

Tunggu balasan muncul di layar HP.

---

### SCENE 3.2 — WhatsApp: Laporkan Masalah GPS (1 menit)

Kirim: `GPS tidak update dari tadi pagi`

> "User langsung laporkan masalah GPS tanpa harus pilih menu."

Tunggu balasan solusi + pertanyaan "Berhasil?"

---

### SCENE 3.3 — WhatsApp: Konfirmasi Gagal → Ticket (1.5 menit)

Kirim: `2` (tidak berhasil)

> "User bilang tidak berhasil. Bot otomatis eskalasi ke pembuatan tiket."

Bot minta unit, lokasi, waktu. Isi pelan-pelan di HP:
```
Kirim: B 1234 AB
Kirim: Tol Cipularang KM 45
Kirim: 09.30
Kirim: 1 (konfirmasi Ya)
```

> "Bot otomatis buat tiket di osTicket dan kasih nomor tiket."

---

### SCENE 3.4 — Email Notifikasi (30 detik)

**Buka inbox email operator:**

> "Operator dapat email notifikasi otomatis berisi detail tiket baru."

Tunjukin email masuk: subjek, ticket number, unit, deskripsi.

---

### SCENE 3.5 — Dashboard Analytics (1 menit)

**Kembali ke browser dashboard:**

> "Setiap tiket yang dibuat otomatis masuk dashboard analytics."

Refresh dashboard → tunjukin data baru bertambah (ticket count +1, category graph update).

---

## PENUTUP (30 detik)

> "Jadi sistem ini sudah lengkap: WhatsApp chatbot AI, auto-ticket, analytics dashboard, email notification — semua berjalan otomatis 24/7 di VPS."

> "Sekian demo dari saya. Terima kasih."

---

## PANDUAN TEKNIS REKAMAN

### Setup Recording
- **Software**: OBS Studio (gratis, open source) atau QuickTime Screen Recording
- **Resolution**: 1920x1080
- **Frame rate**: 30fps
- **Audio**: Mic external/colokan headset (bukan mic laptop)

### Lighting
- Ruangan cukup terang (natural light dari jendela atau lampu LED)
- Layar laptop bright (100% brightness)
- Background rapi (meja minimalis / virtual background OBS)

### Hal yang Harus Dihindari
- ❌ Layar gelap/blur saat scroll
- ❌ Mic laptop pecicilan (pakai headset)
- ❌ Suara AC / kipas angin nyaring
- ❌ Gangguan notification HP/pc lain
- ❌ Bicara terlalu pelan

### Hal yang Harus Ada
- ✅ Layar jelas, teks/code readable
- ✅ Suara pembicara tenang dan jelas
- ✅ Pace bicara santai (tidak buru-buru)
- ✅ HP/webcam tunjukin WhatsApp real-time
- ✅ Hands-free mic atau mic headset

### Durasi per Scene
| Scene | Target |
|-------|--------|
| BUILD | 5-7 menit |
| INSTALL | 3-5 menit |
| USE | 4-5 menit |
| Penutup | 30 detik |
| **TOTAL** | **12-17 menit** |

### Kalau advisor tanya:
| Pertanyaan | Jawaban Singkat |
|-----------|----------------|
| Kenapa pakai WhatsApp? | Paling aksesibel untuk driver di jalan |
| Kenapa AI fallback manual? | Agar bot selalu bisa jawab masalah TRAMOS |
| Perbedaan dengan chatbot biasa? | RAG + semantic search + auto ticket + analytics |
| Sudah diuji belum? | Sudah — 11 regression test unit test |
| Kenapa VPS bukan cloud managed? | Lebih murah dan fleksibel untuk skripsi |
| Kapasitas berapa user? | VPS kami 8GB RAM, support 50-100 concurrent users |

---

*Script ini sudah final. Print atau buka di layar kedua sebagai teleprompter saat rekam.*
