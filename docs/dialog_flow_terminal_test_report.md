# TRAMOS Terminal Dialog Flow Test Report

Generated at: 2026-05-22 14:23:09 Asia/Jakarta

## Scope

- Channel tested: terminal simulation using `process_message_with_ai()`.
- WhatsApp Cloud API delivery: not used.
- Database/session tracking: enabled.
- osTicket: real integration, no mock.
- LLM/Gemini: disabled for deterministic KB fallback testing.

## Environment

- Database URL: `postgresql://***:***@localhost:5434/tramos_db`
- osTicket base URL: `http://127.0.0.1/osTicket/api`
- osTicket configured: `True`
- WhatsApp phone ID configured: `True`

## Summary

- Total scenarios: 5
- Passed: 5
- Failed: 0

| Case | Scenario | Final State | Ticket | Result |
|---|---|---|---|---|
| S01 | KB solution works, no ticket created | `resolved` | `-` | PASS |
| S02 | KB solution fails, real osTicket ticket is created | `closed` | `135682` | PASS |
| S03 | Ambiguous feedback is clarified before closing | `resolved` | `-` | PASS |
| S04 | Invalid inputs and detail correction before ticket | `closed` | `817264` | PASS |
| S05 | New issue after resolved session starts cleanly | `collecting_name` | `-` | PASS |

## S01 - KB solution works, no ticket created

Purpose: Driver reports GPS issue, follows troubleshooting, confirms resolved.

Phone/session test id: `62899056849301`

| # | Driver message | State | Bot response |
|---|---|---|---|
| 1 | halo | `none` -> `collecting_name` | Selamat Siang! 👋 Kami TRAMOS Support Bot 🤖 Siapa nama Anda? |
| 2 | Andi Pratama | `collecting_name` -> `collecting_problem` | Terima kasih Andi Pratama! 😊 🤔 Ceritakan masalah yang Anda alami 1️⃣ GPS tidak berfungsi 2️⃣ Kamera error 3️⃣ Baterai cepat habis 4️⃣ Masalah koneksi (Kirim nomor atau jawab langsung) |
| 3 | GPS di unit saya tidak update lokasi dan posisi kendaraan hilang dari aplikasi sejak tadi pagi | `collecting_problem` -> `asking_solution_worked` | Andi Pratama, ini solusi untuk masalah GPS Anda: Tracking hilang berarti monitoring jadi blind spot 📍 Jangan khawatir, kita handle ini bareng-bareng. GPS & Tracking Issues - Sangat yakin ini solusinya Ini langkah-langkahnya: 1. Cek posisi device: • Pastikan device GPS berada di area terbuka (outdoor) • Sinyal GPS tidak bisa menembus gedung atau atap tebal • Pindahkan ke area yang bisa 'melihat langit' langsung ✓ C... |
| 4 | sudah berhasil setelah saya restart device, makasih | `asking_solution_worked` -> `resolved` | ✅ Problem Teratasi! Senang mendengar solusi yang kami berikan sudah fixed! 🎉 Tips untuk ke depannya: • Jika ada masalah lagi, hubungi kami kapan saja 😊 Jika ada masalah lagi, langsung hubungi kami ya 👍 Stay safe on the road! 🚗 |

### Full Dialog Transcript

#### Turn 1

Driver:

```text
halo
```

Bot:

```text
Selamat Siang! 👋

Kami TRAMOS Support Bot 🤖

Siapa nama Anda?
```

#### Turn 2

Driver:

```text
Andi Pratama
```

Bot:

```text
Terima kasih Andi Pratama! 😊

🤔 Ceritakan masalah yang Anda alami

1️⃣ GPS tidak berfungsi
2️⃣ Kamera error
3️⃣ Baterai cepat habis
4️⃣ Masalah koneksi

(Kirim nomor atau jawab langsung)
```

#### Turn 3

Driver:

```text
GPS di unit saya tidak update lokasi dan posisi kendaraan hilang dari aplikasi sejak tadi pagi
```

Bot:

