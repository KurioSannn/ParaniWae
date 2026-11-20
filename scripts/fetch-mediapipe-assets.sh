#!/bin/sh
# Mengunduh model MediaPipe (di-host sendiri) ke frontend/public/mediapipe/models dan memverifikasi SHA-256.
# Lisensi model: Apache-2.0 (Google/MediaPipe). Browser pengguna TIDAK memanggil CDN pihak ketiga.
set -e
cd "$(dirname "$0")/../frontend/public/mediapipe/models" 2>/dev/null || { mkdir -p "$(dirname "$0")/../frontend/public/mediapipe/models"; cd "$(dirname "$0")/../frontend/public/mediapipe/models"; }
fetch() { # nama url sha256
  if [ -f "$1" ] && [ "$(shasum -a 256 "$1" | cut -d' ' -f1)" = "$3" ]; then echo "OK (sudah ada): $1"; return; fi
  echo "Mengunduh $1 ..."; curl -fsSL -o "$1" "$2"
  [ "$(shasum -a 256 "$1" | cut -d' ' -f1)" = "$3" ] || { echo "CHECKSUM TIDAK COCOK: $1" >&2; rm -f "$1"; exit 1; }
}
fetch pose_landmarker_lite.task "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task" 59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a
fetch hand_landmarker.task "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1
echo "Selesai."
