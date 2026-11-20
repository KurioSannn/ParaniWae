# Kontrak bersama: SILATARA Practice Studio

Ditetapkan **sebelum** A/B/C bekerja paralel. Perubahan kontrak = PR yang sama dengan pembaruan tipe + dokumen ini, ditinjau pihak konsumen.

## 1. Prinsip produk (batas keras)
- Practice Studio hanya mengukur **kualitas input & keterdeteksian landmark**. **Tidak ada** skor teknik, persentase kemiripan, koreksi biomekanik, prediksi kemampuan, rep counter, atau klaim akurasi pencak silat — sampai gerakan referensi + rubrik disahkan instruktur mitra.
- Data yang disimpan: **metadata sesi minimal + ringkasan agregat kualitas input**. Tidak pernah: video, frame, foto, landmark, koordinat tubuh. Skema server menolak (422) bidang di luar daftar.
- Kamera hanya setelah persetujuan eksplisit; audio selalu mati; kamera + worker berhenti saat sesi selesai/pindah halaman/tab ditutup.
- Latihan hanya solo tingkat pemula yang disetujui; tampilkan label **[DEMO]/belum diverifikasi** bila materi belum disetujui mitra.

## 2. Keadaan UI (`StudioState`)
`intro → initializing → ready → (waiting_for_subject | detecting | partial_detection | insufficient_visibility) ⇄ paused → completed`, dan `error` dari mana pun.
- `waiting_for_subject`: tidak ada pose (NO_POSE). `detecting`: semua landmark wajib terlihat & di dalam frame. `partial_detection`: pose ada, sebagian landmark wajib terlihat (cakupan ≥ 0,5) tetapi belum penuh. `insufficient_visibility`: cakupan < 0,5, di luar frame, banyak orang, atau data landmark tidak lengkap.
- Status ditampilkan setelah **stabil** (≥5 hasil berurutan sama) agar tidak berkedip.

## 3. Kontrak engine (C → A)
`AsyncLandmarkerAdapter` (tidak berubah) + `InferenceConfig` (+ `inputShape: "native" | "square-pad"`). `LandmarkFrame` tidak berubah. Rendering kerangka: `drawSkeleton(ctx, frame, size, opts)` dan `projectLandmark(l, size, {mirror})` di `features/practice/skeleton.ts`; koordinat landmark **ternormalisasi terhadap frame input** (0..1) dan diproyeksikan ke piksel CSS kanvas yang berukuran sama dengan area video (rasio mengikuti video, tanpa crop).
`QualityAggregator`, `SessionClock`, `StateSmoother`, `deriveDetectionState` di `features/practice/studio-state.ts`.

## 4. Kontrak API (B → A)
Semua memerlukan sesi login; mutasi memerlukan `X-CSRF-Token`; hanya data milik sendiri (data orang lain → 404).

| Method | Path | Fungsi |
|---|---|---|
| POST | `/api/v1/practice-sessions` | Mulai sesi `{lesson_id, model_version, client_version}` → 201 `PracticeSession` (status `in_progress`). Syarat: login, lesson published & publik, **terdaftar di kurikulum** (403 `NOT_ENROLLED`), lesson boleh dilatih (403 `PRACTICE_NOT_AVAILABLE`) |
| POST | `/api/v1/practice-sessions/{id}/complete` | Akhiri sesi `{status: completed\|abandoned\|error, active_duration_ms, paused_duration_ms, quality_summary, error_code?}`; `ended_at` ditetapkan **server**; durasi dibatasi oleh waktu nyata (422 bila mustahil); 409 bila sudah berakhir |
| GET | `/api/v1/practice-sessions/{id}` | Detail sesi milik sendiri |
| GET | `/api/v1/me/practice-sessions?lesson=&status=&page=&page_size=` | Riwayat (paginated, terbaru dulu) |
| GET | `/api/v1/me/practice-summary?tz_offset=420` | Total sesi, total detik aktif, 7 hari, tren 14 hari per tanggal, sesi terakhir |
| GET | `/api/v1/courses/{slug}/lessons/{lesson}` | + `practice: {available, reason, is_demo, label}` |

`quality_summary` (semua angka; `extra=forbid`): `frames_total`, `processed_frames`, `dropped_frames`, `valid_frame_ratio` (0..1), `ms_in_state{waiting_for_subject,detecting,partial_detection,insufficient_visibility}`, `reasons{NO_POSE,MULTIPLE_PEOPLE,TOO_FEW_LANDMARKS,LOW_VISIBILITY,OUT_OF_FRAME,NO_HAND,LOW_HAND_CONFIDENCE}` (hitungan frame), `engine` (`worker`|`synthetic`), `delegate` (`GPU`|`CPU`|null), `simulated` (bool).

Aturan **boleh dilatih** (server): lesson published & publik dan (lesson `is_demo` — sesi kamera teknis berlabel DEMO tanpa gerakan referensi — ATAU memiliki gerakan terkait `practice_mode=solo_beginner` yang publik). Selain itu `PRACTICE_NOT_AVAILABLE`.

## 5. Tipe frontend
`frontend/src/lib/types.ts` (pemilik: B): `PracticeSession`, `PracticeSummary`, `QualitySummaryPayload`, `LessonPractice`. Klien: `frontend/src/lib/practice-api.ts` (A). Modul CV (`features/practice/**`) **tidak boleh** memanggil jaringan (dijaga tes statis); hanya `practice-api.ts` yang mengirim metadata sesi.

## 6. Pembagian berkas
- **A (UI):** `components/PracticeStudio.tsx`, `components/Practice*`, `app/app/**/practice/**`, perubahan lesson/dashboard/progress, `AppNav`, `lib/practice-api.ts`, spec Playwright `practice.spec.ts`.
- **B (domain):** `backend/app/{models/practice.py,schemas/practice.py,services/practice.py,api/v1/practice.py}`, migrasi, `backend/tests/test_practice*.py`, `lib/types.ts` (bagian practice), docs API.
- **C (CV):** `features/practice/{skeleton,studio-state,letterbox,synthetic-adapter}.ts`, perubahan worker (`inputShape`, penghitung warning), tes unit terkait, `docs/AI_CV_FOUNDATION.md` (bagian proyeksi/warning).
