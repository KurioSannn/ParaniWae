import Link from "next/link";
import { BadgeCheck } from "lucide-react";
import { Card, EmptyState, ErrorState, PageHeader, Pagination, ProvenanceBadge, SearchForm } from "@/components/ui";
import { apiGet, qs } from "@/lib/api";
import { LEVEL_LABEL, SAFETY_LABEL } from "@/lib/format";
import type { MovementSummary, Page, PartnerSummary, TraditionSummary } from "@/lib/types";

export const metadata = { title: "Pustaka Gerakan — SILATARA", description: "Dokumentasi gerakan yang disusun dan ditinjau bersama instruktur dan mitra." };
type SP = { q?: string; tradition?: string; partner?: string; level?: string; safety_category?: string; partner_verified?: string; page?: string };

export default async function LibraryPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const [r, tr, pa] = await Promise.all([
    apiGet<Page<MovementSummary>>(`/movements${qs({ ...sp, page_size: 12 })}`),
    apiGet<Page<TraditionSummary>>("/traditions?page_size=100"),
    apiGet<Page<PartnerSummary>>("/partners?page_size=100"),
  ]);
  return (
    <>
      <PageHeader eyebrow="Pustaka" title="Pustaka Gerakan"
        description="Hanya dokumentasi yang sudah ditinjau dan diterbitkan yang tampil di sini, lengkap dengan sumber, instruktur penyusun, dan status verifikasinya. Kategori keselamatan adalah klasifikasi administratif, bukan sertifikasi." />
      <SearchForm action="/library" values={sp} placeholder="Nama gerakan"
        filters={[
          { name: "tradition", label: "Tradisi", options: tr.ok ? tr.data.items.map((t) => ({ value: t.slug, label: t.name })) : [] },
          { name: "partner", label: "Perguruan", options: pa.ok ? pa.data.items.map((p) => ({ value: p.slug, label: p.name })) : [] },
          { name: "level", label: "Tingkat", options: Object.entries(LEVEL_LABEL).map(([value, label]) => ({ value, label })) },
          { name: "safety_category", label: "Kategori keselamatan", options: Object.entries(SAFETY_LABEL).map(([value, label]) => ({ value, label })) },
          { name: "partner_verified", label: "Verifikasi mitra", options: [{ value: "true", label: "Mitra terverifikasi" }, { value: "false", label: "Belum/contoh" }] },
        ]} />
      {!r.ok ? <ErrorState message={r.error} retryHref="/library" />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada gerakan terbit">Gerakan muncul di sini setelah didokumentasikan instruktur, ditinjau, dan diterbitkan admin.</EmptyState>
        : <>
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{r.data.items.map((m) => (
            <li key={m.id}><Card className="h-full">
              <h2 className="font-serif text-xl text-forest-900"><Link className="underline-offset-2 hover:underline" href={`/library/${m.id}`}>{m.name_id}</Link></h2>
              {m.name_local && <p className="text-sm text-slate-600">{m.name_local}</p>}
              <p className="mt-2 text-sm text-slate-600">{m.tradition_name}{m.partner_name ? ` · ${m.partner_name}` : ""}</p>
              <p className="mt-1 text-sm">{m.level ? LEVEL_LABEL[m.level] : ""}{m.level && m.safety_category ? " · " : ""}{m.safety_category ? SAFETY_LABEL[m.safety_category] : ""}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2"><ProvenanceBadge p={m.provenance} />
                {m.partner_verified && <span className="inline-flex items-center gap-1 text-xs text-forest-900"><BadgeCheck aria-hidden className="h-3.5 w-3.5" />Mitra terverifikasi</span>}</div>
            </Card></li>))}</ul>
          <Pagination page={r.data} basePath="/library" params={sp} /></>}
    </>
  );
}