```text
Andi Pratama, ini solusi untuk masalah GPS Anda:

Tracking hilang berarti monitoring jadi blind spot 📍 Jangan khawatir, kita handle ini bareng-bareng.


GPS & Tracking Issues - Sangat yakin ini solusinya

Ini langkah-langkahnya:

1. Cek posisi device:
   • Pastikan device GPS berada di area terbuka (outdoor)
   • Sinyal GPS tidak bisa menembus gedung atau atap tebal
   • Pindahkan ke area yang bisa 'melihat langit' langsung
   ✓ Cek: Tunggu 2-3 menit. Cek apakah indikator GPS sudah menunjukkan sinyal (biasanya ada ikon satelit).

2. Restart device tracking:
   • Matikan device GPS sepenuhnya
   • Tunggu 30 detik
   • Nyalakan kembali dan tunggu hingga boot sempurna (biasanya 1-2 menit)
   ✓ Cek: Setelah restart, cek apakah lokasi di app TRAMOS sudah terupdate dengan benar.

3. Cek koneksi internet device:
   • GPS butuh internet untuk mengirim data lokasi ke server
   • Pastikan SIM card aktif dan ada sinyal data (4G/3G)
   • Coba buka browser di device untuk tes koneksi
   ✓ Cek: J...
```

#### Turn 4

Driver:

```text
sudah berhasil setelah saya restart device, makasih
```

Bot:

```text
✅ Problem Teratasi!

Senang mendengar solusi yang kami berikan sudah fixed! 🎉

Tips untuk ke depannya:
  • Jika ada masalah lagi, hubungi kami kapan saja 😊

Jika ada masalah lagi, langsung hubungi kami ya 👍
Stay safe on the road! 🚗
```

## S02 - KB solution fails, real osTicket ticket is created

Purpose: Driver reports camera issue, solution fails, complete field data, create support ticket.

Phone/session test id: `62899037234102`

| # | Driver message | State | Bot response |
|---|---|---|---|
| 1 | halo | `none` -> `collecting_name` | Selamat Siang! 👋 Kami TRAMOS Support Bot 🤖 Siapa nama Anda? |
| 2 | Budi Hartono | `collecting_name` -> `collecting_problem` | Terima kasih Budi Hartono! 😊 🤔 Ceritakan masalah yang Anda alami 1️⃣ GPS tidak berfungsi 2️⃣ Kamera error 3️⃣ Baterai cepat habis 4️⃣ Masalah koneksi (Kirim nomor atau jawab langsung) |
| 3 | kamera dashboard mati total, tampilan video hitam terus | `collecting_problem` -> `asking_solution_worked` | Budi Hartono, ini solusi untuk masalah Camera Anda: Recording error, bisa jadi dokumentasi perjalanan berantakan 📹 Jangan khawatir, kita handle ini bareng-bareng. Camera & Video Recording Issues - Sangat yakin ini solusinya Ini langkah-langkahnya: 1. Periksa fisik kamera: • Bersihkan lensa kamera dengan kain lembut • Pastikan tidak ada debu, air, atau noda yang menghalangi • Cek apakah kabel power kamera terhubung... |
| 4 | belum berhasil, masih error | `asking_solution_worked` -> `collecting_unit` | Baik, saya akan eskalasi ke tim teknisi kami. Untuk membuat tiket laporan, saya butuh 3 informasi singkat: 1️⃣ Nama unit/kendaraan 2️⃣ Lokasi saat ini 3️⃣ Waktu kejadian Pertama, *unit atau kendaraan mana* yang bermasalah? (Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_) |
| 5 | TRAM-017 | `collecting_unit` -> `collecting_location` | ✅ Unit: *TRAM-017* Selanjutnya, *di mana lokasi* unit tersebut saat ini? Bisa sebut: • Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_) • Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_) • Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_) |
| 6 | Tol Cikampek KM 42 arah Jakarta | `collecting_location` -> `collecting_time` | ✅ Lokasi: *Tol Cikampek KM 42 arah Jakarta* Terakhir, *kapan masalah ini terjadi*? Bisa jawab dengan: • Jam spesifik (misal: _14:30_, _jam 3 sore_) • Waktu umum (misal: _tadi pagi_, _kemarin sore_) • _sekarang_ / _barusan_ jika baru terjadi |
| 7 | jam 7 pagi | `collecting_time` -> `confirming_details` | 📋 *Ringkasan Tiket Laporan* ───────────────────────── 👤 Nama: Budi Hartono 🚛 Unit: TRAM-017 📍 Lokasi: Tol Cikampek KM 42 arah Jakarta 🕐 Waktu: 7:00 🏷️ Kategori: Camera 📝 Masalah: kamera dashboard mati total, tampilan video hitam terus ───────────────────────── Apakah data di atas sudah benar? 🤔 1️⃣ *Ya*, lanjutkan buat tiket 2️⃣ *Tidak*, saya mau perbaiki |
| 8 | ya lanjut buat tiket | `confirming_details` -> `closed` | ✅ **Tiket Berhasil Dibuat!** 📌 Nomor Tiket: #135682 🏷️ Kategori: Camera 🚗 Equipment: TRAM-017 📍 Lokasi: Tol Cikampek KM 42 arah Jakarta ⏰ Waktu: 7:00 Tim support TRAMOS akan segera menangani masalah Anda. Kami akan menghubungi Anda berdasarkan detail yang Anda berikan. Terima kasih telah melaporkan! 🙏 |

