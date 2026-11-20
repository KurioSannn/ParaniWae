import Link from "next/link";
import { Card, EmptyState, ErrorState, PageHeader, ProgressBar } from "@/components/ui";
import { formatDate } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import { SessionRow } from "@/components/PracticeBits";
import type { MyProgress, Page, PracticeSession } from "@/lib/types";

export const metadata = { title: "Progres belajar" };

export default async function ProgressPage() {
  await requireUser("/app/progress");
  const [r, ps] = await Promise.all([sGet<MyProgress>("/me/progress"), sGet<Page<PracticeSession>>("/me/practice-sessions?page_size=3")]);
  return (
    <>
      <PageHeader eyebrow="Progres" title="Progres belajar"
        description="Persentase dihitung dari pelajaran yang saat ini terbit di tiap kurikulum. Angka ini bukan penilaian kemahiran." />
      {!r.ok ? <ErrorState message={r.error} retryHref="/app/progress" />
        : r.data.enrollments.length === 0 ? <EmptyState title="Belum ada progres">Ikuti sebuah kurikulum di <Link className="underline" href="/academy">akademi</Link>.</EmptyState>
        : <>
          <Card className="mb-6"><ProgressBar progress={r.data.totals} label="Keseluruhan" /></Card>
          <ul className="space-y-3">{r.data.enrollments.map(({ course, enrollment: e }) => (
            <li key={course.id}><Card>
              <h2 className="font-semibold"><Link className="hover:underline" href={`/academy/courses/${course.slug}`}>{course.title}</Link></h2>
              <p className="mb-3 text-sm text-slate-600">Mulai {formatDate(e.enrolled_at)}{e.completed_at && ` · selesai ${formatDate(e.completed_at)}`}</p>
              <ProgressBar progress={e.progress} />
              {e.next_lesson_slug && <Link className="mt-3 inline-block underline" href={`/app/courses/${course.slug}/lessons/${e.next_lesson_slug}`}>Pelajaran berikutnya →</Link>}
            </Card></li>))}</ul></>}
      {ps.ok && ps.data.items.length > 0 && (
        <section aria-labelledby="riwayat-latihan" className="mt-10" data-testid="progress-practice">
          <div className="mb-3 flex items-end justify-between gap-3"><h2 id="riwayat-latihan" className="font-serif text-2xl text-forest-900">Latihan kamera terakhir</h2><Link className="text-sm underline" href="/app/practice">Semua riwayat</Link></div>
          <p className="mb-3 text-sm text-slate-600">Sesi latihan tidak mengubah persentase progres pelajaran di atas.</p>
          <ul className="space-y-3">{ps.data.items.map((s) => <SessionRow key={s.id} s={s} />)}</ul>
        </section>)}
    </>
  );
}
