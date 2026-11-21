import Link from "next/link";
import { ClipboardList } from "lucide-react";
import { Card, EmptyState, ErrorState, PageHeader } from "@/components/ui";
import { formatDate } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { Portal } from "@/lib/types";

export const metadata = { title: "Program Pilot" };

export default async function PilotPortalPage() {
  const user = await requireUser("/app/pilot");
  const r = await sGet<Portal>("/pilot/me/portal");
  if (!r.ok) return <ErrorState message={r.error} retryHref="/app/pilot" />;
  const { memberships, pending_surveys } = r.data;
  return (
    <>
      <PageHeader eyebrow="Program Pilot" title="Program dan cohort Anda"
        description="Di sini Anda melihat program uji coba yang Anda ikuti, jadwal, kemajuan belajar, pengumuman, dan survei yang perlu diisi." />
      {pending_surveys.length > 0 && (
        <section aria-labelledby="sv" className="mb-8 rounded-2xl border border-bronze-700/30 bg-bronze-500/10 p-5">
          <h2 id="sv" className="flex items-center gap-2 font-semibold"><ClipboardList aria-hidden className="h-4 w-4" />Survei menunggu Anda</h2>
          <ul className="mt-2 space-y-1">{pending_surveys.map((s) => <li key={s.id}><Link className="underline" href={`/app/pilot/surveys/${s.id}`}>{s.title}</Link></li>)}</ul>
        </section>)}
      {memberships.length === 0 ? (
        <EmptyState title="Anda belum tergabung di program pilot">
          Program pilot diikuti lewat undangan dari instruktur/perguruan. Buka tautan undangan yang Anda terima; undangan hanya dapat dipakai sekali.
        </EmptyState>
      ) : (
        <ul className="grid gap-4 md:grid-cols-2">{memberships.map((m) => (
          <li key={m.cohort_id}><Card className="h-full">
            <p className="text-xs uppercase tracking-widest text-bronze-700">{m.is_demo ? "[DEMO] " : ""}{m.program_status_label}</p>
            <h2 className="mt-1 font-serif text-xl text-forest-900"><Link className="underline-offset-2 hover:underline" href={`/app/pilot/cohorts/${m.cohort_id}`}>{m.program_name}</Link></h2>
            <p className="text-sm text-slate-600">Cohort {m.cohort_name} · bergabung {formatDate(m.joined_at)}</p>
            {m.progress && (<div className="mt-3"><div role="progressbar" aria-label="Progres belajar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={m.progress.percent} className="h-2 overflow-hidden rounded-full bg-line-200"><div className="h-full bg-forest-700" style={{ width: `${m.progress.percent}%` }} /></div>
              <p className="mt-1 text-sm text-slate-600">{m.progress.completed}/{m.progress.total} pelajaran · {m.progress.percent}%</p></div>)}
          </Card></li>))}</ul>)}
      {user.role !== "learner" && <p className="mt-8 text-sm"><Link className="underline" href="/app/pilot/manage">Kelola program pilot →</Link></p>}
    </>
  );
}
