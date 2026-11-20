import Link from "next/link";
import { Card, ErrorState, PageHeader } from "@/components/ui";
import { KIND_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { ManageItem, Page } from "@/lib/types";

export const metadata = { title: "Kelola konten" };

export default async function ManageHome() {
  const user = await requireUser("/app/manage", ["instructor", "curator", "admin"]);
  const kinds = await sGet<{ key: string; label: string }[]>("/manage/kinds");
  if (!kinds.ok) return <ErrorState message={kinds.error} retryHref="/app/manage" />;
  const counts = await Promise.all(kinds.data.map(async (k) => {
    const r = await sGet<Page<ManageItem>>(`/manage/${k.key}?status=pending_review&page_size=1`);
    return [k.key, r.ok ? r.data.total : 0] as const;
  }));
  const pending = Object.fromEntries(counts);
  return (
    <>
      <PageHeader eyebrow="Kelola konten" title="Pengelolaan konten budaya"
        description={user.role === "instructor" ? "Anda dapat membuat dan mengajukan draf milik Anda. Persetujuan dan penerbitan dilakukan kurator." : "Buat, tinjau, setujui, dan terbitkan. Hanya konten berstatus Terbit yang tampil di katalog publik."} />
      <ul className="grid gap-4 sm:grid-cols-2">
        {kinds.data.map((k) => (
          <li key={k.key}><Link href={`/app/manage/${k.key}`} className="block rounded-2xl border border-line-200 bg-paper-50 p-5 hover:border-sage-500">
            <h2 className="font-serif text-xl text-forest-900">{KIND_LABEL[k.key] ?? k.label}</h2>
            <p className="text-sm text-slate-600">{pending[k.key] ? `${pending[k.key]} menunggu review` : "Tidak ada yang menunggu review"}</p></Link></li>))}
      </ul>
      <Card className="mt-8 text-sm text-slate-600">Alur: <strong>Draf → Menunggu review → Terverifikasi → Terbit</strong>. Konten non-demo wajib memiliki sumber dan rujukan bukti persetujuan mitra sebelum disetujui.</Card>
    </>
  );
}
