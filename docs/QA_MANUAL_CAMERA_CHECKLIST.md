# Checklist Uji Manual Kamera & MediaPipe Worker (webcam fisik)

Tujuan: memverifikasi hal yang **tidak dapat** dibuktikan otomatis: webcam fisik, deteksi pose/tangan MANUSIA, dan kinerja perangkat nyata. Lakukan di **Chrome** dan **Safari** (macOS) pada laptop masing-masing; Firefox bila tersedia.

> **Pisahkan hasil.** Bagian A (otomatis/simulasi) sudah dijalankan di CI dengan kamera PALSU dan **tidak boleh** dilaporkan sebagai hasil webcam. Bagian B hanya boleh diisi dari pengujian nyata oleh Anda. Jangan menulis "lulus" untuk langkah yang tidak benar-benar Anda lakukan.

## Aturan privasi untuk penguji
- **Jangan merekam/menyimpan/membagikan video atau foto wajah/tubuh Anda.** Halaman ini tidak menyimpan apa pun; jangan menambahkannya lewat OBS/screen recorder.
- Screenshot laporan: **hanya** panel status/metrik (tutup preview atau gunakan latar netral). Jangan unggah gambar yang memuat wajah. Hapus tangkapan layar setelah laporan terisi.
- Jangan menaruh file hasil benchmark berisi data pribadi (JSON benchmark tidak berisi gambar/landmark, tetapi periksa `userAgent`/label kamera sebelum dibagikan).

## Bagian A — yang SUDAH diuji otomatis (kamera PALSU Chromium; bukan bukti webcam/manusia)
Lifecycle kamera; worker dibuat dari origin sendiri dan ditutup saat stop/navigasi/`pagehide`; izin ditolak (simulasi), kamera tidak ada, kamera sibuk, konteks tidak aman, kegagalan init model/worker (tanpa fallback sinkron); tidak ada request mutasi/storage/log landmark; responsivitas UI sintetis; benchmark A/B sintetis. Lihat `docs/AI_CV_FOUNDATION.md`.

## Bagian B — pengujian NYATA (isi oleh Anggota C / penguji)
### Persiapan
1. `make start` dan `make mediapipe-assets` (sekali). Buka `http://localhost:<FRONTEND_PORT>` — **harus `localhost`** (IP LAN/domain tanpa HTTPS memblokir kamera). Port dari `.env` (mis. 3010).
2. Masuk dengan akun demo (`demo-pelajar@silatara.test`, sandi demo di README). Buka **Uji Kamera** (`/app/practice/camera-check`).
3. Posisi 1,5–2 m dari laptop, seluruh tubuh kepala–kaki dalam frame, cahaya depan memadai, hanya Anda di frame.

