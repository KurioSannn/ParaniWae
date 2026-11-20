import { Card, EmptyState, ErrorState, Grid, PageHeader, Pagination, SearchForm } from "@/components/ui";
import { TraditionCard } from "@/components/Cards";
import { qs } from "@/lib/api";
import { sGet } from "@/lib/server-api";
import type { Page, TraditionSummary } from "@/lib/types";

export const metadata = { title: "Jelajahi Warisan" };
type SP = { q?: string; region?: string; sort?: string; page?: string };

export default async function HeritagePage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const r = await sGet<Page<TraditionSummary>>(`/traditions${qs({ q: sp.q, region: sp.region, sort: sp.sort, page: sp.page, page_size: 9 })}`);
  return (
    <>
      <PageHeader eyebrow="Warisan" title="Jelajahi Warisan"
        description="Tradisi pencak silat yang sudah diterbitkan beserta sumber dan status verifikasinya. Katalog sengaja dimulai kecil dan tumbuh bersama mitra." />
      <SearchForm action="/heritage" values={sp} placeholder="Nama atau ringkasan tradisi"
        filters={[{ name: "sort", label: "Urutkan", options: [{ value: "name", label: "Nama A–Z" }, { value: "-name", label: "Nama Z–A" }, { value: "newest", label: "Terbaru" }] }]} />
      {!r.ok ? <ErrorState message={r.error} retryHref="/heritage" />
        : r.data.items.length === 0 ? <EmptyState title="Tidak ada tradisi yang cocok">Ubah kata kunci, atau katalog ini memang belum memiliki tradisi terbit.</EmptyState>
        : <><Grid>{r.data.items.map((t) => <TraditionCard key={t.id} t={t} level={2} />)}</Grid>
            <Pagination page={r.data} basePath="/heritage" params={sp} /></>}
      <Card className="mt-10 text-sm text-slate-600">Setiap tradisi memiliki sumber dan status verifikasi sendiri; tidak ada satu standar tunggal yang berlaku untuk semua aliran.</Card>
    </>
  );
}
