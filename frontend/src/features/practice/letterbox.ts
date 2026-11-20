import type { Landmark } from "@/features/practice/landmarks";

/** Opsi `square-pad`: frame diberi bingkai hitam menjadi persegi sebelum inferensi; koordinat dipetakan balik. */
export function squarePad(w: number, h: number): { size: number; padX: number; padY: number } {
  const size = Math.max(w, h);
  return { size, padX: (size - w) / 2, padY: (size - h) / 2 };
}

/** Landmark ternormalisasi terhadap kanvas persegi -> ternormalisasi terhadap frame asli (w×h). */
export function unpadLandmark<T extends Landmark>(l: T, w: number, h: number): T {
  const { size, padX, padY } = squarePad(w, h);
  return { ...l, x: (l.x * size - padX) / w, y: (l.y * size - padY) / h };
}
