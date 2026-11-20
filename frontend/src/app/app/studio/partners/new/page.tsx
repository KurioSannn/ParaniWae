import { PageHeader } from "@/components/ui";
import { NewPartnerForm } from "@/components/studio/NewPartnerForm";
import { requireUser } from "@/lib/server-api";

export default async function NewPartnerPage() {
  await requireUser("/app/studio/partners/new", ["instructor", "curator", "admin"]);
  return (
    <>
      <PageHeader eyebrow="Studio Instruktur" title="Profil mitra baru"
        description="Profil ini disimpan sebagai draf dan belum menjadikan organisasi Anda mitra resmi. Verifikasi memerlukan penanggung jawab, kontak, cakupan tradisi, dan dokumen persetujuan, lalu diputuskan admin dengan bukti." />
      <NewPartnerForm />
    </>
  );
}
