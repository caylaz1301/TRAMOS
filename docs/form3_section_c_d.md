# Form 3 — Section C and D

## C. STANDARDS USED

Tabel berikut merangkum standar teknis yang digunakan dalam pengembangan aplikasi **Design and Development of a WhatsApp-Based Issue Reporting and Analytics Dashboard System for TRAMOS Web at PT Andakara Informatika Nusantara**.

| No | Area | Standard / Specification | Implementation in This Project |
|---|---|---|---|
| 1 | API Architecture | RESTful API principles | Komunikasi backend menggunakan endpoint REST (`GET`, `POST`) untuk webhook, ticketing, dan analytics. |
| 2 | Data Exchange Format | JSON (`application/json`, RFC 8259) | Payload pesan WhatsApp, request/response API internal, dan integrasi osTicket dikirim dalam JSON. |
| 3 | Transport Security | HTTPS over TLS 1.2+ | Webhook WhatsApp menggunakan endpoint HTTPS (melalui tunnel/domain publik) agar data terenkripsi saat transit. |
| 4 | Webhook Integration | Meta WhatsApp Business webhook contract | Verifikasi webhook menggunakan `hub.mode`, `hub.challenge`, `hub.verify_token`; pesan masuk diproses dari payload webhook resmi Meta. |
| 5 | Authentication Token | JWT (RFC 7519) | Otentikasi endpoint internal/dashboard menggunakan token JWT (`PyJWT`). |
| 6 | Backend Runtime Standard | ASGI (Asynchronous Server Gateway Interface) | Aplikasi backend dibangun dengan FastAPI + Uvicorn sesuai standar service async Python. |
| 7 | HTTP Semantics | HTTP/1.1 status code semantics (RFC 9110) | Respons API menggunakan status code yang konsisten (200, 400, 401, 404, 500) sesuai kondisi proses. |
| 8 | Character Encoding | UTF-8 | Semua data teks (chat WhatsApp, deskripsi issue, log sistem) diproses dengan UTF-8. |
| 9 | Database Standard | PostgreSQL SQL compliance | Penyimpanan data conversation, ticket, user, dan analytics menggunakan PostgreSQL. |
| 10 | ORM Standardization | SQLAlchemy ORM patterns | Mapping model-entity, relasi, dan transaksi database menggunakan SQLAlchemy ORM. |
| 11 | API Documentation | OpenAPI 3.x | Dokumentasi API tersedia otomatis melalui FastAPI Swagger/ReDoc. |
| 12 | Modeling Standard | UML 2.x | Pemodelan sistem menggunakan Use Case Diagram, Activity Diagram, Sequence Diagram, dan Class Diagram. |
| 13 | Logging Format | Structured logging (JSON logger) | Logging backend disusun terstruktur untuk memudahkan monitoring dan debugging webhook/dialog flow/ticketing. |
| 14 | Time Format | ISO 8601 datetime | Timestamp event backend dan health monitoring dicatat dalam format waktu standar terstruktur. |
| 15 | Configuration Standard | Environment-based configuration (`.env`) | Konfigurasi secret, API key, dan token dipisahkan dari source code untuk keamanan deployment. |

---

## D. IMPLEMENTATION AND TESTING SCENARIO

### D.1 Implementation Plan

| Phase | Implementation Activity | Technical Detail | Output |
|---|---|---|---|
| 1 | Environment setup | Install dependency, set `.env`, konfigurasi PostgreSQL, osTicket, WhatsApp token | Environment siap dijalankan |
| 2 | Backend API development | Bangun route FastAPI: webhook, ticket, health, analytics; validasi schema dengan Pydantic | Endpoint inti tersedia |
| 3 | WhatsApp webhook integration | Implement `GET` verification + `POST` incoming message handler; mapping payload Meta | Pesan WhatsApp masuk ke sistem |
| 4 | Conversation & AI flow | Implement state machine dialog (greeting, problem capture, KB troubleshooting, escalation) dengan fallback rule-based + Ollama/Mistral | Alur chat multi-turn stabil |
| 5 | Ticket automation | Jika unresolved, collect data (unit, lokasi, waktu), lalu kirim ke osTicket API | Ticket otomatis tercipta |
| 6 | Data persistence | Simpan conversation, ticket, status, dan analytics source ke PostgreSQL | Data historis tersimpan |
| 7 | Analytics endpoint/dashboard | Proses agregasi issue category, resolution rate, escalation trend untuk dashboard | Monitoring manajemen tersedia |
| 8 | Reliability improvements | Tambahkan dedup message webhook, validation input, dan error handling | Respon ganda dan input invalid berkurang |
| 9 | Integration testing & UAT | Uji end-to-end dari WhatsApp sampai ticket dan dashboard | Sistem siap demonstrasi capstone |

