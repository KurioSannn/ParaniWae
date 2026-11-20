import Link from "next/link";
import { notFound } from "next/navigation";
import { ManageForm } from "@/components/ManageForm";
import { Card, PageHeader } from "@/components/ui";
import { KIND_LABEL } from "@/lib/format";
import { MANAGE_FIELDS } from "@/lib/manage-config";
import { requireUser } from "@/lib/server-api";

export default async function NewContent({ params }: { params: Promise<{ kind: string }> }) {
  const { kind } = await params;
  if (!MANAGE_FIELDS[kind]) notFound();
  const user = await requireUser(`/app/manage/${kind}/new`, ["instructor", "curator", "admin"]);
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href={`/app/manage/${kind}`}>{KIND_LABEL[kind]}</Link> / Baru</nav>
      <PageHeader title={`Buat ${KIND_LABEL[kind]}`} description="Konten baru selalu berstatus draf dan tidak tampil publik sampai disetujui dan diterbitkan." />
      <Card className="max-w-3xl"><ManageForm kind={kind} role={user.role} /></Card>
    </>
  );
}
