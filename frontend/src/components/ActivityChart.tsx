import type { PracticeDayPoint } from "@/lib/types";
import { formatDuration } from "@/lib/format";

/** Tren durasi latihan harian (bukan skor kemampuan). SVG + tabel tersembunyi untuk pembaca layar. */
export function ActivityChart({ days }: { days: PracticeDayPoint[] }) {
  const max = Math.max(60, ...days.map((d) => d.active_seconds));
  const w = 560, h = 120, gap = 6, bw = (w - gap * (days.length - 1)) / days.length;
  const total = days.reduce((s, d) => s + d.active_seconds, 0);
  const active = days.filter((d) => d.sessions > 0).length;
  const label = `Durasi latihan aktif per hari selama ${days.length} hari terakhir: total ${formatDuration(total * 1000)}, aktif pada ${active} hari.`;
  return (
    <figure>
      <svg role="img" aria-label={label} viewBox={`0 0 ${w} ${h + 18}`} className="w-full max-w-xl">
        <line x1="0" y1={h} x2={w} y2={h} stroke="#E4E1D8" />
        {days.map((d, i) => {
          const bh = d.active_seconds ? Math.max(3, (d.active_seconds / max) * (h - 8)) : 0;
          const x = i * (bw + gap);
          return (
            <g key={d.date}>
              <rect x={x} y={h - bh} width={bw} height={bh} rx="3" fill="#315C4D"><title>{`${d.date}: ${formatDuration(d.active_seconds * 1000)}, ${d.sessions} sesi`}</title></rect>
              {d.sessions === 0 && <rect x={x} y={h - 2} width={bw} height="2" fill="#E4E1D8" />}
              {(i === 0 || i === days.length - 1 || i === Math.floor(days.length / 2)) && <text x={x + bw / 2} y={h + 14} textAnchor="middle" fontSize="10" fill="#52605A">{d.date.slice(5)}</text>}
            </g>
          );
        })}
      </svg>
      <figcaption className="sr-only">{label}</figcaption>
      <table className="sr-only"><caption>Latihan per hari</caption><thead><tr><th scope="col">Tanggal</th><th scope="col">Sesi</th><th scope="col">Durasi aktif</th></tr></thead>
        <tbody>{days.map((d) => <tr key={d.date}><td>{d.date}</td><td>{d.sessions}</td><td>{formatDuration(d.active_seconds * 1000)}</td></tr>)}</tbody></table>
    </figure>
  );
}
