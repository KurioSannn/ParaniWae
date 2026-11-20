import { EmptyState, ErrorState, Grid, PageHeader, Pagination, SearchForm } from "@/components/ui";
import { PartnerCard } from "@/components/Cards";
import { qs } from "@/lib/api";
import { PARTNER_TYPE_LABEL } from "@/lib/format";
import { sGet } from "@/lib/server-api";
import type { Page, PartnerSummary } from "@/lib/types";

export const metadata = { title: "Perguruan" };
type SP = { q?: string; partner_type?: string; sort?: string; page?: string };

export default async function CommunityPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const r = await sGet<Page<PartnerSummary>>(`/partners${qs({ ...sp, page_size: 9 })}`);
  return (
    <>
      <PageHeader eyebrow="Komunitas" title="Perguruan dan komunitas"
        description="Hanya perguruan yang diterbitkan dengan sumber yang jelas. Entri non-demo wajib terverifikasi dan menyetujui listing publik." />
      <SearchForm action="/community" values={sp} placeholder="Nama, kota, atau deskripsi"
        filters={[{ name: "partner_type", label: "Jenis", options: Object.entries(PARTNER_TYPE_LABEL).map(([value, label]) => ({ value, label })) }]} />
      {!r.ok ? <ErrorState message={r.error} retryHref="/community" />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada perguruan yang cocok" />
        : <><Grid>{r.data.items.map((p) => <PartnerCard key={p.id} p={p} level={2} />)}</Grid>
            <Pagination page={r.data} basePath="/community" params={sp} /></>}
    </>
  );
}
