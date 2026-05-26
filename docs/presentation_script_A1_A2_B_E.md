# Script Presentasi Form 4 - Bagian A.1, A.2, B, dan E

Topik: Design and Development of a WhatsApp-Based Issue Reporting and Analytics Dashboard System for TRAMOS Web at PT Andakara Informatika Nusantara

Pembicara: Ivander Johana Pratama

## Pembuka

Selamat pagi/siang, Bapak/Ibu dosen.

Pada kesempatan ini, saya akan menjelaskan bagian implementasi dan tampilan produk dari sistem TRAMOS. Bagian yang akan saya jelaskan mencakup bagian A.1, yaitu implementation of functions, procedures, and classes, yang terdiri dari subbagian 1.1 sampai 1.3. Setelah itu saya akan menjelaskan bagian A.2 mengenai database implementation, bagian B mengenai product display, dan bagian E mengenai manual guide.

Secara umum, TRAMOS adalah sistem pelaporan masalah berbasis WhatsApp yang terintegrasi dengan AI chatbot, osTicket, PostgreSQL database, dan analytics dashboard. Sistem ini dirancang agar driver atau staff dapat melaporkan kendala operasional melalui WhatsApp, kemudian chatbot akan menganalisis masalah tersebut. Jika masalah dapat diselesaikan oleh AI, maka sistem akan memberikan solusi otomatis. Namun jika tidak dapat diselesaikan, sistem akan membuat ticket secara otomatis ke osTicket.

## A.1 Functions, Procedure, and Class Implementation

Pada bagian A.1, kami membagi implementasi fungsi utama sistem menjadi tiga bagian, yaitu WhatsApp Webhook and AI Intent Processing, Auto-Ticketing API Integration, dan Analytics Dashboard.

## 1.1 WhatsApp Webhook and AI Intent Processing

Untuk subbagian 1.1, kami mengimplementasikan WhatsApp Webhook and AI Intent Processing sebagai pintu masuk utama komunikasi antara user dan sistem TRAMOS.

Ketika driver atau staff mengirim pesan melalui WhatsApp, pesan tersebut akan diterima oleh webhook backend yang terhubung dengan Meta WhatsApp Business API. Di dalam backend, pesan yang masuk akan diproses oleh fungsi `handle_incoming_message`.

Fungsi `handle_incoming_message` bertugas untuk membaca data pesan yang diterima, mengambil informasi pengirim, memeriksa isi pesan, lalu meneruskan pesan tersebut ke proses chatbot. Jadi, fungsi ini menjadi penghubung awal antara pesan dari WhatsApp dan logic utama sistem TRAMOS.

Setelah pesan diterima, sistem menjalankan fungsi `process_message_with_ai`. Fungsi ini digunakan untuk mengatur alur percakapan chatbot. Dalam implementasinya, chatbot menggunakan pendekatan state machine. Artinya, chatbot memahami posisi user dalam percakapan, bukan hanya membalas satu pesan secara acak.

Sebagai contoh, pada awal percakapan, sistem akan menyapa user dan meminta nama. Setelah nama diberikan, sistem akan meminta deskripsi masalah. Setelah masalah dijelaskan, sistem akan menganalisis kategori masalah tersebut dan menentukan langkah berikutnya.

Pendekatan state machine ini penting karena laporan dari user biasanya tidak selalu lengkap. User bisa saja hanya mengetik "aplikasi error", "GPS tidak update", atau "mobil bermasalah". Karena itu, chatbot perlu mengumpulkan informasi secara bertahap agar laporan yang diterima sistem lebih jelas dan terstruktur.

Selain itu, sistem juga menggunakan Natural Language Processing atau NLP untuk mengenali maksud dari pesan user. Dari pesan tersebut, AI dapat mengklasifikasikan masalah ke dalam kategori tertentu, seperti application issue, GPS issue, service issue, equipment issue, atau kategori lainnya.