### Langkah (satu laporan per perangkat × browser)
| # | Langkah | Hasil yang diharapkan | Lulus? (isi sendiri) |
|---|---|---|---|
| 1 | Muat halaman tanpa klik | Pemberitahuan privasi tampil; lampu kamera **mati**; browser **tidak** meminta izin | |
| 2 | Klik "Saya mengerti, nyalakan kamera" → **Izinkan** | Preview tampil, lampu kamera menyala; tidak ada permintaan mikrofon | |
| 3 | Klik "Nyalakan deteksi landmark" | "Memuat model di thread latar…"; **halaman tetap bisa digulir/diklik**; panel Metrik teknis muncul; status worker "ready" | |
| 4 | Berdiri penuh di frame | Kerangka menempel ke tubuh; status "Siap dianalisis" setelah stabil | |
| 5 | Amati lancar/tidaknya UI saat deteksi berjalan (gulir halaman, geser jendela) | Tidak membeku. Catat bila ada jeda terlihat | |
| 6 | Angkat tangan ke kamera | Frame bertangan bertambah di panel (tangan terdeteksi) | |
| 7 | Keluar sebagian dari frame | "Belum dapat dianalisis" + saran OUT_OF_FRAME | |
| 8 | Tutup lensa / matikan lampu | NO_POSE / visibilitas rendah | |
| 9 | Masukkan orang kedua | "Terdeteksi lebih dari satu orang" | |
| 10 | Pindah tab lain ±10 detik lalu kembali | Status worker "paused" lalu "ready" lagi; kamera tetap aktif | |
| 11 | "Matikan deteksi landmark" | Panel metrik hilang; (DevTools → Sources/Application: worker berhenti) | |
| 12 | "Hentikan kamera" | Lampu kamera **mati segera** | |
| 13 | Nyalakan lagi, pindah halaman | Lampu kamera mati saat berpindah halaman | |
| 14 | Nyalakan lagi, **tutup tab** | Lampu kamera mati | |
| 15 | Percobaan baru: **Blokir** izin | "Izin kamera ditolak…"; tombol mulai tersedia lagi | |
| 16 | Kamera dipakai aplikasi lain (mis. Zoom) lalu coba nyalakan | Pesan "sedang dipakai aplikasi lain"; tidak macet | |
| 17 | (Bila ada) kamera eksternal → "Pilih kamera" | Dropdown terisi; berganti kamera setelah Hentikan→Nyalakan | |
| 18 | DevTools → Network selama langkah 2–9 | **Tidak ada** POST/PUT/unggahan; aset dari `localhost`; Console tanpa error merah | |
| 19 | Buka `/app/practice/benchmark`, jalankan benchmark (frame 30, ulangan 3) — **peringatan: tab baseline akan membeku** | Tabel hasil + JSON; salin ke laporan | |

### Template laporan (salin ke `docs/qa-reports/AAAA-MM-DD-<inisial>-<browser>.md`)
```
Penguji (inisial):                 Tanggal:
BAGIAN: pengujian NYATA (bukan simulasi)   [ya/tidak]
OS & versi:
Perangkat (model/tahun/CPU/RAM/GPU):
Browser & versi:                   (Chrome / Safari / Firefox)
Kamera (bawaan/eksternal, merek/model):
Resolusi video (dari panel):       Resolusi layar:
URL (harus http://localhost:…):

Izin kamera (diminta setelah klik? hasil Izinkan/Blokir):
Status model loading (berhasil? pesan galat?):
Delegasi (GPU/CPU) & versi pustaka (dari benchmark):
Pose inference (kerangka sesuai tubuh? subjek manusia sungguhan: ya/tidak):
Hand inference (tangan terdeteksi? ya/tidak):
Frame latency (dari panel: n=__ rata-rata __ median __ p95 __ ms):
Inisialisasi model __ ms | startup worker __ ms | frame diproses __ | dilewati(backpressure) __ | dibuang worker __ | error __
Responsivitas: jeda rAF terbesar __ ms | jeda event-loop terbesar __ ms | long task __
UI terasa membeku saat deteksi? (ya/tidak; berapa lama; saat apa):
Quality gate teramati (Siap / OUT_OF_FRAME / NO_POSE / MULTIPLE_PEOPLE / lainnya):
Worker berhenti saat: matikan deteksi / hentikan kamera / pindah halaman / tutup tab ? (ya/tidak per kasus)
Lampu kamera mati saat: stop / pindah halaman / tutup tab ? (ya/tidak per kasus)
Request jaringan mencurigakan (POST/unggahan)? (ya/tidak):
Warning/Error konsol (salin teks, tanpa data pribadi):
Hasil langkah 1–19 (nomor yang gagal + catatan):
Screenshot (hanya panel status/metrik, tanpa wajah/tubuh) — nama berkas:
File benchmark JSON (lampirkan di docs/benchmarks/ setelah memeriksa isi):
Catatan lain:
```
**Larangan klaim:** angka dari satu perangkat/satu sesi tidak boleh dikutip sebagai FPS/akurasi produk. Deteksi yang "terlihat benar" bukan bukti akurasi; akurasi hanya dinilai terhadap anotasi/instruktur pada protokol evaluasi terpisah (C3). Sistem hanya melaporkan **kualitas input**; tidak ada skor/koreksi gerakan sebelum rubrik instruktur mitra disetujui.