### Full Dialog Transcript

#### Turn 1

Driver:

```text
halo
```

Bot:

```text
Selamat Siang! 👋

Kami TRAMOS Support Bot 🤖

Siapa nama Anda?
```

#### Turn 2

Driver:

```text
Budi Hartono
```

Bot:

```text
Terima kasih Budi Hartono! 😊

🤔 Ceritakan masalah yang Anda alami

1️⃣ GPS tidak berfungsi
2️⃣ Kamera error
3️⃣ Baterai cepat habis
4️⃣ Masalah koneksi

(Kirim nomor atau jawab langsung)
```

#### Turn 3

Driver:

```text
kamera dashboard mati total, tampilan video hitam terus
```

Bot:

```text
Budi Hartono, ini solusi untuk masalah Camera Anda:

Recording error, bisa jadi dokumentasi perjalanan berantakan 📹 Jangan khawatir, kita handle ini bareng-bareng.


Camera & Video Recording Issues - Sangat yakin ini solusinya

Ini langkah-langkahnya:

1. Periksa fisik kamera:
   • Bersihkan lensa kamera dengan kain lembut
   • Pastikan tidak ada debu, air, atau noda yang menghalangi
   • Cek apakah kabel power kamera terhubung dengan baik
   ✓ Cek: Lensa bersih dan kabel terpasang kuat.

2. Power cycle kamera:
   • Cabut kabel power kamera selama 1-2 menit
   • Pasang kembali dengan hati-hati
   • Tunggu sampai kamera fully boot (LED indikator menyala normal)
   ✓ Cek: LED kamera menyala normal (biasanya hijau = OK, merah = error).

3. Cek storage dan permission:
   • Pastikan storage device masih cukup (minimal 10% free)
   • Cek apakah permission kamera sudah diberikan di app settings
   ✓ Cek: Coba record video pendek (30 detik) dan playback hasilnya.

4. Reset pengaturan kamera...
```

#### Turn 4

Driver:

```text
belum berhasil, masih error
```

Bot:

```text
Baik, saya akan eskalasi ke tim teknisi kami.

Untuk membuat tiket laporan, saya butuh 3 informasi singkat:
1️⃣ Nama unit/kendaraan
2️⃣ Lokasi saat ini
3️⃣ Waktu kejadian

Pertama, *unit atau kendaraan mana* yang bermasalah?
(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)
```

#### Turn 5

Driver:

```text
TRAM-017
```

Bot:

```text
✅ Unit: *TRAM-017*

Selanjutnya, *di mana lokasi* unit tersebut saat ini?

Bisa sebut:
• Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_)
• Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_)
• Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_)
```

#### Turn 6

Driver:

```text
Tol Cikampek KM 42 arah Jakarta
```

Bot:

```text
✅ Lokasi: *Tol Cikampek KM 42 arah Jakarta*

Terakhir, *kapan masalah ini terjadi*?

Bisa jawab dengan:
• Jam spesifik (misal: _14:30_, _jam 3 sore_)
• Waktu umum (misal: _tadi pagi_, _kemarin sore_)
• _sekarang_ / _barusan_ jika baru terjadi
```

#### Turn 7

Driver:

```text
jam 7 pagi
```

Bot:

```text
📋 *Ringkasan Tiket Laporan*
─────────────────────────
👤 Nama: Budi Hartono
🚛 Unit: TRAM-017
📍 Lokasi: Tol Cikampek KM 42 arah Jakarta
🕐 Waktu: 7:00
🏷️ Kategori: Camera
📝 Masalah: kamera dashboard mati total, tampilan video hitam terus
─────────────────────────

Apakah data di atas sudah benar? 🤔

1️⃣ *Ya*, lanjutkan buat tiket
2️⃣ *Tidak*, saya mau perbaiki
```

#### Turn 8

Driver:

```text
ya lanjut buat tiket
```

Bot:

```text
Baik, sedang membuat tiket support untuk Anda... ⏳
```

#### Turn 9

Driver:

```text
(system/no user message)
```

