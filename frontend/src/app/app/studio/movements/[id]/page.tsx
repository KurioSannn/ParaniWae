import Link from "next/link";
import { notFound } from "next/navigation";
import { ErrorState } from "@/components/ui";
import { MovementWorkspace } from "@/components/studio/MovementWorkspace";
import { requireUser, sGet } from "@/lib/server-api";
import type { HistoryEntry, StudioMovement } from "@/lib/types";

export default async function MovementWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireUser(`/app/studio/movements/${id}`, ["instructor", "curator", "admin"]);
  const [m, h] = await Promise.all([sGet<StudioMovement>(`/studio/movements/${id}`), sGet<HistoryEntry[]>(`/studio/movements/${id}/history`)]);
  if (!m.ok && m.status === 404) notFound();
  if (!m.ok) return <ErrorState message={m.error} retryHref={`/app/studio/movements/${id}`} />;
  return (
    <>
      <p className="mb-4 text-sm"><Link href="/app/studio/movements" className="underline">← Semua dokumentasi gerakan</Link></p>
      <MovementWorkspace key={m.data.active_document?.id} initial={m.data} initialHistory={h.ok ? h.data : []} />
    </>
  );
}
