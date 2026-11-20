import Link from "next/link";
import { Card, EmptyState, ErrorState, PageHeader, ProgressBar } from "@/components/ui";
import { ActivityChart } from "@/components/ActivityChart";
import { SessionRow } from "@/components/PracticeBits";
import { formatDuration } from "@/lib/format";
import { sGet, requireUser } from "@/lib/server-api";
import type { MyProgress, PracticeSummary } from "@/lib/types";

export const metadata = { title: "Ringkasan" };

export default async function Dashboard({ searchParams }: { searchParams: Promise<{ akses?: string }> }) {
  const [user, sp, r, ps] = await Promise.all([requireUser("/app"), searchParams, sGet<MyProgress>("/me/progress"), sGet<PracticeSummary>("/me/practice-summary?tz_offset=420")]);
  return (
    <>
      <PageHeader eyebrow="Ringkasan" title={`Halo, ${user.display_name}`} description="Lanjutkan pelajaran Anda atau jelajahi kurikulum baru." />
      {sp.akses === "ditolak" && <div role="alert" className="mb-6 rounded-xl border border-clay-600/30 bg-clay-600/5 p-4 text-clay-600">Peran Anda tidak memiliki akses ke halaman tersebut.</div>}
      {!r.ok ? <ErrorState message={r.error} retryHref="/app" />
        : r.data.enrollments.length === 0
          ? <EmptyState title="Anda belum mengikuti kurikulum apa pun"><Link className="underline" href="/academy">Telusuri akademi</Link> untuk memulai.</EmptyState>
          : <>
            <Card className="mb-6"><ProgressBar progress={r.data.totals} label="Total progres semua kurikulum" />
              <p className="mt-2 text-sm text-slate-600">{r.data.courses_completed} kurikulum selesai</p></Card>
            <h2 className="mb-3 font-serif text-2xl text-forest-900">Lanjutkan belajar</h2>
            <ul className="space-y-3">{r.data.enrollments.map(({ course, enrollment }) => (
              <li key={course.id}><Card>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div><h3 className="font-semibold"><Link className="hover:underline" href={`/academy/courses/${course.slug}`}>{course.title}</Link></h3>
                    <p className="text-sm text-slate-600">{enrollment.status === "completed" ? "Selesai" : "Sedang berjalan"}</p></div>
                  {enrollment.next_lesson_slug && <Link className="rounded-xl bg-forest-700 px-4 py-2 text-sm font-medium text-paper-50" href={`/app/courses/${course.slug}/lessons/${enrollment.next_lesson_slug}`}>
                    {enrollment.progress.completed ? "Lanjutkan" : "Mulai"}</Link>}
                </div>
                <div className="mt-3"><ProgressBar progress={enrollment.progress} /></div>
              </Card></li>))}</ul></>}
      {ps.ok && (
        <section aria-labelledby="latihan-terakhir" className="mt-10" data-testid="dash-practice">
          <div className="mb-3 flex items-end justify-between gap-3"><h2 id="latihan-terakhir" className="font-serif text-2xl text-forest-900">Latihan kamera</h2><Link className="text-sm underline" href="/app/practice">Semua riwayat</Link></div>
          {ps.data.total_sessions === 0
            ? <Card><p className="text-sm text-slate-600">Belum ada sesi latihan. Buka sebuah pelajaran lalu tekan <em>Mulai Latihan</em>.</p></Card>
            : <div className="grid gap-4 lg:grid-cols-[1fr_16rem]">
                <Card><p className="mb-2 text-sm text-slate-600">Waktu latihan aktif, 14 hari terakhir</p><ActivityChart days={ps.data.days} /></Card>
                <Card><dl className="space-y-2 text-sm"><div><dt className="text-slate-600">Total sesi</dt><dd className="font-serif text-3xl text-forest-900">{ps.data.total_sessions}</dd></div>
                  <div><dt className="text-slate-600">7 hari terakhir</dt><dd>{ps.data.sessions_last_7_days} sesi · {formatDuration(ps.data.active_seconds_last_7_days * 1000)}</dd></div></dl></Card>
              </div>}
          {ps.data.last_session && <ul className="mt-3"><SessionRow s={ps.data.last_session} /></ul>}
        </section>)}
    </>
  );
}
