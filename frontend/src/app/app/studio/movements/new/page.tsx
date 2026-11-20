import { ErrorState, PageHeader } from "@/components/ui";
import { NewMovementForm } from "@/components/studio/NewMovementForm";
import { requireUser, sGet } from "@/lib/server-api";
import type { Page, PartnerRow, StudioPartnerDetail } from "@/lib/types";

export default async function NewMovementPage({ searchParams }: { searchParams: Promise<{ partner?: string }> }) {
  await requireUser("/app/studio/movements/new", ["instructor", "curator", "admin"]);
  const sp = await searchParams;
  const pr = await sGet<Page<PartnerRow>>("/studio/partners?page_size=100");
  if (!pr.ok) return <ErrorState message={pr.error} />;
  const partners = await Promise.all(pr.data.items.map(async (p) => {
    const d = await sGet<StudioPartnerDetail>(`/studio/partners/${p.id}`);
    return { id: p.id, name: p.name, status: p.verification_status, traditions: d.ok ? d.data.traditions : [] };
  }));
  return (
    <>
      <PageHeader eyebrow="Studio Instruktur" title="Dokumentasikan gerakan"
        description="Mulai dengan nama, mitra, dan tradisi. Isi lengkap (fase, keselamatan, sumber, hak) ditulis di editor setelah ini. Versi pertama berstatus draf dan tersimpan otomatis." />
      <NewMovementForm partners={partners} initialPartner={sp.partner} />
    </>
  );
}
