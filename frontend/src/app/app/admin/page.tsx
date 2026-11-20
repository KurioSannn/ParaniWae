import { AdminUsers } from "@/components/AdminUsers";
import { Card, ErrorState, PageHeader, Pagination, SearchForm } from "@/components/ui";
import { qs } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { AdminUser, Page } from "@/lib/types";

export const metadata = { title: "Admin" };
type SP = { q?: string; role?: string; page?: string };
type Audit = { id: string; action: string; entity_type: string; entity_id: string | null; created_at: string };

export default async function AdminPage({ searchParams }: { searchParams: Promise<SP> }) {
  const me = await requireUser("/app/admin", ["admin"]);
  const sp = await searchParams;
  const [users, audit] = await Promise.all([
    sGet<Page<AdminUser>>(`/admin/users${qs({ ...sp, page_size: 10 })}`),
    sGet<Page<Audit>>("/admin/audit-logs?page_size=10"),
  ]);
  return (
    <>
      <PageHeader eyebrow="Admin" title="Pengguna dan audit" description="Perubahan peran/status dicatat di jejak audit dan langsung mencabut sesi pengguna terkait." />
      <SearchForm action="/app/admin" values={sp} placeholder="Nama atau email"
        filters={[{ name: "role", label: "Peran", options: ["learner", "instructor", "curator", "admin"].map((v) => ({ value: v, label: v })) }]} />
      {!users.ok ? <ErrorState message={users.error} /> : <><AdminUsers users={users.data.items} selfId={me.id} /><Pagination page={users.data} basePath="/app/admin" params={sp} /></>}
      <h2 className="mb-3 mt-10 font-serif text-2xl text-forest-900">Jejak audit terbaru</h2>
      {!audit.ok ? <ErrorState message={audit.error} /> : <Card><ul className="space-y-1 text-sm">{audit.data.items.map((a) => <li key={a.id}><span className="font-medium">{a.action}</span> · {a.entity_type} · {formatDate(a.created_at)}</li>)}</ul></Card>}
    </>
  );
}
