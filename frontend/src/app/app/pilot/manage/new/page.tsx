import { ErrorState, PageHeader } from "@/components/ui";
import { NewProgramForm } from "@/components/pilot/NewProgramForm";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, PartnerRow } from "@/lib/types";

export default async function NewProgramPage() {
  await requireUser("/app/pilot/manage/new", ["instructor", "curator", "admin"]);
  const r = await sGet<Page<PartnerRow>>("/studio/partners?page_size=100");
  if (!r.ok) return <ErrorState message={r.error} />;
  return (
    <>
      <PageHeader eyebrow="Pilot & Impact Studio" title="Program pilot baru" description="Disimpan sebagai draf. Pengajuan persetujuan memerlukan mitra terverifikasi (atau mitra demo), tujuan, periode, penanggung jawab, dan minimal satu cohort." />
      <NewProgramForm partners={r.data.items.map((p) => ({ id: p.id, name: p.name, verified: p.verification_status === "verified" || p.is_demo }))} />
    </>
  );
}