Setelah kategori dikenali, sistem akan mencari solusi yang sesuai dari knowledge base. Jika solusi tersedia, chatbot akan memberikan langkah troubleshooting kepada user. Setelah itu chatbot akan menanyakan apakah solusi tersebut berhasil atau tidak.

Jadi, pada subbagian 1.1 ini, fokus implementasinya adalah bagaimana pesan WhatsApp diterima, diproses, dianalisis oleh AI, dan diarahkan ke alur percakapan yang sesuai.

## 1.2 Auto-Ticketing API Integration

Selanjutnya, pada subbagian 1.2, kami mengimplementasikan Auto-Ticketing API Integration.

Modul ini digunakan ketika masalah yang dilaporkan user tidak berhasil diselesaikan oleh solusi otomatis dari AI. Dalam kondisi tersebut, sistem akan melakukan eskalasi dengan membuat ticket baru ke osTicket.

Fungsi utama pada bagian ini adalah `_create_ticket_from_session`. Fungsi ini mengambil informasi dari sesi percakapan user, seperti nama pelapor, deskripsi masalah, kategori masalah, unit kendaraan atau equipment, lokasi kejadian, dan waktu kejadian.

Data tersebut tidak langsung dikirim begitu saja, tetapi dikumpulkan terlebih dahulu melalui dialog chatbot. Misalnya, ketika user mengatakan bahwa solusi belum berhasil, bot akan bertanya data tambahan seperti unit kendaraan, lokasi, dan waktu masalah terjadi. Setelah semua data lengkap, sistem akan menampilkan ringkasan laporan kepada user untuk dikonfirmasi.

Jika user menyetujui ringkasan tersebut, sistem akan mengirim data ke osTicket menggunakan REST API. Setelah ticket berhasil dibuat, osTicket akan mengembalikan ticket ID, lalu chatbot menampilkan nomor ticket tersebut kepada user.

Implementasi ini membantu mengurangi pekerjaan manual support operator. Sebelumnya, laporan masalah harus dicatat secara manual atau dipindahkan secara manual ke sistem ticketing. Dengan integrasi ini, laporan yang tidak terselesaikan dapat langsung masuk ke osTicket secara otomatis.

Selain itu, proses ini juga menjaga traceability. Artinya, setiap ticket yang dibuat tetap dapat ditelusuri kembali ke percakapan awal user. Hal ini membantu support operator memahami konteks masalah sebelum melakukan penanganan.

Jadi, pada subbagian 1.2 ini, fokus implementasinya adalah proses eskalasi otomatis dari percakapan chatbot menjadi ticket resmi di osTicket.

## 1.3 Analytics Dashboard

Pada subbagian 1.3, kami mengimplementasikan Analytics Dashboard sebagai media visualisasi dan monitoring performa sistem TRAMOS.

Dashboard ini dikembangkan menggunakan React pada bagian frontend dan terhubung dengan backend API. Salah satu fungsi penting pada bagian ini adalah `fetchData`, yang digunakan untuk mengambil data dari backend.

Data yang diambil mencakup informasi seperti total conversations, total tickets, total messages, issue category distribution, urgency distribution, system health metrics, dan AI performance metrics.

Dashboard ini membantu management analyst dan admin untuk memantau kondisi sistem tanpa perlu membaca semua percakapan satu per satu. Misalnya, management dapat melihat kategori masalah apa yang paling sering muncul, berapa banyak masalah yang dapat diselesaikan oleh AI, dan berapa banyak masalah yang harus dieskalasikan menjadi ticket.

Selain itu, dashboard juga menampilkan insight berbasis data. Dengan adanya data ini, perusahaan dapat mengetahui pola masalah operasional. Contohnya, jika dalam periode tertentu banyak laporan terkait GPS atau aplikasi, maka management dapat mengambil keputusan untuk melakukan perbaikan pada area tersebut.

