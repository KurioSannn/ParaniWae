import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Pagination } from "@/components/ui";
import { qs } from "@/lib/api";
import { formatDate, PROGRAM_STATUS_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, ProgramRow } from "@/lib/types";

export default async function ManageProgramsPage({ searchParams }: { searchParams: Promise<{ page?: string; status?: string }> }) {
  await requireUser("/app/pilot/manage", ["instructor", "curator", "admin"]);
  const sp = await searchParams;
  const r = await sGet<Page<ProgramRow>>(`/pilot/programs${qs({ ...sp, page_size: 15 })}`);
  return (
    <>
      <PageHeader eyebrow="Pilot & Impact Studio" title="Program pilot"
        description="Program uji coba bersama perguruan, instruktur, dan kelompok pelajar. Program baru resmi hanya setelah disetujui admin dengan bukti; mitra belum terverifikasi hanya dapat menyimpan draf.">
        <Link href="/app/pilot/manage/new" className="mt-4 inline-block rounded-xl bg-forest-700 px-5 py-2.5 font-medium text-paper-50 hover:bg-forest-900">+ Program baru</Link>
      </PageHeader>
      {!r.ok ? <ErrorState message={r.error} retryHref="/app/pilot/manage" />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada program pilot">Buat program dari mitra Anda. Pastikan mitra sudah dibuat di Studio Instruktur.</EmptyState>
        : <>
          <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
            <table className="w-full text-left text-sm"><caption className="sr-only">Daftar program pilot</caption>
              <thead className="border-b border-line-200 text-slate-600"><tr><th scope="col" className="px-4 py-3">Program</th><th scope="col" className="px-4 py-3">Penyelenggara</th><th scope="col" className="px-4 py-3">Status</th><th scope="col" className="px-4 py-3">Periode</th><th scope="col" className="px-4 py-3">Peserta</th></tr></thead>
              <tbody className="divide-y divide-line-200">{r.data.items.map((p) => (
                <tr key={p.id}><td className="px-4 py-3"><Link className="font-medium underline" href={`/app/pilot/manage/${p.id}`}>{p.name}</Link>{p.is_demo && <span className="ml-2 text-xs text-slate-600">[DEMO]</span>}</td>
                  <td className="px-4 py-3 text-slate-600">{p.partner_name}{!p.partner_verified && !p.is_demo ? " (belum terverifikasi)" : ""}</td>
                  <td className="px-4 py-3">{PROGRAM_STATUS_LABEL[p.status]}</td><td className="px-4 py-3">{formatDate(p.start_date)} – {formatDate(p.end_date)}</td>
                  <td className="px-4 py-3">{p.member_count}/{p.capacity}</td></tr>))}</tbody></table></div>
          <Pagination page={r.data} basePath="/app/pilot/manage" params={sp} /></>}
    </>
  );
}
