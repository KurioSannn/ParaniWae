import Link from "next/link";
import { notFound } from "next/navigation";
import { SafetyNotice } from "@/components/PracticeStudio";
import { Card, ErrorState, PageHeader } from "@/components/ui";
import { formatDateTime, formatDuration, PRACTICE_STATUS_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { DetectionStateKey, PracticeSession } from "@/lib/types";

export const metadata = { title: "Ringkasan latihan", robots: { index: false } };
const STATE_NAME: Record<DetectionStateKey, string> = {
  detecting: "Tubuh terdeteksi", partial_detection: "Sebagian tubuh terdeteksi",
  insufficient_visibility: "Tubuh belum terlihat cukup", waiting_for_subject: "Menunggu tubuh terdeteksi",
};

export default async function SessionSummary({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireUser(`/app/practice/sessions/${id}`);
  const r = await sGet<PracticeSession>(`/practice-sessions/${encodeURIComponent(id)}`);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/app/practice/sessions/${id}`} />;
  const s = r.data, q = s.quality_summary;
  const totalMs = q ? Object.values(q.ms_in_state).reduce((a, b) => a + b, 0) : 0;
  const lessonUrl = `/app/courses/${s.lesson.course_slug}/lessons/${s.lesson.slug}`;
  return (
    <>
      <PageHeader eyebrow="Ringkasan latihan" title={s.lesson.title} description={`${s.lesson.course_title} · ${PRACTICE_STATUS_LABEL[s.status] ?? s.status}`}>
        {s.lesson.is_demo && <p className="mt-2 text-sm text-slate-600">{s.lesson.verification_label}</p>}
        {q?.simulated && <p className="mt-2 inline-block rounded-full border border-clay-600/40 bg-clay-600/10 px-3 py-1 text-xs text-ink-950">Sesi SIMULASI — landmark sintetis, bukan deteksi tubuh</p>}
      </PageHeader>
      <div className="grid gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-6">
          <Card>
            <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
              <div><dt className="text-slate-600">Durasi latihan aktif</dt><dd data-testid="dur-active" className="font-serif text-2xl text-forest-900">{formatDuration(s.active_duration_ms)}</dd></div>
              <div><dt className="text-slate-600">Waktu jeda</dt><dd className="text-lg">{formatDuration(s.paused_duration_ms)}</dd></div>
              <div><dt className="text-slate-600">Status sesi</dt><dd className="text-lg">{PRACTICE_STATUS_LABEL[s.status] ?? s.status}</dd></div>
              <div><dt className="text-slate-600">Mulai</dt><dd>{formatDateTime(s.started_at)}</dd></div>
              <div><dt className="text-slate-600">Selesai</dt><dd>{formatDateTime(s.ended_at)}</dd></div>
              <div><dt className="text-slate-600">Versi model</dt><dd className="break-words text-xs">{s.model_version}</dd></div>
            </dl>
          </Card>
          {q ? (
            <Card>
              <h2 className="mb-1 font-serif text-xl text-forest-900">Kualitas input (agregat)</h2>
              <p className="mb-3 text-sm text-slate-600">Seberapa jelas tubuh terlihat oleh kamera selama sesi. <strong>Ini bukan penilaian gerakan</strong> dan bukan ukuran kemampuan.</p>
              <ul className="space-y-2">
                {(Object.keys(STATE_NAME) as DetectionStateKey[]).map((k) => {
                  const ms = q.ms_in_state[k], pct = totalMs ? Math.round((ms / totalMs) * 100) : 0;
                  return (
                    <li key={k}>
                      <div className="flex justify-between text-sm"><span>{STATE_NAME[k]}</span><span>{formatDuration(ms)} · {pct}%</span></div>
                      <div role="img" aria-label={`${STATE_NAME[k]}: ${pct}% dari waktu`} className="h-2 overflow-hidden rounded-full bg-line-200"><div className="h-full rounded-full bg-sage-500" style={{ width: `${pct}%` }} /></div>
                    </li>);
                })}
              </ul>
              <p className="mt-3 text-sm text-slate-600">Frame diproses: {q.processed_frames} · dilewati karena mesin sibuk: {q.dropped_frames} · proporsi frame dengan tubuh terlihat penuh: {Math.round(q.valid_frame_ratio * 100)}%.</p>
            </Card>
          ) : <Card><p className="text-sm text-slate-600">Ringkasan kualitas tidak tersedia untuk sesi ini.</p></Card>}
          <SafetyNotice />
        </div>
        <div className="space-y-3">
          <Card>
            <h2 className="mb-2 font-semibold">Materi terkait</h2>
            <p className="text-sm">{s.lesson.title}</p>
            <Link href={lessonUrl} className="mt-3 inline-block rounded-xl bg-forest-700 px-4 py-2 font-medium text-paper-50 hover:bg-forest-900">Kembali ke materi</Link>
            <Link href={`${lessonUrl}/practice`} className="mt-2 block underline">Latihan lagi</Link>
            <Link href="/app/practice" className="mt-2 block underline">Semua riwayat latihan</Link>
          </Card>
        </div>
      </div>
    </>
  );
}
