/**
 * Siklus hidup kamera — terpisah dari React supaya mudah diuji.
 * Kamera hanya dimulai oleh aksi pengguna; stop() menghentikan SEMUA track (idempoten).
 */
export type CameraState =
  | { status: "idle" }
  | { status: "requesting" }
  | { status: "active"; deviceId: string | null; label: string | null }
  | { status: "denied" }
  | { status: "unavailable"; reason: "NO_DEVICE" | "NO_API" | "INSECURE_CONTEXT" }
  | { status: "error"; message: string }
  | { status: "stopped" };

export type CameraAction =
  | { type: "request" }
  | { type: "granted"; deviceId: string | null; label: string | null }
  | { type: "denied" }
  | { type: "unavailable"; reason: "NO_DEVICE" | "NO_API" | "INSECURE_CONTEXT" }
  | { type: "error"; message: string }
  | { type: "stop" };

export const INITIAL_CAMERA_STATE: CameraState = { status: "idle" };

export function cameraReducer(state: CameraState, action: CameraAction): CameraState {
  switch (action.type) {
    case "request": return state.status === "requesting" ? state : { status: "requesting" };
    case "granted": return { status: "active", deviceId: action.deviceId, label: action.label };
    case "denied": return { status: "denied" };
    case "unavailable": return { status: "unavailable", reason: action.reason };
    case "error": return { status: "error", message: action.message };
    case "stop": return state.status === "idle" ? state : { status: "stopped" };
  }
}

export function classifyCameraError(err: unknown): CameraAction {
  const name = (err as { name?: string } | null)?.name ?? "";
  if (name === "NotAllowedError" || name === "SecurityError" || name === "PermissionDeniedError") return { type: "denied" };
  if (name === "NotFoundError" || name === "DevicesNotFoundError" || name === "OverconstrainedError") return { type: "unavailable", reason: "NO_DEVICE" };
  if (name === "NotReadableError" || name === "TrackStartError") {
    return { type: "error", message: "Kamera sedang dipakai aplikasi lain atau tidak dapat dibuka. Tutup aplikasi tersebut lalu coba lagi." };
  }
  return { type: "error", message: "Kamera tidak dapat dimulai. Coba muat ulang halaman." };
}

export interface MediaDevicesLike {
  getUserMedia(c: MediaStreamConstraints): Promise<MediaStream>;
  enumerateDevices(): Promise<MediaDeviceInfo[]>;
}

export class CameraController {
  private stream: MediaStream | null = null;

  constructor(
    private readonly devices: MediaDevicesLike | undefined = typeof navigator !== "undefined" ? navigator.mediaDevices : undefined,
    private readonly secure: boolean = typeof window !== "undefined" ? window.isSecureContext : true,
  ) {}

  get active(): boolean { return this.stream !== null; }

  /** Mulai kamera. Stream sebelumnya dihentikan lebih dulu (mencegah stream ganda). */
  async start(deviceId?: string): Promise<{ stream: MediaStream; deviceId: string | null; label: string | null } | CameraAction> {
    this.stop();
    if (!this.secure) return { type: "unavailable", reason: "INSECURE_CONTEXT" };
    if (!this.devices?.getUserMedia) return { type: "unavailable", reason: "NO_API" };
    try {
      const stream = await this.devices.getUserMedia({
        video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false, // tidak pernah meminta mikrofon
      });
      this.stream = stream;
      const track = stream.getVideoTracks()[0];
      return { stream, deviceId: track?.getSettings?.().deviceId ?? deviceId ?? null, label: track?.label ?? null };
    } catch (err) {
      return classifyCameraError(err);
    }
  }

  stop(): void {
    if (!this.stream) return;
    for (const t of this.stream.getTracks()) t.stop();
    this.stream = null;
  }

  async listVideoDevices(): Promise<MediaDeviceInfo[]> {
    if (!this.devices?.enumerateDevices) return [];
    try {
      return (await this.devices.enumerateDevices()).filter((d) => d.kind === "videoinput");
    } catch {
      return [];
    }
  }
}

export function isStarted(r: Awaited<ReturnType<CameraController["start"]>>): r is { stream: MediaStream; deviceId: string | null; label: string | null } {
  return "stream" in r;
}

export const CAMERA_MESSAGES = {
  denied: "Izin kamera ditolak. Anda dapat mengizinkannya lewat pengaturan situs di browser, atau lanjut belajar tanpa kamera.",
  NO_DEVICE: "Kamera tidak ditemukan pada perangkat ini. Anda tetap dapat belajar tanpa kamera.",
  NO_API: "Browser ini tidak mendukung akses kamera.",
  INSECURE_CONTEXT: "Kamera hanya dapat dipakai pada koneksi aman (HTTPS) atau localhost.",
} as const;
