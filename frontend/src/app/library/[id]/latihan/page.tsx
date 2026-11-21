import Link from "next/link";
import { notFound } from "next/navigation";
import { AssessmentPractice } from "@/components/assessment/AssessmentPractice";
import { Movement3DPlayer } from "@/components/knowledge/Movement3DPlayer";
import { MovementVisual } from "@/components/knowledge/Bits";
import { Card, ErrorState, PageHeader } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { clipFor, type CharacterManifest } from "@/lib/character";
import type { MovementDetail } from "@/lib/research";
import { getCurrentUser } from "@/lib/server-api";
import type { Protocol } from "@/features/assessment/types";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return { title: `Latihan kamera · ${id.replaceAll("-", " ")}`, robots: { index: false }, alternates: { canonical: `/library/${id}/latihan` } };
}

const STEPS = ["Pelajari gerakan", "Lihat peraga 3D", "Coba latihan", "Analisis gerakan", "Skor & saran"];

export default async function PracticePage({ params, searchParams }: { params: Promise<{ id: string }>; searchParams: Promise<{ pelajaran?: string }> }) {
  const { id } = await params;
  const { pelajaran } = await searchParams;
  const m = await apiGet<MovementDetail>(`/research/movements/${encodeURIComponent(id)}`);
  if (!m.ok) return m.status === 404 ? notFound() : <ErrorState message={m.error} retryHref={`/library/${id}/latihan`} />;
  const [p, ch, user] = await Promise.all([
    apiGet<Protocol>(`/research/assessment/protocols/${encodeURIComponent(m.data.id)}`),
    apiGet<CharacterManifest>("/research/character"),
    getCurrentUser(),
  ]);
  if (!p.ok || p.data.status !== "active") {
    return (
      <>
        <PageHeader eyebrow="Latihan kamera" title={m.data.names.primary} />
        <Card className="max-w-2xl"><p>Latihan dengan penilaian kamera belum tersedia untuk gerakan ini. Pelajari uraian dan peraganya terlebih dahulu.</p>
          <Link className="mt-3 inline-block underline" href={`/library/${id}`}>Kembali ke gerakan</Link></Card>
      </>
    );
  }
  const clip = clipFor(ch.ok ? ch.data : null, m.data.id);
  const proto = p.data;
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/library">Pustaka Gerakan</Link> / <Link className="underline" href={`/library/${id}`}>{m.data.names.primary}</Link> / Latihan</nav>
      <PageHeader eyebrow="Latihan kamera" title={`Coba ${m.data.names.primary}`} description={proto.summary} />
      <ol className="mb-6 flex flex-wrap gap-2 text-sm" aria-label="Langkah latihan">
        {STEPS.map((s, i) => <li key={s} className="rounded-full border border-line-200 bg-paper-50 px-3 py-1"><span className="font-medium">{i + 1}.</span> {s}</li>)}
      </ol>
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-6">
          <AssessmentPractice protocol={proto} movementTitle={m.data.names.primary} loggedIn={!!user} lessonRef={pelajaran} />
        </div>
        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          {clip ? <Movement3DPlayer clip={clip} title={m.data.names.primary} fallback={<MovementVisual a={m.data.animation} title={m.data.names.primary} />} />
            : <MovementVisual a={m.data.animation} title={m.data.names.primary} />}
          <Card>
            <h2 className="mb-2 font-semibold">Yang dinilai</h2>
            <ul className="space-y-1 text-sm">{proto.criteria.map((c) => <li key={c.id}>• {c.label} <span className="text-slate-600">(bobot {c.weight})</span></li>)}
              <li>• Kelengkapan fase <span className="text-slate-600">(bobot {proto.phase_completion_weight})</span></li></ul>
            <p className="mt-3 text-xs text-slate-600">{proto.disclaimer}</p>
          </Card>
          <Card>
            <h2 className="mb-1 font-semibold">Keselamatan</h2>
            <p className="text-sm text-slate-600">Lakukan hanya gerak solo ini di area lapang dan lantai yang tidak licin. Hentikan bila nyeri. Latihan teknik lanjutan, sparring, dan senjata hanya bersama pelatih.</p>
          </Card>
        </aside>
      </div>
    </>
  );
}
