import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Pagination, SearchForm } from "@/components/ui";
import { qs } from "@/lib/api";
import { formatDate, LEVEL_LABEL, SAFETY_LABEL, STATUS_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, StudioMovementRow } from "@/lib/types";
import { StatusBadge } from "@/components/ui";

type SP = { q?: string; status?: string; safety_category?: string; level?: string; page?: string };

export default async function StudioMovementsPage({ searchParams }: { searchParams: Promise<SP> }) {
  await requireUser("/app/studio/movements", ["instructor", "curator", "admin"]);
  const sp = await searchParams;
  const r = await sGet<Page<StudioMovementRow>>(`/studio/movements${qs({ ...sp, page_size: 15 })}`);
  return (
    <>
      <PageHeader eyebrow="Studio Instruktur" title="Dokumentasi gerakan">
        <Link href="/app/studio/movements/new" className="mt-4 inline-block rounded-xl bg-forest-700 px-5 py-2.5 font-medium text-paper-50 hover:bg-forest-900">+ Dokumentasikan gerakan</Link>
      </PageHeader>
      <SearchForm action="/app/studio/movements" values={sp} placeholder="Nama gerakan"
        filters={[
          { name: "status", label: "Status versi", options: Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label })) },
          { name: "safety_category", label: "Kategori keselamatan", options: Object.entries(SAFETY_LABEL).map(([value, label]) => ({ value, label })) },
          { name: "level", label: "Tingkat", options: Object.entries(LEVEL_LABEL).map(([value, label]) => ({ value, label })) },
        ]} />
      {!r.ok ? <ErrorState message={r.error} retryHref="/app/studio/movements" />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada dokumentasi gerakan">Mulai dengan satu gerakan. Pastikan mitra dan tradisinya sudah ada di Partner Workspace.</EmptyState>
        : <>
          <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
            <table className="w-full text-left text-sm"><caption className="sr-only">Daftar dokumentasi gerakan</caption>
              <thead className="border-b border-line-200 text-slate-600"><tr>
                <th scope="col" className="px-4 py-3">Gerakan</th><th scope="col" className="px-4 py-3">Tradisi · Mitra</th><th scope="col" className="px-4 py-3">Kategori</th>
                <th scope="col" className="px-4 py-3">Versi kerja</th><th scope="col" className="px-4 py-3">Tayang</th><th scope="col" className="px-4 py-3">Diubah</th></tr></thead>
              <tbody className="divide-y divide-line-200">{r.data.items.map((m) => (
                <tr key={m.id}>
                  <td className="px-4 py-3"><Link className="font-medium underline" href={`/app/studio/movements/${m.id}`}>{m.name_id}</Link>{m.is_demo && <span className="ml-2 text-xs text-slate-600">[DEMO]</span>}</td>
                  <td className="px-4 py-3 text-slate-600">{m.tradition_name} · {m.partner_name}</td>
                  <td className="px-4 py-3">{m.safety_category ? SAFETY_LABEL[m.safety_category] : "—"}{m.level ? ` · ${LEVEL_LABEL[m.level]}` : ""}</td>
                  <td className="px-4 py-3">{m.working_status ? <><StatusBadge status={m.working_status} /> <span className="text-slate-600">v{m.working_version}</span></> : "—"}</td>
                  <td className="px-4 py-3">{m.published_version_no ? `v${m.published_version_no}` : "—"}</td>
                  <td className="px-4 py-3">{formatDate(m.updated_at)}</td></tr>))}</tbody></table></div>
          <Pagination page={r.data} basePath="/app/studio/movements" params={sp} /></>}
    </>
  );
}