Bot:

```text
✅ **Tiket Berhasil Dibuat!**

📌 Nomor Tiket: #135682
🏷️ Kategori: Camera
🚗 Equipment: TRAM-017
📍 Lokasi: Tol Cikampek KM 42 arah Jakarta
⏰ Waktu: 7:00

Tim support TRAMOS akan segera menangani masalah Anda.
Kami akan menghubungi Anda berdasarkan detail yang Anda berikan.

Terima kasih telah melaporkan! 🙏
```

## S03 - Ambiguous feedback is clarified before closing

Purpose: Driver says 'oke' after solution; bot should not mark issue resolved until explicit confirmation.

Phone/session test id: `62899021199203`

| # | Driver message | State | Bot response |
|---|---|---|---|
| 1 | halo | `none` -> `collecting_name` | Selamat Siang! 👋 Kami TRAMOS Support Bot 🤖 Siapa nama Anda? |
| 2 | Citra Lestari | `collecting_name` -> `collecting_problem` | Terima kasih Citra Lestari! 😊 🤔 Ceritakan masalah yang Anda alami 1️⃣ GPS tidak berfungsi 2️⃣ Kamera error 3️⃣ Baterai cepat habis 4️⃣ Masalah koneksi (Kirim nomor atau jawab langsung) |
| 3 | koneksi internet unit sering offline dan data tracking putus putus | `collecting_problem` -> `asking_solution_worked` | Citra Lestari, ini solusi untuk masalah Connectivity Anda: Koneksi putus-putus itu yang paling menjengkelkan saat op 📡 Jangan khawatir, kita handle ini bareng-bareng. Internet & Network Connectivity - Sangat yakin ini solusinya Ini langkah-langkahnya: 1. Cek kualitas sinyal: • Lihat indikator sinyal di device • Minimal 2 bar untuk koneksi data yang stabil • Jika kurang, coba pindah ke lokasi dengan sinyal lebih ba... |
| 4 | oke | `asking_solution_worked` -> `asking_solution_worked` | 🤔 Siap. Setelah dicoba, apakah masalahnya sudah benar-benar berhasil diperbaiki? 1️⃣ Ya, berhasil 2️⃣ Tidak, masih error (Kirim nomor atau jawab langsung) |
| 5 | ya sudah berhasil | `asking_solution_worked` -> `resolved` | ✅ Problem Teratasi! Senang mendengar solusi yang kami berikan sudah fixed! 🎉 Tips untuk ke depannya: • Jika ada masalah lagi, hubungi kami kapan saja 😊 Jika ada masalah lagi, langsung hubungi kami ya 👍 Stay safe on the road! 🚗 |

### Full Dialog Transcript

#### Turn 1

Driver:

```text
halo
```

Bot:

```text
Selamat Siang! 👋

Kami TRAMOS Support Bot 🤖

Siapa nama Anda?
```

#### Turn 2

Driver:

```text
Citra Lestari
```

Bot:

```text
Terima kasih Citra Lestari! 😊

🤔 Ceritakan masalah yang Anda alami

1️⃣ GPS tidak berfungsi
2️⃣ Kamera error
3️⃣ Baterai cepat habis
4️⃣ Masalah koneksi

(Kirim nomor atau jawab langsung)
```

#### Turn 3

Driver:

```text
koneksi internet unit sering offline dan data tracking putus putus
```

Bot:

```text
Citra Lestari, ini solusi untuk masalah Connectivity Anda:

Koneksi putus-putus itu yang paling menjengkelkan saat op 📡 Jangan khawatir, kita handle ini bareng-bareng.


Internet & Network Connectivity - Sangat yakin ini solusinya

Ini langkah-langkahnya:

1. Cek kualitas sinyal:
   • Lihat indikator sinyal di device
   • Minimal 2 bar untuk koneksi data yang stabil
   • Jika kurang, coba pindah ke lokasi dengan sinyal lebih baik
   ✓ Cek: Sinyal minimal 2 bar dan stabil (tidak naik-turun terus).

2. Toggle mode pesawat:
   • Aktifkan mode pesawat (Airplane Mode) selama 10 detik, lalu matikan kembali
   • Ini akan mereset koneksi jaringan
   ✓ Cek: Setelah toggle, device harusnya reconnect ke jaringan dalam 15-30 detik.

3. Restart koneksi data:
   • Matikan WiFi dan Mobile Data
   • Tunggu 10 detik
   • Nyalakan Mobile Data kembali
   ✓ Cek: Coba buka browser atau app TRAMOS untuk test koneksi.

4. Cek pengaturan APN:
   • Buka Settings → Mobile Network → APN
   • Pastikan APN sesu...
```