Dashboard juga dirancang dengan komponen modular seperti summary cards, charts, dan filter berdasarkan tanggal. Dengan desain ini, pengguna dapat melihat data harian, mingguan, atau bulanan sesuai kebutuhan.

Jadi, pada subbagian 1.3 ini, fokus implementasinya adalah bagaimana data dari chatbot, database, dan ticketing system divisualisasikan menjadi informasi yang mudah dianalisis oleh pihak management.

## A.2 Database Implementation

Selanjutnya, pada bagian A.2, saya akan menjelaskan implementasi database pada sistem TRAMOS.

Dalam project ini, kami menggunakan PostgreSQL sebagai database utama. PostgreSQL dipilih karena sistem TRAMOS membutuhkan database yang kuat untuk menangani data transactional dan relational. Data yang dikelola sistem cukup kompleks, seperti data user, conversation, message history, AI processing, ticketing, session, dan analytics.

Alasan pertama penggunaan PostgreSQL adalah karena mendukung ACID compliance. Hal ini penting untuk menjaga konsistensi data, terutama pada proses pembuatan ticket. Ketika ticket berhasil dibuat, data percakapan, data ticket, dan data analytics harus tersimpan dengan benar dan tidak boleh terpisah.

Alasan kedua adalah data relationship integrity. Di dalam sistem TRAMOS, banyak data yang saling berhubungan. Contohnya, satu user dapat memiliki banyak conversation, satu conversation dapat memiliki banyak message history, dan satu conversation juga dapat menghasilkan satu ticket jika masalah tidak terselesaikan.

Dengan foreign key seperti `user_id`, `conversation_id`, dan `ticket_id`, sistem dapat melacak hubungan data secara jelas. Ini berguna ketika support operator atau analyst ingin melihat asal-usul sebuah ticket dari percakapan WhatsApp.

Alasan ketiga adalah kemampuan query PostgreSQL yang baik. Dashboard membutuhkan query agregasi seperti menghitung jumlah conversation, menghitung total ticket, melihat kategori masalah terbanyak, dan menghitung AI resolution rate. PostgreSQL mendukung operasi join dan aggregate function yang dibutuhkan untuk proses analytics tersebut.

Secara struktur, database TRAMOS dibagi menjadi beberapa kelompok tabel.

Kelompok pertama adalah Conversation and Messaging System. Bagian ini berisi tabel seperti `conversations`, `message_history`, `conversation_turns`, dan `conversation_context`. Fungsinya adalah menyimpan riwayat percakapan user dengan chatbot, termasuk konteks percakapan yang sedang berlangsung.

Kelompok kedua adalah AI Processing and Solution Tracking. Bagian ini berisi tabel seperti `solution_attempts`, `solutions`, dan `solution_effectiveness`. Fungsinya adalah mencatat solusi yang diberikan AI dan mengevaluasi apakah solusi tersebut berhasil membantu user.

Kelompok ketiga adalah Ticketing System. Bagian ini berisi tabel `tickets`, yang terhubung dengan user dan conversation. Tabel ini digunakan untuk menyimpan ticket yang dibuat otomatis dari percakapan chatbot dan menjaga sinkronisasi dengan osTicket.

Kelompok keempat adalah Analytics and Dashboard System. Bagian ini berisi tabel seperti `analytics_data`, `dashboard_analytics_summary`, dan `dashboard_users`. Tabel ini digunakan untuk menyimpan data mentah dan data ringkasan agar dashboard dapat menampilkan informasi dengan cepat.

Kelompok terakhir adalah User and Session Management. Bagian ini berisi tabel seperti `users`, `user_profile_data`, dan `whatsapp_sessions`. Fungsinya adalah mengelola data pengguna, profil, session, dan role user dalam sistem.

