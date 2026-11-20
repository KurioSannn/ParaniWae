import Link from "next/link";
import { EmptyState, ErrorState, PageHeader, Pagination, SearchForm } from "@/components/ui";
import { PartnerStatusPill } from "@/components/studio/StatusPills";
import { qs } from "@/lib/api";
import { formatDate, PARTNER_STATUS_LABEL, PARTNER_TYPE_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, PartnerRow } from "@/lib/types";

type SP = { q?: string; status?: string; page?: string };

export default async function PartnersListPage({ searchParams }: { searchParams: Promise<SP> }) {
  await requireUser("/app/studio/partners", ["instructor", "curator", "admin"]);
  const sp = await searchParams;
  const r = await sGet<Page<PartnerRow>>(`/studio/partners${qs({ ...sp, page_size: 15 })}`);
  return (
    <>
      <PageHeader eyebrow="Studio Instruktur" title="Mitra">
        <Link href="/app/studio/partners/new" className="mt-4 inline-block rounded-xl bg-forest-700 px-5 py-2.5 font-medium text-paper-50 hover:bg-forest-900">+ Profil mitra baru</Link>
      </PageHeader>
      <SearchForm action="/app/studio/partners" values={sp} placeholder="Nama atau kota"
        filters={[{ name: "status", label: "Status kemitraan", options: Object.entries(PARTNER_STATUS_LABEL).map(([value, label]) => ({ value, label })) }]} />
      {!r.ok ? <ErrorState message={r.error} retryHref="/app/studio/partners" />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada mitra">Buat profil mitra sebagai draf. Profil bukan mitra resmi sampai admin memverifikasi dengan bukti.</EmptyState>
        : <>
          <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
            <table className="w-full text-left text-sm"><caption className="sr-only">Daftar mitra</caption>
              <thead className="border-b border-line-200 text-slate-600"><tr><th scope="col" className="px-4 py-3">Nama</th><th scope="col" className="px-4 py-3">Jenis</th><th scope="col" className="px-4 py-3">Peran saya</th><th scope="col" className="px-4 py-3">Status</th><th scope="col" className="px-4 py-3">Diubah</th></tr></thead>
              <tbody className="divide-y divide-line-200">{r.data.items.map((p) => (
                <tr key={p.id}><td className="px-4 py-3"><Link className="font-medium underline" href={`/app/studio/partners/${p.id}`}>{p.name}</Link></td>
                  <td className="px-4 py-3">{PARTNER_TYPE_LABEL[p.partner_type]}</td>
                  <td className="px-4 py-3">{p.my_role === "manager" ? "Penanggung jawab" : p.my_role === "instructor" ? "Anggota" : "—"}</td>
                  <td className="px-4 py-3"><PartnerStatusPill status={p.verification_status} demo={p.is_demo} /></td>
                  <td className="px-4 py-3">{formatDate(p.updated_at)}</td></tr>))}</tbody></table></div>
          <Pagination page={r.data} basePath="/app/studio/partners" params={sp} /></>}
    </>
  );
}
