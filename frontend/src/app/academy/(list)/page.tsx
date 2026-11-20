import { EmptyState, ErrorState, Grid, PageHeader, Pagination, SearchForm } from "@/components/ui";
import { CourseCard } from "@/components/Cards";
import { qs } from "@/lib/api";
import { LEVEL_LABEL } from "@/lib/format";
import { sGet } from "@/lib/server-api";
import type { CourseSummary, Page } from "@/lib/types";

export const metadata = { title: "Akademi" };
type SP = { q?: string; level?: string; sort?: string; page?: string };

export default async function AcademyPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const r = await sGet<Page<CourseSummary>>(`/courses${qs({ ...sp, page_size: 9 })}`);
  return (
    <>
      <PageHeader eyebrow="Akademi" title="Kurikulum belajar"
        description="Hanya kurikulum yang sudah diterbitkan yang tampil di sini. Setiap kurikulum terikat pada satu tradisi dan satu mitra." />
      <SearchForm action="/academy" values={sp} placeholder="Judul atau ringkasan kurikulum"
        filters={[
          { name: "level", label: "Tingkat", options: Object.entries(LEVEL_LABEL).map(([value, label]) => ({ value, label })) },
          { name: "sort", label: "Urutkan", options: [{ value: "title", label: "Judul A–Z" }, { value: "-title", label: "Judul Z–A" }, { value: "newest", label: "Terbaru" }, { value: "shortest", label: "Terpendek" }] },
        ]} />
      {!r.ok ? <ErrorState message={r.error} retryHref="/academy" />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada kurikulum yang cocok">Kurikulum baru akan muncul setelah melewati review dan diterbitkan.</EmptyState>
        : <><Grid>{r.data.items.map((c) => <CourseCard key={c.id} c={c} level={2} />)}</Grid>
            <Pagination page={r.data} basePath="/academy" params={sp} /></>}
    </>
  );
}