Dengan struktur database ini, seluruh modul TRAMOS dapat saling terhubung. Data dari WhatsApp chatbot dapat tersimpan di database, data ticket dapat ditelusuri kembali, dan dashboard dapat mengambil data yang sudah diproses untuk ditampilkan sebagai analytics.

Jadi, database pada sistem TRAMOS tidak hanya berfungsi sebagai tempat penyimpanan, tetapi juga sebagai pusat integrasi antara chatbot, AI processing, ticketing, dan dashboard analytics.

## B. Product Display

Pada bagian B, kami menampilkan hasil product display atau tampilan produk yang sudah diimplementasikan dalam sistem TRAMOS.

Tampilan pertama adalah Authentication Interface. Halaman ini menjadi pintu masuk bagi user yang ingin mengakses dashboard TRAMOS. User dapat melakukan login menggunakan email dan password. Selain itu, sistem juga mendukung Google Sign-In agar proses login lebih mudah.

Authentication interface ini penting karena dashboard berisi data operasional, ticket, dan hasil analisis sistem. Oleh karena itu, hanya user yang terdaftar dan terverifikasi yang boleh mengakses dashboard.

Selain login, sistem juga memiliki halaman sign up. Pada halaman ini, user mengisi data seperti full name, email, phone number, dan password. Setelah registrasi, sistem dapat melakukan verifikasi OTP melalui email. Dengan proses ini, sistem memastikan bahwa akun yang dibuat valid dan dapat digunakan secara aman.

Setelah login berhasil, user akan masuk ke Overview Dashboard Interface. Halaman ini menampilkan ringkasan data operasional dari sistem TRAMOS. Beberapa informasi yang ditampilkan antara lain total conversations, total tickets, total messages, AI resolution rate, issue category distribution, urgency level distribution, dan session quality.

Dashboard ini dibuat agar management analyst dapat memahami kondisi operasional dengan cepat. Jika sebelumnya data laporan harus dibaca satu per satu, sekarang data tersebut dapat diringkas dalam bentuk summary card dan chart.

Selain Overview Dashboard, sistem juga memiliki AI Performance Page. Halaman ini digunakan untuk mengevaluasi performa chatbot. Data yang ditampilkan mencakup jumlah masalah yang berhasil diselesaikan oleh AI, jumlah eskalasi ke ticket, dan kualitas percakapan chatbot.

Dengan halaman ini, admin dapat mengetahui apakah chatbot sudah cukup efektif dalam mengurangi beban support operator. Jika banyak masalah tetap dieskalasikan, maka knowledge base atau flow chatbot dapat diperbaiki.

Tampilan berikutnya adalah Reports and Notifications Page. Halaman ini digunakan sebagai pusat monitoring status sistem. Di dalamnya terdapat informasi mengenai kondisi backend, database, AI processing, WhatsApp integration, osTicket integration, dan analytics processing.

Halaman ini juga menyediakan ringkasan laporan dan rekomendasi berbasis AI. Tujuannya adalah membantu admin dan management melihat masalah yang sering muncul serta menentukan prioritas perbaikan.

Selanjutnya adalah WhatsApp AI Chatbot Interface. Ini adalah interface utama untuk driver atau field user. User tidak perlu menginstal aplikasi tambahan karena cukup menggunakan WhatsApp untuk melaporkan masalah.

Pada awal percakapan, chatbot akan menyapa user dan meminta nama. Setelah itu, bot meminta user menjelaskan masalah yang dialami. Berdasarkan pesan tersebut, sistem akan menganalisis kategori masalah dan memberikan solusi yang sesuai.

Contohnya, jika user melaporkan aplikasi error, bot dapat memberikan langkah troubleshooting seperti force close aplikasi, membuka ulang aplikasi, mengecek koneksi internet, atau mengikuti instruksi perbaikan lainnya. Setelah solusi diberikan, chatbot akan bertanya apakah masalah sudah selesai.