#### Turn 4

Driver:

```text
oke
```

Bot:

```text
🤔 Siap. Setelah dicoba, apakah masalahnya sudah benar-benar berhasil diperbaiki?

1️⃣ Ya, berhasil
2️⃣ Tidak, masih error

(Kirim nomor atau jawab langsung)
```

#### Turn 5

Driver:

```text
ya sudah berhasil
```

Bot:

```text
✅ Problem Teratasi!

Senang mendengar solusi yang kami berikan sudah fixed! 🎉

Tips untuk ke depannya:
  • Jika ada masalah lagi, hubungi kami kapan saja 😊

Jika ada masalah lagi, langsung hubungi kami ya 👍
Stay safe on the road! 🚗
```

## S04 - Invalid inputs and detail correction before ticket

Purpose: Validate bad name/problem/unit/location/time inputs, then correction flow creates ticket.

Phone/session test id: `62899006768404`

| # | Driver message | State | Bot response |
|---|---|---|---|
| 1 | halo | `none` -> `collecting_name` | Selamat Siang! 👋 Kami TRAMOS Support Bot 🤖 Siapa nama Anda? |
| 2 | A | `collecting_name` -> `collecting_name` | Nama-nya belum kedeteksi. Coba tulis nama lengkap ya 😊 |
| 3 | Dewi Anggraini | `collecting_name` -> `collecting_problem` | Terima kasih Dewi Anggraini! 😊 🤔 Ceritakan masalah yang Anda alami 1️⃣ GPS tidak berfungsi 2️⃣ Kamera error 3️⃣ Baterai cepat habis 4️⃣ Masalah koneksi (Kirim nomor atau jawab langsung) |
| 4 | ok | `collecting_problem` -> `collecting_problem` | Saya belum menangkap detail masalahnya. Tolong ceritakan kendala yang dialami driver/unit, misalnya: - GPS tidak update lokasi - Kamera mati atau layar hitam - Kendaraan mogok di jalan - Aplikasi error saat dipakai |
| 5 | aplikasi TRAMOS error blank screen saat buka laporan perjalanan | `collecting_problem` -> `asking_solution_worked` | Dewi Anggraini, ini solusi untuk masalah Application Anda: App yang error bisa bikin sistem seolah offline 😞 Jangan khawatir, kita handle ini bareng-bareng. Application & Software Issues - Mungkin ini solusinya Ini langkah-langkahnya: 1. Force close dan buka ulang: • Tutup aplikasi sepenuhnya (swipe up dari recent apps, jangan hanya tekan back) • Tunggu 5 detik • Buka lagi aplikasi TRAMOS ✓ Cek: Apakah app sudah b... |
| 6 | tidak berhasil | `asking_solution_worked` -> `collecting_unit` | Baik, saya akan eskalasi ke tim teknisi kami. Untuk membuat tiket laporan, saya butuh 3 informasi singkat: 1️⃣ Nama unit/kendaraan 2️⃣ Lokasi saat ini 3️⃣ Waktu kejadian Pertama, *unit atau kendaraan mana* yang bermasalah? (Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_) |
| 7 | oke | `collecting_unit` -> `collecting_unit` | Terima kasih 😊 Tapi saya butuh nama *unit/kendaraan* yang bermasalah ya. Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_ |
| 8 | Unit GPS-05 | `collecting_unit` -> `collecting_location` | ✅ Unit: *Unit GPS-05* Selanjutnya, *di mana lokasi* unit tersebut saat ini? Bisa sebut: • Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_) • Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_) • Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_) |
| 9 | siap | `collecting_location` -> `collecting_location` | Terima kasih 😊 Tapi saya butuh info *lokasi* unit/kendaraan saat ini ya. Contoh: _Jakarta_, _Tol Cikampek KM 5_, atau _Pool Cakung_ |
| 10 | Pool Cakung | `collecting_location` -> `collecting_time` | ✅ Lokasi: *Pool Cakung* Terakhir, *kapan masalah ini terjadi*? Bisa jawab dengan: • Jam spesifik (misal: _14:30_, _jam 3 sore_) • Waktu umum (misal: _tadi pagi_, _kemarin sore_) • _sekarang_ / _barusan_ jika baru terjadi |
| 11 | kemarin | `collecting_time` -> `collecting_time` | Maaf, saya kurang mengerti waktunya 🙏 Coba tulis ulang dengan format seperti: • _14:30_ atau _jam 3 sore_ • _tadi pagi_ atau _kemarin malam_ • _sekarang_ atau _barusan_ |
| 12 | kemarin sore | `collecting_time` -> `confirming_details` | 📋 *Ringkasan Tiket Laporan* ───────────────────────── 👤 Nama: Dewi Anggraini 🚛 Unit: Unit GPS-05 📍 Lokasi: Pool Cakung 🕐 Waktu: 15:00 🏷️ Kategori: Application 📝 Masalah: aplikasi TRAMOS error blank screen saat buka laporan perjalanan ───────────────────────── Apakah data di atas sudah benar? 🤔 1️⃣ *Ya*, lanjutkan buat tiket 2️⃣ *Tidak*, saya mau perbaiki |
| 13 | tidak, data salah | `confirming_details` -> `collecting_unit` | Baik, kita ulangi datanya ya. *Unit atau kendaraan mana* yang bermasalah? (Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_) |
| 14 | Unit GPS-06 | `collecting_unit` -> `collecting_location` | ✅ Unit: *Unit GPS-06* Selanjutnya, *di mana lokasi* unit tersebut saat ini? Bisa sebut: • Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_) • Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_) • Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_) |
| 15 | Depo Cilincing | `collecting_location` -> `collecting_time` | ✅ Lokasi: *Depo Cilincing* Terakhir, *kapan masalah ini terjadi*? Bisa jawab dengan: • Jam spesifik (misal: _14:30_, _jam 3 sore_) • Waktu umum (misal: _tadi pagi_, _kemarin sore_) • _sekarang_ / _barusan_ jika baru terjadi |
| 16 | 14:30 | `collecting_time` -> `confirming_details` | 📋 *Ringkasan Tiket Laporan* ───────────────────────── 👤 Nama: Dewi Anggraini 🚛 Unit: Unit GPS-06 📍 Lokasi: Depo Cilincing 🕐 Waktu: 14:30 🏷️ Kategori: Application 📝 Masalah: aplikasi TRAMOS error blank screen saat buka laporan perjalanan ───────────────────────── Apakah data di atas sudah benar? 🤔 1️⃣ *Ya*, lanjutkan buat tiket 2️⃣ *Tidak*, saya mau perbaiki |
| 17 | ya | `confirming_details` -> `closed` | ✅ **Tiket Berhasil Dibuat!** 📌 Nomor Tiket: #817264 🏷️ Kategori: Application 🚗 Equipment: Unit GPS-06 📍 Lokasi: Depo Cilincing ⏰ Waktu: 14:30 Tim support TRAMOS akan segera menangani masalah Anda. Kami akan menghubungi Anda berdasarkan detail yang Anda berikan. Terima kasih telah melaporkan! 🙏 |

