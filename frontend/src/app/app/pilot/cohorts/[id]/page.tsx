import Link from "next/link";
import { notFound } from "next/navigation";
import { CheckCircle2, Circle } from "lucide-react";
import { CohortConsent } from "@/components/pilot/CohortConsent";
import { Card, ErrorState, PageHeader } from "@/components/ui";
import { formatDate, formatDateTime } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { MyCohort } from "@/lib/types";

export default async function MyCohortPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireUser(`/app/pilot/cohorts/${id}`);
  const r = await sGet<MyCohort>(`/pilot/me/cohorts/${id}`);
  if (!r.ok && r.status === 404) notFound();
  if (!r.ok) return <ErrorState message={r.error} retryHref={`/app/pilot/cohorts/${id}`} />;
  const c = r.data;
  return (
    <>
      <p className="mb-4 text-sm"><Link className="underline" href="/app/pilot">← Program Pilot</Link></p>
      <PageHeader eyebrow={`${c.is_demo ? "[DEMO] " : ""}${c.program_status_label} · ${c.partner_name}`} title={c.program_name} description={c.program_objective ?? undefined}>
        <p className="mt-2 text-slate-600">Cohort {c.name} · instruktur {c.instructor ?? "—"} · {formatDate(c.start_date)} – {formatDate(c.end_date)}</p>
      </PageHeader>
      <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-8">
          {c.surveys.filter((s) => !s.answered).length > 0 && (
            <Card className="border-bronze-700/30 bg-bronze-500/10"><h2 className="font-semibold">Survei menunggu Anda</h2>
              <ul className="mt-1">{c.surveys.filter((s) => !s.answered).map((s) => <li key={s.id}><Link className="underline" href={`/app/pilot/surveys/${s.id}`}>{s.title}</Link></li>)}</ul></Card>)}
          <section aria-labelledby="belajar"><h2 id="belajar" className="mb-3 font-serif text-2xl text-forest-900">Materi dan progres</h2>
            {c.progress && <p className="mb-3 text-sm text-slate-600">{c.progress.completed}/{c.progress.total} pelajaran selesai ({c.progress.percent}%) · Practice Studio: {c.practice.completed_sessions} sesi selesai, {c.practice.active_minutes} menit aktif. Angka ini hanya aktivitas, bukan penilaian teknik.</p>}
            <ul className="divide-y divide-line-200 rounded-2xl border border-line-200 bg-paper-50">{c.lessons.map((l) => (
              <li key={l.id}><Link href={`/app/courses/${c.course_slug}/lessons/${l.slug}`} className="flex items-center gap-3 px-4 py-3 hover:bg-parchment-100">
                {l.completed ? <CheckCircle2 aria-label="Selesai" className="h-5 w-5 text-forest-700" /> : <Circle aria-label="Belum selesai" className="h-5 w-5 text-slate-600" />}
                <span className="min-w-0 flex-1"><span className="block font-medium">{l.title}</span><span className="block text-xs text-slate-600">{l.module}</span></span></Link></li>))}</ul></section>
          <section aria-labelledby="jadwal"><h2 id="jadwal" className="mb-3 font-serif text-2xl text-forest-900">Jadwal</h2>
            {c.sessions.length === 0 ? <p className="text-slate-600">Belum ada jadwal pertemuan.</p> : (
              <ul className="space-y-2">{c.sessions.map((s) => <li key={s.id} className="rounded-xl border border-line-200 bg-paper-50 px-4 py-3"><p className="font-medium">{s.title}</p><p className="text-sm text-slate-600">{formatDateTime(s.starts_at)}{s.location_note ? ` · ${s.location_note}` : ""}</p></li>)}</ul>)}</section>
          <section aria-labelledby="umum"><h2 id="umum" className="mb-3 font-serif text-2xl text-forest-900">Pengumuman</h2>
            {c.announcements.length === 0 ? <p className="text-slate-600">Belum ada pengumuman.</p> : (
              <ul className="space-y-3">{c.announcements.map((a) => <li key={a.id}><Card><h3 className="font-semibold">{a.title}</h3><p className="mt-1 whitespace-pre-line">{a.body}</p><p className="mt-2 text-xs text-slate-600">{a.author ?? "—"} · {formatDateTime(a.created_at)}</p></Card></li>)}</ul>)}</section>
        </div>
        <aside><CohortConsent programId={c.program_id} cohortId={c.id} initial={c.consents} policy={c.policy_version} /></aside>
      </div>
    </>
  );
}