Jika user menjawab bahwa masalah sudah selesai, maka sistem akan menutup percakapan tanpa membuat ticket. Ini penting karena ticket hanya dibuat untuk masalah yang memang tidak dapat diselesaikan secara otomatis.

Namun jika user menjawab bahwa masalah belum selesai, sistem akan masuk ke alur eskalasi. Chatbot akan meminta data tambahan seperti unit kendaraan, lokasi kejadian, dan waktu kejadian. Setelah data lengkap, sistem menampilkan ringkasan laporan dan meminta konfirmasi user.

Jika user mengonfirmasi, sistem akan membuat ticket otomatis ke osTicket dan mengirimkan nomor ticket kepada user. Dengan begitu, user memiliki bukti laporan dan support operator dapat langsung menangani masalah tersebut.

Selain chatbot, TRAMOS juga memiliki Email Notification Integration. Setelah ticket dibuat, sistem dapat mengirim email otomatis ke support. Email tersebut berisi detail ticket seperti ticket ID, kategori masalah, data user, deskripsi masalah, prioritas, waktu, dan link menuju ticket di osTicket.

Terakhir adalah osTicket Ticket Management Interface. Pada halaman ini, support operator dapat melihat ticket yang masuk, membaca detail masalah, melihat status ticket, mengatur prioritas, dan memberikan update penanganan.

Integrasi dengan osTicket membuat proses eskalasi lebih rapi karena semua masalah yang tidak terselesaikan oleh AI masuk ke sistem helpdesk yang terstruktur.

Jadi, pada bagian Product Display, sistem TRAMOS menunjukkan alur lengkap dari login dashboard, monitoring analytics, interaksi WhatsApp chatbot, pembuatan ticket otomatis, notifikasi email, hingga pengelolaan ticket melalui osTicket.

## E. Manual Guide

Pada bagian E, kami menjelaskan manual guide atau panduan penggunaan sistem. Bagian ini dibagi menjadi developer perspective, end-user perspective, dan user guide berdasarkan role.

Pertama, dari developer perspective, terdapat beberapa prerequisite yang dibutuhkan untuk menjalankan sistem TRAMOS. Komponen yang dibutuhkan adalah Python 3.10 atau versi lebih baru, PostgreSQL, Node.js, npm, ngrok, osTicket, Meta WhatsApp Business Account, dan Gemini API Key.

Untuk menjalankan backend, developer masuk ke direktori project TRAMOS, membuat virtual environment, mengaktifkan environment, lalu menginstall dependencies dari file `requirements.txt`. Setelah itu backend dapat dijalankan menggunakan perintah `uvicorn main:app --reload --host 0.0.0.0 --port 9999`.

Untuk setup database, developer perlu membuat database PostgreSQL untuk menyimpan data TRAMOS. Database ini akan digunakan untuk menyimpan data user, percakapan, message history, ticket, session, dan analytics.

Untuk menjalankan frontend dashboard, developer masuk ke folder `dashboard`, menjalankan `npm install`, lalu menjalankan `npm run dev`. Setelah itu dashboard dapat diakses melalui browser.

Untuk menjalankan integrasi WhatsApp, developer perlu menggunakan ngrok. Ngrok digunakan agar backend lokal dapat diakses dari internet oleh Meta WhatsApp webhook. Setelah URL ngrok aktif, URL tersebut dimasukkan ke Meta Developer Dashboard sebagai callback URL.

Pada konfigurasi webhook, developer juga harus memastikan verify token yang ada di Meta sama dengan verify token pada backend. Selain itu, field `messages` harus disubscribe agar sistem dapat menerima pesan masuk dari WhatsApp.

Untuk osTicket integration, developer perlu menyiapkan API key dari osTicket dan memasukkan osTicket base URL ke dalam file environment. Setelah itu sistem dapat mengirim request ke osTicket untuk membuat ticket secara otomatis.

