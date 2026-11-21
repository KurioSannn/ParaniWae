import Link from "next/link";
import { Card, EmptyState, ErrorState, PageHeader } from "@/components/ui";
import { requireUser, sGet } from "@/lib/server-api";

export const metadata = { title: "Riwayat latihan kamera", robots: { index: false } };

type Attempt = { id: string; created_at: string; movement_id: string; status: string; total_score: number | null; input_quality: number | null;
  protocol_version: string; feedback: string[] | null; criteria: { label: string; score: number | null }[] | null };
type Resp = { items: Attempt[]; by_movement: { movement_id: string; attempts: number; best_score: number | null; average_score: number | null }[] };

const name = (id: string) => id.replace(/^mv\.[a-z]+\./, "").replaceAll("-", " ");

export default async function HistoryPage() {
  await requireUser("/app/latihan/riwayat");
  const r = await sGet<Resp>("/assessments?limit=100");
  if (!r.ok) return <ErrorState message={r.error} retryHref="/app/latihan/riwayat" />;
  const { items, by_movement } = r.data;
  return (
    <>
      <PageHeader eyebrow="Latihan" title="Riwayat latihan kamera" description="Ringkasan skor kesesuaian dari latihan yang Anda simpan. Video dan posisi tubuh tidak pernah disimpan." />
      {!items.length ? <EmptyState title="Belum ada hasil tersimpan"><Link className="underline" href="/library">Pilih gerakan di Pustaka Gerakan</Link> lalu tekan “Coba Latihan Sekarang”.</EmptyState> : (
        <div className="space-y-8">
          <section aria-labelledby="per-gerakan">
            <h2 id="per-gerakan" className="mb-3 font-serif text-2xl text-forest-900">Per gerakan</h2>
            <ul className="grid gap-3 md:grid-cols-2">
              {by_movement.map((b) => {
                const trend = items.filter((a) => a.movement_id === b.movement_id && a.total_score !== null).reverse().map((a) => a.total_score!);
                const w = 160, h = 36;
                const pts = trend.map((s, i) => `${trend.length < 2 ? w / 2 : (i / (trend.length - 1)) * w},${h - (s / 100) * h}`).join(" ");
                return (
                  <li key={b.movement_id}><Card>
                    <p className="font-medium capitalize">{name(b.movement_id)}</p>
                    <p className="text-sm text-slate-600">{b.attempts} kali · terbaik {b.best_score ?? "—"} · rata-rata {b.average_score ?? "—"}</p>
                    {trend.length > 0 && <svg role="img" aria-label={`Tren skor: ${trend.join(", ")}`} width={w} height={h} className="mt-2"><polyline points={pts} fill="none" stroke="#315c4d" strokeWidth="2" /></svg>}
                    <Link className="mt-2 inline-block text-sm underline" href={`/library/${b.movement_id.replace(/^mv\.[a-z]+\./, "")}/latihan`}>Latih lagi</Link>
                  </Card></li>
                );
              })}
            </ul>
          </section>
          <section aria-labelledby="semua">
            <h2 id="semua" className="mb-3 font-serif text-2xl text-forest-900">Semua hasil</h2>
            <ul className="space-y-2">
              {items.map((a) => (
                <li key={a.id}><Card>
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="font-medium capitalize">{name(a.movement_id)}</p>
                    <p className="text-sm text-slate-600">{new Date(a.created_at).toLocaleString("id-ID", { dateStyle: "medium", timeStyle: "short" })}</p>
                  </div>
                  <p className="text-sm">{a.status === "scored" ? <>Skor <strong>{a.total_score}</strong></> : "Belum dapat dinilai"} · kualitas masukan {a.input_quality !== null ? Math.round(a.input_quality * 100) : "—"}% · protokol {a.protocol_version}</p>
                  {a.feedback?.length ? <ul className="mt-1 list-disc pl-5 text-sm text-slate-600">{a.feedback.map((f) => <li key={f}>{f}</li>)}</ul> : null}
                </Card></li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </>
  );
}