### D.2 Detailed Testing Scenarios

| No | Scenario | Preconditions | Test Steps | Expected Result | Alternative / Negative Case |
|---|---|---|---|---|---|
| 1 | Webhook verification success | Server aktif, token benar | Kirim request `GET` verifikasi webhook dengan token valid | Server mengembalikan challenge, verifikasi sukses | Jika token salah, sistem menolak verifikasi (`403`/gagal verifikasi) |
| 2 | Incoming WhatsApp message received | Webhook URL aktif & terhubung | Kirim pesan dari user ke nomor WhatsApp bisnis | Pesan diterima backend dan diproses | Jika payload invalid, request ditolak dengan error handling |
| 3 | Duplicate message handling | Mekanisme dedup aktif | Kirim payload message ID yang sama dua kali | Hanya 1 pesan diproses, tidak ada balasan ganda | Jika dedup nonaktif, berpotensi terjadi double response |
| 4 | Intent/category detection | Modul NLP/KB aktif | User kirim keluhan seperti “GPS lelet/lambat” | Sistem mengklasifikasikan kategori issue yang sesuai | Jika keyword ambigu, bot meminta klarifikasi |
| 5 | KB solution flow success | Knowledge base memiliki solusi relevan | User melaporkan masalah umum; bot kirim langkah solusi | User menerima troubleshooting + pertanyaan hasil | Jika solusi tidak ada, sistem lanjut ke eskalasi tiket |
| 6 | Escalation data collection completeness | State eskalasi aktif | User isi unit, lokasi, waktu | Sistem menyimpan data lengkap dan lanjut konfirmasi | Jika user hanya kirim “ok/iya”, bot meminta input valid ulang |
| 7 | Time parsing validation | Form pengisian waktu aktif | Input waktu: `14:30`, `jam 3 sore`, `tadi pagi` | Sistem menormalkan waktu dan menyimpan ke context ticket | Jika format tidak dikenali, bot meminta format waktu yang benar |
| 8 | Ticket creation to osTicket | osTicket API reachable, API key valid | Setelah konfirmasi, trigger create ticket | Ticket ID berhasil dibuat dan dikirim ke user | Jika osTicket down/API key salah, sistem kirim pesan gagal yang aman + log error |
| 9 | Database persistence test | PostgreSQL terhubung | Jalankan percakapan end-to-end sampai ticket dibuat | Conversation, message, dan metadata tersimpan | Jika koneksi DB putus, proses gagal terkontrol dan tercatat di log |
| 10 | Health endpoint monitoring | Server berjalan | Akses endpoint health check | Menampilkan status komponen (`database`, `ai_engine`, dll.) | Jika AI engine tidak reachable, status `degraded` namun layanan inti tetap berjalan |
| 11 | JWT authentication test | Endpoint protected aktif | Akses endpoint protected tanpa token lalu dengan token valid | Tanpa token ditolak, token valid diterima | Token invalid/expired menghasilkan `401 Unauthorized` |
| 12 | End-to-end UAT with operator | WhatsApp, backend, DB, osTicket aktif | Simulasi kasus real: report issue → solusi → unresolved → ticket | Alur lengkap berjalan; operator menerima ticket; data tercatat untuk analytics | Jika salah satu service gagal, sistem memberi fallback message dan logging yang jelas |

### D.3 Test Execution Notes

- Pengujian dilakukan berlapis: unit logic, API integration, webhook integration, dan end-to-end user journey.
- Prioritas kualitas: kejelasan dialog, akurasi pencatatan data tiket, ketahanan terhadap pesan duplikat, dan stabilitas integrasi eksternal.
- Kriteria lulus utama: issue dari WhatsApp dapat diproses otomatis, ticket terbentuk saat unresolved, dan data masuk ke pipeline analytics.
