import Link from "next/link";
import { notFound } from "next/navigation";
import { ErrorState } from "@/components/ui";
import { PartnerWorkspace } from "@/components/studio/PartnerWorkspace";
import { requireUser, sGet } from "@/lib/server-api";
import type { HistoryEntry, Page, PartnerEvent, StudioPartnerDetail, TraditionSummary } from "@/lib/types";

export default async function PartnerWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await requireUser(`/app/studio/partners/${id}`, ["instructor", "curator", "admin"]);
  const [d, h, t] = await Promise.all([
    sGet<StudioPartnerDetail>(`/studio/partners/${id}`),
    sGet<PartnerEvent[]>(`/studio/partners/${id}/history`),
    sGet<Page<TraditionSummary>>("/traditions?page_size=100"),
  ]);
  if (!d.ok && d.status === 404) notFound();
  if (!d.ok) return <ErrorState message={d.error} retryHref={`/app/studio/partners/${id}`} />;
  return (
    <>
      <p className="mb-4 text-sm"><Link href="/app/studio/partners" className="underline">← Semua mitra</Link></p>
      <PartnerWorkspace initial={d.data} initialHistory={h.ok ? h.data : []} traditions={t.ok ? t.data.items.map((x) => ({ id: x.id, name: x.name })) : []} viewerRole={user.role} viewerId={user.id} />
    </>
  );
}
export type _Unused = HistoryEntry;