### Full Dialog Transcript

#### Turn 1

Driver:

```text
halo
```

Bot:

```text
Selamat Siang! 👋

Kami TRAMOS Support Bot 🤖

Siapa nama Anda?
```

#### Turn 2

Driver:

```text
A
```

Bot:

```text
Nama-nya belum kedeteksi. Coba tulis nama lengkap ya 😊
```

#### Turn 3

Driver:

```text
Dewi Anggraini
```

Bot:

```text
Terima kasih Dewi Anggraini! 😊

🤔 Ceritakan masalah yang Anda alami

1️⃣ GPS tidak berfungsi
2️⃣ Kamera error
3️⃣ Baterai cepat habis
4️⃣ Masalah koneksi

(Kirim nomor atau jawab langsung)
```

#### Turn 4

Driver:

```text
ok
```

Bot:

```text
Saya belum menangkap detail masalahnya.

Tolong ceritakan kendala yang dialami driver/unit, misalnya:
- GPS tidak update lokasi
- Kamera mati atau layar hitam
- Kendaraan mogok di jalan
- Aplikasi error saat dipakai
```

#### Turn 5

Driver:

```text
aplikasi TRAMOS error blank screen saat buka laporan perjalanan
```

Bot:

```text
Dewi Anggraini, ini solusi untuk masalah Application Anda:

App yang error bisa bikin sistem seolah offline 😞 Jangan khawatir, kita handle ini bareng-bareng.


Application & Software Issues - Mungkin ini solusinya

Ini langkah-langkahnya:

1. Force close dan buka ulang:
   • Tutup aplikasi sepenuhnya (swipe up dari recent apps, jangan hanya tekan back)
   • Tunggu 5 detik
   • Buka lagi aplikasi TRAMOS
   ✓ Cek: Apakah app sudah bisa dibuka normal tanpa crash?

2. Clear cache aplikasi:
   • Buka Settings → Apps → TRAMOS → Storage → Clear Cache (BUKAN Clear Data)
   • Ini menghapus file sementara tanpa menghapus data penting
   ✓ Cek: Buka app lagi, cek apakah masalah masih ada.

3. Cek update aplikasi:
   • Buka Play Store/App Store → cari TRAMOS → cek apakah ada update tersedia
   • Jika ada, update ke versi terbaru
   ✓ Cek: Versi aplikasi sudah yang terbaru.

4. Reinstall aplikasi:
   • Jika semua langkah gagal, uninstall aplikasi TRAMOS
   • Install ulang dari Play Store/App Store
   • Login kembali dengan akun yang sama
   ✓ Cek: App terinstall fresh dan bisa login normal.

🤔 Coba langkah-langkah di atas. Berhasil nggak?

1️⃣ ✅ Ya, berhasil!
2️⃣ ❌ Tidak, masih error

(Kirim nomor atau jawab langsung)
```

