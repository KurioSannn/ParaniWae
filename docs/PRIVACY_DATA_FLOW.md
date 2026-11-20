# Audit alur data kamera & privasi (setelah pemindahan ke Web Worker)

Hasil audit 20 Nov 2026. Bukti: tes otomatis (vitest + Playwright) yang disebutkan; hal yang tidak dapat dibuktikan ditandai.

## Alur data
```
Kamera (getUserMedia, audio:false, hanya setelah klik)
  └─> <video> (memori; tidak di-render ke jaringan)
        └─> createImageBitmap ──transfer──> Web Worker (same-origin) ──> MediaPipe (wasm+model dari origin sendiri)
                                         <── LandmarkFrame (angka) ── postMessage
              └─> quality gate + gambar kerangka di <canvas> (memori)
```
Tidak ada cabang ke jaringan/penyimpanan/log. Backend **tidak memiliki** endpoint penerima media/frame/landmark (diuji: `test_api_has_no_video_or_frame_upload_surface` memindai OpenAPI).

## Practice Studio (sesi latihan)
Yang dikirim ke backend hanya **metadata sesi + angka agregat kualitas input** (`POST /practice-sessions`, `/complete`): waktu mulai, durasi aktif/jeda, status, versi model, waktu per status deteksi, hitungan alasan kualitas, jumlah frame diproses/dilewati. **Tidak** ada frame, foto, video, koordinat, atau landmark. Dijaga oleh: skema Pydantic `extra=forbid` (tes menolak `landmarks`, `frame`, `video_url`, `photo`, `pose`), tidak adanya kolom semacam itu di DB, `lib/practice-api.ts` sebagai satu-satunya klien (tes statis), dan Playwright yang memeriksa body request.

## Pemeriksaan
| Risiko | Kontrol | Bukti |
|---|---|---|
| Kamera menyala tanpa aksi pengguna | Hanya `start()` dari klik; tombol eksplisit + pemberitahuan | Playwright: `getUserMedia` 0 panggilan sebelum klik; vitest komponen |
| Audio | `audio:false` hard-coded; tidak pernah `true` | vitest privasi (`camera.ts`); Playwright: constraint `audio:false`, 0 track audio |
| Raw video/frame diunggah | Tidak ada kode `fetch/XHR/sendBeacon/WebSocket/FormData` di modul CV; tidak ada `toDataURL/toBlob/MediaRecorder/captureStream` | vitest pemindaian statis; Playwright: 0 request ber-body/mutasi saat kamera+deteksi aktif |
| Landmark/frame masuk storage | Tidak ada pemakaian `localStorage/sessionStorage/indexedDB/caches/cookie` di modul CV | vitest statis; Playwright: storage kosong, tidak ada IndexedDB baru, cookie bersih |
| Landmark/frame masuk log/analytics | Tidak ada `console.*` di modul CV; tidak ada analytics/telemetri pihak ketiga | vitest statis; Playwright: console tanpa pola data (koordinat/visibility/ImageBitmap/data:image). Warning internal pustaka MediaPipe (nama berkas C++) tercatat terpisah, tidak berisi data pengguna |
| Worker/aset dari pihak ketiga | Worker, wasm, model: same-origin | Playwright: 0 request lintas-origin; URL aset berupa path relatif (vitest) |
| Frame tertinggal di memori | `ImageBitmap.close()` di worker (`finally`), di pompa (bitmap batal), dan di adapter (setelah dispose) | vitest (pipeline, worker-adapter). **Tidak diukur**: kebocoran memori jangka panjang (butuh sesi panjang di perangkat nyata) |
| Kamera/worker tertinggal setelah keluar | stop, unmount, `pagehide` → worker `terminate()` + track `stop()` | Playwright: event `close` worker + `track.readyState==="ended"` |
| Telemetri backend | Backend hanya menerima ringkasan sesi pada fitur masa depan (belum ada endpoint); tidak ada pencatatan landmark | audit kontrak API |

## Auth / sesi / proxy (ringkas, rujukan)
Sesi server-side + CSRF + Argon2 + kuncian akun + rate limit PostgreSQL + token email sekali pakai + anti-enumerasi ([ADR-0002](adr/0002-authentication.md), [ADR-0003](adr/0003-auth-hardening.md)). Cookie `Secure` otomatis di luar development. Proxy tepercaya: default aman, produksi belum terbukti ([REVERSE_PROXY_READINESS](REVERSE_PROXY_READINESS.md)). Akun demo: hanya `APP_ENV=development`; produksi **gagal start** bila `DEMO_USER_PASSWORD` diset, `SEED_DEMO_DATA=true`, `EXPOSE_DEMO_DATA=true`, cookie tidak Secure, sandi DB lemah, atau `MAIL_PROVIDER=dev_sink` (diuji).

## Belum terverifikasi
Perilaku pada Safari; kebocoran memori jangka panjang; apakah ekstensi browser pengguna dapat mengakses stream (di luar kendali aplikasi); kebijakan retensi/consent untuk fitur penyimpanan hasil sesi (belum ada fitur).
