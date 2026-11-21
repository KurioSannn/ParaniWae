/** LandmarkFrame (worker) → MeasureFrame (mesin penilaian). Hanya di memori perangkat; tidak pernah dikirim/disimpan. */
import { assessFrameQuality } from "@/features/practice/quality-gate";
import type { LandmarkFrame } from "@/features/practice/landmarks";
import type { MeasureFrame, Vec3 } from "@/features/assessment/types";
import { estimateView } from "@/features/assessment/features";

export function toMeasureFrame(frame: LandmarkFrame, tSec: number): MeasureFrame {
  const pose = frame.poses[0];
  if (!pose) return { t: tSec, image: null, world: null, visibility: new Array(33).fill(0), usable: false };
  const aspect = frame.meta.width && frame.meta.height ? frame.meta.width / frame.meta.height : 1;
  const image = pose.landmarks.map((l): Vec3 => [l.x * aspect, l.y, l.z]);
  const world = pose.world ? pose.world.map((l): Vec3 => [l.x, l.y, l.z]) : null;
  return { t: tSec, image, world, visibility: pose.landmarks.map((l) => l.visibility ?? 0), usable: assessFrameQuality(frame).usable };
}

/** Pemeriksaan posisi sebelum merekam: tubuh utuh terlihat & sudut kamera sesuai protokol. */
export function positioningCheck(f: MeasureFrame, view: "front" | "side"): { ok: boolean; message: string } {
  if (!f.image || !f.usable) return { ok: false, message: "Pastikan seluruh tubuh, dari kepala sampai telapak kaki, terlihat di bingkai." };
  const v = estimateView(f.image);
  if (v !== "unknown" && v !== view) {
    return { ok: false, message: view === "side" ? "Putar badan sehingga sisi tubuh menghadap kamera." : "Hadapkan badan ke kamera." };
  }
  return { ok: true, message: "Posisi sudah tepat. Tahan sebentar…" };
}