#### Turn 6

Driver:

```text
tidak berhasil
```

Bot:

```text
Baik, saya akan eskalasi ke tim teknisi kami.

Untuk membuat tiket laporan, saya butuh 3 informasi singkat:
1️⃣ Nama unit/kendaraan
2️⃣ Lokasi saat ini
3️⃣ Waktu kejadian

Pertama, *unit atau kendaraan mana* yang bermasalah?
(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)
```

#### Turn 7

Driver:

```text
oke
```

Bot:

```text
Terima kasih 😊 Tapi saya butuh nama *unit/kendaraan* yang bermasalah ya.

Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_
```

#### Turn 8

Driver:

```text
Unit GPS-05
```

Bot:

```text
✅ Unit: *Unit GPS-05*

Selanjutnya, *di mana lokasi* unit tersebut saat ini?

Bisa sebut:
• Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_)
• Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_)
• Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_)
```

#### Turn 9

Driver:

```text
siap
```

Bot:

```text
Terima kasih 😊 Tapi saya butuh info *lokasi* unit/kendaraan saat ini ya.

Contoh: _Jakarta_, _Tol Cikampek KM 5_, atau _Pool Cakung_
```

#### Turn 10

Driver:

```text
Pool Cakung
```

Bot:

```text
✅ Lokasi: *Pool Cakung*

Terakhir, *kapan masalah ini terjadi*?

Bisa jawab dengan:
• Jam spesifik (misal: _14:30_, _jam 3 sore_)
• Waktu umum (misal: _tadi pagi_, _kemarin sore_)
• _sekarang_ / _barusan_ jika baru terjadi
```

#### Turn 11

Driver:

```text
kemarin
```

Bot:

```text
Maaf, saya kurang mengerti waktunya 🙏

Coba tulis ulang dengan format seperti:
• _14:30_ atau _jam 3 sore_
• _tadi pagi_ atau _kemarin malam_
• _sekarang_ atau _barusan_
```

#### Turn 12

Driver:

```text
kemarin sore
```

Bot:

```text
📋 *Ringkasan Tiket Laporan*
─────────────────────────
👤 Nama: Dewi Anggraini
🚛 Unit: Unit GPS-05
📍 Lokasi: Pool Cakung
🕐 Waktu: 15:00
🏷️ Kategori: Application
📝 Masalah: aplikasi TRAMOS error blank screen saat buka laporan perjalanan
─────────────────────────

Apakah data di atas sudah benar? 🤔

1️⃣ *Ya*, lanjutkan buat tiket
2️⃣ *Tidak*, saya mau perbaiki
```

#### Turn 13

Driver:

```text
tidak, data salah
```

Bot:

```text
Baik, kita ulangi datanya ya.

*Unit atau kendaraan mana* yang bermasalah?
(Contoh: _B 1234 AB_, _TRAM-001_, _Unit GPS-05_, atau _nama perusahaan_)
```

#### Turn 14

Driver:

```text
Unit GPS-06
```

Bot:

```text
✅ Unit: *Unit GPS-06*

Selanjutnya, *di mana lokasi* unit tersebut saat ini?

Bisa sebut:
• Nama kota/kabupaten (misal: _Jakarta_, _Surabaya_)
• Area/jalan (misal: _Tol Cikampek KM 5_, _Bandara Soetta_)
• Pool/garasi (misal: _Pool Cakung_, _Depo Cilincing_)
```

