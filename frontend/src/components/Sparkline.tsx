/** Garis sederhana untuk tren latensi (nilai terakhir). Dekoratif; angka sebenarnya ada di teks. */
export function Sparkline({ values, label }: { values: number[]; label: string }) {
  if (values.length < 2) return null;
  const w = 160, h = 32, max = Math.max(...values, 1);
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - (v / max) * (h - 2) - 1}`).join(" ");
  return (
    <svg role="img" aria-label={label} viewBox={`0 0 ${w} ${h}`} className="h-8 w-40 text-forest-700">
      <polyline fill="none" stroke="currentColor" strokeWidth="1.5" points={pts} />
    </svg>
  );
}
