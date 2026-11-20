# Fondasi AI Computer Vision (status: fondasi saja)

**Yang ada:** akses kamera aman, ekstraksi landmark di browser (MediaPipe), tipe data, quality gate input, dan kontrak asesmen.
**Yang TIDAK ada (dan tidak boleh diklaim):** penilaian benar/salah gerakan, skor teknik, koreksi postur, ambang biomekanik, rubrik, referensi gerakan. Semuanya menunggu rubrik+referensi+toleransi+umpan balik yang disetujui instruktur mitra untuk satu aliran/mitra tertentu (CLAUDE.md #4–#7).

## Arsitektur inferensi: Web Worker (sprint 20 Nov 2026)
Inferensi MediaPipe **tidak lagi berjalan di main thread**. Alur:
```
<video> --rVFC--> FramePump --createImageBitmap--> [transfer, zero-copy] --> Worker (classic IIFE) --> MediaPipe Pose+Hand
   ^  (backpressure, rate limit, pause)                                              |
   +----------------- LandmarkFrame (objek polos) + procMs <----- postMessage -------+
```
- **Classic worker, bukan module worker:** MediaPipe memuat loader wasm dengan `importScripts` (tidak ada di module worker). `landmarker.worker.ts` di-bundle esbuild → IIFE (`npm run build:worker` → `public/mediapipe/worker/landmarker.worker.js`, di-gitignore; dibangun otomatis oleh entrypoint dev, Dockerfile, dan CI). **Diverifikasi empiris** di Chromium (bukan asumsi): worker memuat wasm + model, GPU→CPU fallback bekerja di dalam worker.
- **Protokol bertipe** (`worker/protocol.ts`): `init | frame | pause | resume | dispose` → `status | ready | result | dropped | error | metrics-bearing results`. Tipe data `LandmarkFrame` tidak berubah (kontrak UI/quality gate tetap).
- **Transfer frame:** `createImageBitmap(video)` di main thread (resolusi asli; `maxFrameWidth=null` — **tidak ada downscale diam-diam**) ditransfer ke worker; worker memanggil `bitmap.close()` di `finally`; bitmap yang tidak jadi dikirim ditutup di pompa/adapter (diuji).
- **Backpressure** (`pipeline.ts`): maks `maxInFlight` (default 1) frame di engine; frame video baru **dilewati** (dihitung `droppedBackpressure`) selama engine penuh; `minIntervalMs` (default 66 ≈ 15 fps) adalah konfigurasi, bukan "drop"; worker membuang frame basi (`maxFrameAgeMs` 500); watchdog menganggap frame yang tak kembali 5 s sebagai "hilang". Penjadwalan per-frame video (`requestVideoFrameCallback`, fallback rAF).
- **Siklus hidup:** model diinisialisasi **sekali per sesi deteksi** (adapter menolak `init` kedua); `dispose` idempoten (kirim `dispose`, lepas handler, `terminate()`); error fatal (init gagal, timeout 60 s, crash) → UI menampilkan galat dan **tidak ada fallback sinkron di main thread** (bahkan tidak ada jalur kode untuk itu di UI); jeda inferensi saat tab tersembunyi (`visibilitychange`), kamera tetap aktif; unmount/`pagehide`/stop menghentikan worker + kamera.
- **Implementasi lama dipertahankan HANYA sebagai baseline benchmark** (`mediapipe-adapter.ts`, sinkron di main thread; tidak dipakai UI).
- **Trade-off konfigurasi** (`config.ts`): `minIntervalMs` kecil → resolusi temporal lebih baik tetapi CPU/baterai/panas naik; `maxInFlight>1` hanya menambah antrean+latensi (satu model); `maxFrameWidth` kecil → inferensi lebih cepat dan memori lebih kecil tetapi akurasi landmark berpotensi turun (**belum diukur; default tidak diperkecil**); `hands` aktif menambah beban model kedua; `maxPeople` >1 menambah beban dan dibutuhkan untuk mendeteksi `MULTIPLE_PEOPLE`.

## Peta kode (`frontend/src/features/practice/`)
| Berkas | Isi |
|---|---|
| `landmarks.ts` | Tipe `Landmark`, `PoseDetection`, `HandDetection`, `FrameMetadata`, `LandmarkFrame`; indeks BlazePose; sambungan kerangka |
| `quality-gate.ts` | `assessFrameQuality`, `summarizeQuality`, `QualityWindow`, panduan Indonesia. Hanya **kelayakan input** |
| `camera.ts` | `CameraController` + `cameraReducer` |
| `config.ts` | `InferenceConfig` + default, `MEDIAPIPE_VERSION` (dijaga tes agar sinkron dengan `package.json`), path aset |
| `async-adapter.ts` | Antarmuka `AsyncLandmarkerAdapter` (kontrak engine; dapat diganti tanpa mengubah UI) |
| `worker/landmarker.worker.ts`, `worker/protocol.ts`, `worker/convert.ts` | Worker, protokol bertipe, konversi hasil MediaPipe → `LandmarkFrame` |
| `worker-adapter.ts` | `WorkerLandmarkerAdapter` (init+timeout, crash, dispose, transfer) |
| `pipeline.ts` | `FramePump` (backpressure, pause, watchdog), `createFrameBitmap`, `makeFrameScheduler` |
| `stats.ts`, `responsiveness.ts` | `Series` (mean/median/p95), `ResponsivenessMonitor` (rAF gap + **event-loop lag** + long task) |
| `benchmark.ts` | Runner A/B + `summarizeRuns` |
| `mediapipe-adapter.ts` | Implementasi LAMA sinkron (baseline benchmark saja) |
| `engine.ts`, `assessment-types.ts` | Kontrak asesmen; satu-satunya implementasi `unavailableEngine` → `not_assessable` |
| `fixtures.ts` | **Synthetic test fixture** |
| `components/CameraCheck.tsx` (`/app/practice/camera-check`), `components/BenchmarkRunner.tsx` (`/app/practice/benchmark`) | UI uji kamera + panel metrik; halaman benchmark |

## Practice Studio (fitur produk di atas fondasi ini)
Kontrak dan pembagian berkas: [PRACTICE_STUDIO_CONTRACT](PRACTICE_STUDIO_CONTRACT.md). Alur: lesson → "Mulai Latihan" → intro + persetujuan eksplisit → kamera + Worker siap (`ready`, pratinjau + skeleton, belum merekam) → "Mulai latihan" (sesi server dibuat) → `waiting_for_subject | detecting | partial_detection | insufficient_visibility` ⇄ `paused` → "Hentikan" → kamera + worker dilepas **lalu** metadata disimpan → ringkasan. Hanya kualitas input; tanpa skor/koreksi/rep counter.
- **Proyeksi koordinat** (`skeleton.ts`): landmark ternormalisasi terhadap frame input; kanvas overlay berukuran sama dengan area video yang mengikuti **rasio asli tanpa crop** (`fitVideoBox`), sehingga tidak bergeser pada 4:3 maupun 16:9. Mirror lewat parameter `mirror` (video dicerminkan lewat CSS; kanvas menggambar x terbalik — tidak ganda). Diuji unit (5 rasio, mirror, resize) **dan** di browser dengan membaca piksel kanvas pada koordinat yang diharapkan (4:3 dan 16:9, mirror hidup/mati, tiga ukuran viewport). Data yang dipakai SINTETIS (mode `?sim=1`, spanduk "MODE SIMULASI"), bukan bukti deteksi tubuh.
- **Skeleton:** koneksi tubuh resmi MediaPipe (33 titik; 26 tulang) + koneksi tangan resmi (21). Titik/koneksi wajah rinci (mata/mulut) **sengaja tidak digambar** (privasi, tidak berlebihan); hidung + telinga tetap sebagai penanda kepala. Titik berkonfiden rendah digambar redup/berongga.
- **Hysteresis status:** perubahan status ditampilkan setelah 5 hasil berurutan sama.

## Investigasi warning `NORM_RECT without IMAGE_DIMENSIONS` (20 Nov 2026)
**Temuan (eksperimen + sumber):** warning `landmark_projection_calculator.cc:81 Using NORM_RECT without IMAGE_DIMENSIONS is only supported for the square ROI` berasal dari graph internal wasm MediaPipe. Eksperimen terkontrol (`e2e-browser/tests/camera-roi.spec.ts`, konten frame sama, varian: 4:3 native, persegi-pad 640×640, persegi-crop 480×480, 16:9-pad 854×480, dan `square-pad` di worker) menunjukkan warning muncul **sekali per inisialisasi graph pada semua varian, termasuk input persegi** — jadi **tidak bergantung pada aspect ratio input** dan **tidak muncul per frame**. API Tasks JS tidak menyediakan opsi untuk memberi `IMAGE_DIMENSIONS`/`PROJECTION_MATRIX`. Satu-satunya isu upstream yang menyebut pesan ini ([mediapipe#6216](https://github.com/google-ai-edge/mediapipe/issues/6216)) tidak menjawab dampaknya pada akurasi.
**Keputusan:** warning **tidak dapat dihilangkan di sisi aplikasi** dan **tidak disembunyikan**. Worker menghitungnya (`console.warn` tetap diteruskan) dan angkanya tampil di diagnostik; tes regresi menjaga agar tidak per-frame. Opsi `inputShape: "square-pad"` (bingkai hitam menjadi persegi + pemetaan balik koordinat, diuji unit dan berjalan di worker) disediakan agar **Anggota C membandingkan A/B dengan subjek nyata**; default tetap `native` (belum ada bukti manfaat; menambah biaya satu draw per frame).
**Belum terbukti:** apakah warning memengaruhi akurasi landmark pada frame non-persegi. Tidak dapat dinilai tanpa subjek manusia berizin → tugas C3.

## Quality gate — apa yang diperiksa
Pose terdeteksi (`NO_POSE`), satu orang (`MULTIPLE_PEOPLE`), 33 landmark lengkap (`TOO_FEW_LANDMARKS`), 9 landmark tubuh wajib (hidung, bahu, pinggul, lutut, pergelangan kaki) terlihat (`LOW_VISIBILITY`) dan di dalam frame (`OUT_OF_FRAME`); tangan bila dipersyaratkan (`NO_HAND`, `LOW_HAND_CONFIDENCE`). Ringkasan sesi memakai nama bidang kontrak API: `valid_frame_ratio`, `required_landmark_coverage`, `dropped_frame_ratio`. **Ambang (`visibility ≥ 0.5`, margin 2%, ≥30 frame, ≥80% frame layak) adalah default teknis penangkapan, belum divalidasi lintas perangkat/tubuh/pencahayaan.**

## Privasi (diuji)
- Kamera hanya setelah klik "Saya mengerti, nyalakan kamera"; `audio:false`; tidak ada mikrofon.
- Tidak ada frame/video yang disimpan atau dikirim; tidak ada pemanggilan jaringan oleh pipeline CV selain memuat aset dari origin sendiri.
- Stop: tombol selalu terlihat; track dihentikan saat Hentikan, unmount, dan `pagehide`; start ulang menghentikan stream lama; satu loop deteksi saja.
- Tanpa pengenalan wajah; landmark wajah tidak dipakai (hanya hidung sebagai titik referensi kepala).

## Aset MediaPipe
`@mediapipe/tasks-vision@1.2.3` (dipin). Wasm disalin dari paket npm ke `public/mediapipe/wasm/` otomatis oleh entrypoint frontend. Model (`pose_landmarker_lite.task`, `hand_landmarker.task`, lisensi Apache-2.0) diunduh dengan `make mediapipe-assets` (verifikasi SHA-256); keduanya di-gitignore. Bila model belum ada, UI menampilkan pesan gagal-muat.

## Status verifikasi (dipisah per tingkat bukti; `make e2e-browser`, Chromium nyata, origin `http://localhost:3000` = secure context asli)
| Tingkat | Status | Bukti / catatan |
|---|---|---|
| **Camera lifecycle** (perangkat PALSU) | **PASS** | Kamera tidak diminta sebelum klik; `getUserMedia` sekali, `audio:false`; `<video>` diputar; 1 track video live, 0 audio; Hentikan/navigasi/`pagehide` → track `ended`; start ulang tanpa stream sisa |
| **Worker lifecycle** | **PASS** | Worker classic dari `/mediapipe/worker/landmarker.worker.js` (same-origin); **ditutup** saat deteksi dimatikan, saat pindah halaman, dan saat `pagehide` (event `close` worker diamati); kamera ikut berhenti |
| **Error handling** | **PASS** (sebagian simulasi) | `NotAllowedError` (simulasi; headless tak dapat menekan "Blokir"), `NotFoundError`, `NotReadableError` (simulasi), konteks tidak aman (nyata), tanpa izin di headless (`NotSupportedError` nyata) → pesan jelas. **Kegagalan init**: model diblok / script worker diblok → galat jelas, kamera tetap aktif, worker berhenti, **tanpa fallback main-thread**, dapat dicoba lagi |
| **Model loading** | **PASS** | wasm + 2 model dari origin sendiri (200/304), nol request lintas-origin, nol error konsol, nol response ≥400 |
| **Responsivitas UI (sintetis)** | **PASS (terukur, lihat benchmark)** | Selama inferensi worker: jeda rAF terbesar 33 ms dan 217 ms, p95 17 ms dan 33 ms, pada 2 run tes berbeda (n=294 dan 359 frame; hanya 2 sampel, bukan distribusi) |
| **Privasi runtime** | **PASS** | Tidak ada request mutasi/ber-body, tidak ada `localStorage`/`sessionStorage`/IndexedDB baru, cookie tanpa data, console tanpa pola data landmark/frame; pemindaian statis kode CV melarang `fetch/XHR/sendBeacon/WebSocket/storage/console/toDataURL/MediaRecorder/FormData` |
| **Landmark inference — input nyata** | **PIPELINE JALAN; AKURASI TIDAK TERVERIFIKASI** | Pose+Hand berjalan di worker pada aliran PALSU; hasil benar `NO_POSE`. **Tidak ada video manusia berizin**; deteksi pose/tangan manusia **tidak diuji** |
| **Webcam fisik** | **NOT VERIFIED** | Belum ada pengujian oleh anggota tim. Lihat [QA_MANUAL_CAMERA_CHECKLIST](QA_MANUAL_CAMERA_CHECKLIST.md) |
| **Safari** | **NOT VERIFIED** | Tidak ada Safari di lingkungan uji; `requestVideoFrameCallback`, `createImageBitmap`, transfer `ImageBitmap`, dan classic worker + WebGL di worker harus diverifikasi manual |

### Benchmark: implementasi lama (main thread) vs Web Worker
Sumber: [`docs/benchmarks/2026-11-20-headless-synthetic.json`](benchmarks/2026-11-20-headless-synthetic.json) (`make bench`). **Lingkungan:** Chromium 159.0.8154.6 headless (Playwright), container Linux di Docker Desktop, 8 thread, delegasi dilaporkan "GPU" (WebGL perangkat lunak). **Sumber: SINTETIS** (`fake_device_0`, 640×480) → hanya jalur komputasi, **bukan benchmark pose manusia**. **Parameter sama untuk kedua mesin:** model pose_landmarker_lite + hand_landmarker, interval 66 ms, 2 orang, tangan aktif, resolusi asli, 40 frame/run, **3 ulangan bergantian (A/B)**; angka = **median antar-run** (n=3). Heap JS main thread tercatat per run tetapi tidak dilaporkan di sini (tidak mencakup worker/WASM).

| Metrik (median 3 run) | Baseline main thread | Web Worker |
|---|---|---|
| Inisialisasi model (ms) | 1820 | 2338 (+ startup worker 121) |
| Latensi per frame, median (ms) | 632 | 669 |
| Latensi per frame, rata-rata (ms) | 1301 (ikut stall UI) | 766 |
| Latensi p95 (ms) | 1196 | 1220 |
| Frame diproses | 40 | 40 |
| Frame video dilewati (engine sibuk) | n/a (memblokir) | 985 |
| **Jeda event-loop terbesar (ms)** — blokir main thread | **1793** | **267** |
| Jeda event-loop p95 (ms) | 1415 | 3,6 |
| **Long task (jumlah / total)** | **41 / 52,3 s** | **1 / 64 ms** |
| Jeda rAF terbesar (ms) — kehalusan visual | 24 199 | 250 |
| Jeda rAF p95 (ms) | 1283 | 16,8 |

**Apa yang boleh disimpulkan (dan yang tidak):**
- Di lingkungan ini Worker **menghilangkan pembekuan main thread** (long task 41 → 1; jeda event-loop terbesar median 1793 → 267 ms; tab tidak lagi membeku puluhan detik).
- Worker **tidak mempercepat inferensi itu sendiri** (latensi median ≈ sama, 632 vs 669 ms) dan inisialisasi sedikit lebih lama (+≈0,5 s median; +121 ms startup worker). Throughput efektif ≈1,2–1,4 frame/s di lingkungan software-GL ini; ±25 frame video (30 fps) dilewati per frame yang diproses — itu **perilaku backpressure yang diharapkan**, bukan kegagalan.
- **Outlier tidak terjelaskan:** run Worker ke-3 mengalami stall 5,6 s pada rAF dan 5,7 s pada event-loop dengan 0 long task (median menyembunyikannya; lihat data per-run). Dugaan (belum dibuktikan): kelaparan CPU/GPU-perangkat-lunak di container. Perlu pengulangan lebih banyak (≥10) dan pengukuran di perangkat nyata.
- **Contoh nyata pemisahan sinyal** (panel metrik, satu sesi sintetis): jeda rAF terbesar **8383 ms** sementara jeda event-loop terbesar **53 ms** dan long task **0** → tampilan tersendat oleh compositor/GPU perangkat lunak, bukan oleh blokir main thread. Menilai "UI membeku" hanya dari rAF akan salah.
- Jeda **rAF** dan **event-loop** sengaja dipisah: rAF dapat membesar karena compositor/GPU kewalahan walau main thread bebas; event-loop lag hanya membesar bila main thread terblokir.
- **Dilarang** dikutip: "FPS produk", "akurasi", atau "kinerja di laptop pengguna". Satu lingkungan, satu sesi, sintetis. Benchmark perangkat nyata: tugas Anggota C (C1/C2).
- Warning pustaka MediaPipe yang teramati di kedua mesin (bukan data pengguna): `landmark_projection_calculator.cc: Using NORM_RECT without IMAGE_DIMENSIONS is only supported for the square ROI`. **Risiko akurasi yang belum dinilai**: dapat memengaruhi proyeksi landmark pada frame non-persegi (640×480). Harus diselidiki dengan subjek nyata (C3).

## Berikutnya (setelah mitra menyetujui)
Referensi gerakan + rubrik berversi (tabel `movement_rubrics` sudah ada), implementasi `AssessmentEngine` deterministik, endpoint `practice-sessions` (hanya ringkasan; tanpa video), evaluasi kesepakatan dengan instruktur lintas perangkat.