#### Turn 15

Driver:

```text
Depo Cilincing
```

Bot:

```text
✅ Lokasi: *Depo Cilincing*

Terakhir, *kapan masalah ini terjadi*?

Bisa jawab dengan:
• Jam spesifik (misal: _14:30_, _jam 3 sore_)
• Waktu umum (misal: _tadi pagi_, _kemarin sore_)
• _sekarang_ / _barusan_ jika baru terjadi
```

#### Turn 16

Driver:

```text
14:30
```

Bot:

```text
📋 *Ringkasan Tiket Laporan*
─────────────────────────
👤 Nama: Dewi Anggraini
🚛 Unit: Unit GPS-06
📍 Lokasi: Depo Cilincing
🕐 Waktu: 14:30
🏷️ Kategori: Application
📝 Masalah: aplikasi TRAMOS error blank screen saat buka laporan perjalanan
─────────────────────────

Apakah data di atas sudah benar? 🤔

1️⃣ *Ya*, lanjutkan buat tiket
2️⃣ *Tidak*, saya mau perbaiki
```

#### Turn 17

Driver:

```text
ya
```

Bot:

```text
Baik, sedang membuat tiket support untuk Anda... ⏳
```

#### Turn 18

Driver:

```text
(system/no user message)
```

Bot:

```text
✅ **Tiket Berhasil Dibuat!**

📌 Nomor Tiket: #817264
🏷️ Kategori: Application
🚗 Equipment: Unit GPS-06
📍 Lokasi: Depo Cilincing
⏰ Waktu: 14:30

Tim support TRAMOS akan segera menangani masalah Anda.
Kami akan menghubungi Anda berdasarkan detail yang Anda berikan.

Terima kasih telah melaporkan! 🙏
```

## S05 - New issue after resolved session starts cleanly

Purpose: After a resolved case, a new message should start a fresh conversation instead of reusing old state.

Phone/session test id: `62899014587505`

| # | Driver message | State | Bot response |
|---|---|---|---|
| 1 | halo | `none` -> `collecting_name` | Selamat Siang! 👋 Kami TRAMOS Support Bot 🤖 Siapa nama Anda? |
| 2 | Eko Saputra | `collecting_name` -> `collecting_problem` | Terima kasih Eko Saputra! 😊 🤔 Ceritakan masalah yang Anda alami 1️⃣ GPS tidak berfungsi 2️⃣ Kamera error 3️⃣ Baterai cepat habis 4️⃣ Masalah koneksi (Kirim nomor atau jawab langsung) |
| 3 | baterai device cepat habis dan indikator power turun terus | `collecting_problem` -> `asking_solution_worked` | Eko Saputra, ini solusi untuk masalah Device Anda: Ada masalah yang mengganggu, saya bantu cari solusinya 💪 Jangan khawatir, kita handle ini bareng-bareng. Device Hardware & Software Issues - Sangat yakin ini solusinya Ini langkah-langkahnya: 1. Restart device sepenuhnya: • Matikan device sepenuhnya (bukan sleep) • Tunggu 1 menit penuh • Nyalakan kembali ✓ Cek: Setelah restart, cek apakah masalah masih terjadi. 2.... |
| 4 | berhasil, sudah normal | `asking_solution_worked` -> `resolved` | ✅ Problem Teratasi! Senang mendengar solusi yang kami berikan sudah fixed! 🎉 Tips untuk ke depannya: • Jika ada masalah lagi, hubungi kami kapan saja 😊 Jika ada masalah lagi, langsung hubungi kami ya 👍 Stay safe on the road! 🚗 |
| 5 | halo ada masalah baru | `resolved` -> `collecting_name` | Selamat Siang! 👋 Kami TRAMOS Support Bot 🤖 Siapa nama Anda? |

### Full Dialog Transcript

#### Turn 1

Driver:

```text
halo ada masalah baru
```

Bot:

```text
Selamat Siang! 👋

Kami TRAMOS Support Bot 🤖

Siapa nama Anda?
```

## Notes for Thesis

- Resolved cases end in `resolved` and do not create an osTicket ticket.
- Escalated cases collect unit, location, and incident time before ticket creation.
- Ambiguous acknowledgements after troubleshooting are clarified before the system closes the case.
- Invalid collection inputs are rejected and the same state is repeated until usable data is provided.
- Ticket scenarios create real tickets in the configured local osTicket instance.
