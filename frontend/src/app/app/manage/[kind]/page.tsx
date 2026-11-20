import Link from "next/link";
import { notFound } from "next/navigation";
import { EmptyState, ErrorState, PageHeader, Pagination, SearchForm, StatusBadge } from "@/components/ui";
import { qs } from "@/lib/api";
import { formatDate, KIND_LABEL, STATUS_LABEL } from "@/lib/format";
import { MANAGE_FIELDS } from "@/lib/manage-config";
import { requireUser, sGet } from "@/lib/server-api";
import type { ManageItem, Page } from "@/lib/types";

type SP = { q?: string; status?: string; page?: string };

export default async function ManageList({ params, searchParams }: { params: Promise<{ kind: string }>; searchParams: Promise<SP> }) {
  const { kind } = await params;
  if (!MANAGE_FIELDS[kind]) notFound();
  await requireUser(`/app/manage/${kind}`, ["instructor", "curator", "admin"]);
  const sp = await searchParams;
  const r = await sGet<Page<ManageItem>>(`/manage/${kind}${qs({ ...sp, page_size: 15 })}`);
  return (
    <>
      <PageHeader eyebrow="Kelola konten" title={KIND_LABEL[kind]}>
        <Link href={`/app/manage/${kind}/new`} className="mt-4 inline-block rounded-xl bg-forest-700 px-5 py-2.5 font-medium text-paper-50 hover:bg-forest-900">+ Buat baru</Link>
      </PageHeader>
      <SearchForm action={`/app/manage/${kind}`} values={sp} placeholder="Judul atau slug"
        filters={[{ name: "status", label: "Status", options: Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label })) }]} />
      {!r.ok ? <ErrorState message={r.error} retryHref={`/app/manage/${kind}`} />
        : r.data.items.length === 0 ? <EmptyState title="Belum ada konten">Mulai dengan tombol “Buat baru”.</EmptyState>
        : <>
          <div className="overflow-x-auto rounded-2xl border border-line-200 bg-paper-50">
            <table className="w-full text-left text-sm"><caption className="sr-only">Daftar {KIND_LABEL[kind]}</caption>
              <thead className="border-b border-line-200 text-slate-600"><tr><th scope="col" className="px-4 py-3">Judul</th><th scope="col" className="px-4 py-3">Status</th><th scope="col" className="px-4 py-3">Diubah</th></tr></thead>
              <tbody className="divide-y divide-line-200">{r.data.items.map((i) => (
                <tr key={i.id}><td className="px-4 py-3"><Link className="font-medium underline" href={`/app/manage/${kind}/${i.id}`}>{i.title}</Link>{i.is_demo && <span className="ml-2 text-xs text-slate-600">[DEMO]</span>}</td>
                  <td className="px-4 py-3"><StatusBadge status={i.status} /></td><td className="px-4 py-3">{formatDate(i.updated_at)}</td></tr>))}</tbody></table></div>
          <Pagination page={r.data} basePath={`/app/manage/${kind}`} params={sp} /></>}
    </>
  );
}