Kedua, dari end-user perspective, driver atau field user hanya membutuhkan smartphone, aplikasi WhatsApp, dan koneksi internet. User cukup menyimpan nomor WhatsApp TRAMOS, lalu mengirim laporan masalah melalui chat. Setelah itu user mengikuti pertanyaan dari chatbot.

Jika masalah dapat diselesaikan oleh AI, user akan menerima solusi dan tidak perlu membuat ticket. Jika masalah tidak selesai, chatbot akan membantu user membuat ticket dengan meminta data tambahan seperti unit, lokasi, dan waktu kejadian.

Untuk dashboard user, seperti management analyst, user membutuhkan browser dan akun dashboard. Setelah login, user dapat melihat analytics dashboard untuk memantau total conversation, total ticket, kategori masalah, dan insight operasional.

Untuk support operator, user membutuhkan akun osTicket. Operator dapat login ke osTicket dashboard, melihat ticket yang masuk, membaca detail laporan, mengubah status ticket, dan menyelesaikan ticket.

Ketiga, dari sisi user guide per role, sistem TRAMOS memiliki tiga role utama.

Role pertama adalah Driver atau Staff. Role ini menggunakan WhatsApp chatbot untuk mengirim laporan masalah, menerima solusi dari AI, dan membuat ticket jika masalah tidak dapat diselesaikan.

Role kedua adalah Management Analyst. Role ini menggunakan analytics dashboard untuk melihat ringkasan data, grafik kategori masalah, statistik ticket, dan insight operasional.

Role ketiga adalah Support Operator. Role ini menggunakan osTicket dashboard untuk memantau ticket, menindaklanjuti laporan, memperbarui status ticket, dan menyelesaikan masalah.

Dengan manual guide ini, setiap user memiliki alur penggunaan yang jelas sesuai perannya masing-masing. Developer dapat menjalankan dan mengintegrasikan sistem, driver dapat melaporkan masalah, management dapat menganalisis data, dan support operator dapat menangani ticket.

## Penutup

Sebagai kesimpulan, bagian yang saya jelaskan menunjukkan bahwa TRAMOS dibangun sebagai sistem yang terintegrasi dari awal sampai akhir. Pesan dari WhatsApp diterima oleh webhook, diproses oleh AI chatbot, disimpan di PostgreSQL, dan jika diperlukan akan dieskalasikan menjadi ticket di osTicket.

Selain itu, data dari proses tersebut divisualisasikan melalui analytics dashboard sehingga management dapat memantau performa sistem dan tren masalah operasional. Dengan sistem ini, proses pelaporan masalah menjadi lebih cepat, lebih terstruktur, dan lebih mudah dianalisis.

Terima kasih.

## Versi Sangat Singkat Jika Waktu Presentasi Mepet

Bagian A.1 terdiri dari tiga implementasi utama. Pertama, WhatsApp Webhook and AI Intent Processing menerima pesan dari user, memproses isi pesan, dan mengatur flow chatbot menggunakan state machine. Kedua, Auto-Ticketing API Integration membuat ticket otomatis ke osTicket jika masalah tidak bisa diselesaikan oleh AI. Ketiga, Analytics Dashboard menampilkan data conversation, ticket, issue category, urgency, dan AI performance.

Bagian A.2 menjelaskan PostgreSQL sebagai database utama. Database ini menyimpan percakapan, pesan, hasil analisis AI, ticket, session, user, dan data analytics. Database juga menjadi pusat integrasi antar modul.

Bagian B menjelaskan tampilan produk, mulai dari login, sign up, overview dashboard, AI performance page, reports and notifications, WhatsApp chatbot, email notification, dan osTicket ticket management.

Bagian E menjelaskan manual guide. Developer menjalankan backend, database, frontend, ngrok, WhatsApp webhook, dan osTicket integration. Driver menggunakan WhatsApp untuk melapor, management analyst menggunakan dashboard untuk analisis, dan support operator menggunakan osTicket untuk menangani ticket.

