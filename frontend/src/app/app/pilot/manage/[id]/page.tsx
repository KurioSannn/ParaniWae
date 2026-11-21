import Link from "next/link";
import { notFound } from "next/navigation";
import { ProgramWorkspace } from "@/components/pilot/ProgramWorkspace";
import { ErrorState } from "@/components/ui";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, ProgramAnalytics, ProgramDetail, SurveyOut, CourseSummary } from "@/lib/types";

export default async function ProgramPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await requireUser(`/app/pilot/manage/${id}`, ["instructor", "curator", "admin"]);
  const [p, sv, an, courses] = await Promise.all([
    sGet<ProgramDetail>(`/pilot/programs/${id}`), sGet<SurveyOut[]>(`/pilot/programs/${id}/surveys`),
    sGet<ProgramAnalytics>(`/pilot/programs/${id}/analytics`), sGet<Page<CourseSummary>>("/courses?page_size=100"),
  ]);
  if (!p.ok && p.status === 404) notFound();
  if (!p.ok) return <ErrorState message={p.error} retryHref={`/app/pilot/manage/${id}`} />;
  return (
    <>
      <p className="mb-4 text-sm"><Link className="underline" href="/app/pilot/manage">← Semua program</Link></p>
      <ProgramWorkspace initial={p.data} surveys={sv.ok ? sv.data : []} analytics={an.ok ? an.data : null} analyticsError={an.ok ? null : an.error}
        courses={courses.ok ? courses.data.items.map((c) => ({ id: c.id, title: c.title, partner: c.partner_name ?? null })) : []} viewerRole={user.role} />
    </>
  );
}
