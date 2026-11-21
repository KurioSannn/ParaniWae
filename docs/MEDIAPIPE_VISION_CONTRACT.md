# Kontrak Visi (MediaPipe)

**Model terpasang:** `pose_landmarker_lite` + `hand_landmarker` (@mediapipe/tasks-vision 1.2.3), di-host sendiri, inferensi di Web Worker. Pose = 33 titik tubuh + **world landmarks** (kini diteruskan oleh worker); tangan = 21 titik per tangan dengan klasifikasi kiri/kanan.

**Overlay** (`skeleton.ts`): garis tubuh kiri (hijau)/kanan (kuning), sendi putih, jari berwarna per jari dengan semua sendi, ketebalan mengikuti ukuran video, kejelasan mengikuti visibility, perataan EMA khusus tampilan (`LandmarkSmoother`; pengukuran memakai data mentah), cermin ditangani lewat proyeksi.

**Dipertahankan:** backpressure frame, pelepasan resource, siklus hidup kamera opt-in & dapat dihentikan, tanpa unggahan video, pemulihan worker.

**Belum dievaluasi (jujur):** varian Full/Heavy dan Holistic **tidak dibandingkan** karena tidak ada benchmark pada perangkat nyata; kami tidak mengklaim FPS atau akurasi. Rencana: jalankan `BenchmarkRunner` di perangkat target sebelum mengganti model. Hasil kamera nyata harus diuji manual (`docs/QA_MANUAL_CAMERA_CHECKLIST.md`).
