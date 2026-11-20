import Link from "next/link";
import { ActivityChart } from "@/components/ActivityChart";
import { SessionRow } from "@/components/PracticeBits";
import { Card, EmptyState, ErrorState, PageHeader, Pagination } from "@/components/ui";
import { qs } from "@/lib/api";
import { formatDuration } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, PracticeSession, PracticeSummary } from "@/lib/types";

export const metadata = { title: "Riwayat latihan", robots: { index: false } };
type SP = { page?: string; lesson?: string };

export default async function PracticeHistory({ searchParams }: { searchParams: Promise<SP> }) {
  await requireUser("/app/practice");
  const sp = await searchParams;
  const [sum, list] = await Promise.all([
    sGet<PracticeSummary>("/me/practice-summary?tz_offset=420"),
    sGet<Page<PracticeSession>>(`/me/practice-sessions${qs({ page: sp.page, lesson: sp.lesson, page_size: 8 })}`),
  ]);
  return (
    <>
      <PageHeader eyebrow="Latihan" title="Riwayat latihan"
        description="Waktu dan kualitas input kamera selama sesi Anda. Ini bukan penilaian gerakan atau kemampuan." />
      {!sum.ok ? <ErrorState message={sum.error} retryHref="/app/practice" /> : (
        <div className="mb-8 grid gap-4 lg:grid-cols-[1fr_20rem]">
          <Card>
            <h2 className="mb-2 font-serif text-xl text-forest-900">Aktivitas 14 hari terakhir</h2>
            <ActivityChart days={sum.data.days} />
          </Card>
          <Card>
            <dl className="space-y-3 text-sm">
              <div><dt className="text-slate-600">Total sesi</dt><dd data-testid="sum-total" className="font-serif text-3xl text-forest-900">{sum.data.total_sessions}</dd></div>
              <div><dt className="text-slate-600">Total waktu latihan aktif</dt><dd className="text-lg">{formatDuration(sum.data.total_active_seconds * 1000)}</dd></div>
              <div><dt className="text-slate-600">7 hari terakhir</dt><dd>{sum.data.sessions_last_7_days} sesi · {formatDuration(sum.data.active_seconds_last_7_days * 1000)}</dd></div>
            </dl>
          </Card>
        </div>)}
      {sp.lesson && <p className="mb-3 text-sm">Menampilkan sesi untuk satu pelajaran. <Link className="underline" href="/app/practice">Tampilkan semua</Link></p>}
      {!list.ok ? <ErrorState message={list.error} retryHref="/app/practice" />
        : list.data.items.length === 0 ? <EmptyState title="Belum ada sesi latihan">Buka sebuah pelajaran lalu tekan <em>Mulai Latihan</em>. Mulai dari <Link className="underline" href="/academy">akademi</Link>.</EmptyState>
        : <><ul className="space-y-3" data-testid="session-list">{list.data.items.map((s) => <SessionRow key={s.id} s={s} />)}</ul>
            <Pagination page={list.data} basePath="/app/practice" params={sp} /></>}
    </>
  );
}
