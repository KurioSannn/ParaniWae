import Link from "next/link";
import { notFound } from "next/navigation";
import { CohortManager } from "@/components/pilot/CohortManager";
import { ErrorState } from "@/components/ui";
import { requireUser, sGet } from "@/lib/server-api";
import type { CohortDashboard, CohortManage } from "@/lib/types";

export default async function CohortManagePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireUser(`/app/pilot/manage/cohorts/${id}`, ["instructor", "curator", "admin"]);
  const [c, d, n] = await Promise.all([sGet<CohortManage>(`/pilot/cohorts/${id}`), sGet<CohortDashboard>(`/pilot/cohorts/${id}/dashboard`),
    sGet<{ id: string; participant_user_id: string; participant: string; note: string; created_at: string }[]>(`/pilot/cohorts/${id}/notes`)]);
  if (!c.ok && c.status === 404) notFound();
  if (!c.ok) return <ErrorState message={c.error} retryHref={`/app/pilot/manage/cohorts/${id}`} />;
  if (!d.ok) return <ErrorState message={d.error} />;
  return (
    <>
      <p className="mb-4 text-sm"><Link className="underline" href={`/app/pilot/manage/${c.data.program_id}`}>← {c.data.program.name}</Link></p>
      <CohortManager initial={c.data} dashboard={d.data} notes={n.ok ? n.data : []} />
    </>
  );
}
