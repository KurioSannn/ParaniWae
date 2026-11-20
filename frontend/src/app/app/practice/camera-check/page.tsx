import Link from "next/link";
import { CameraCheck } from "@/components/CameraCheck";
import { PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/server-api";

export const metadata = { title: "Uji kamera" };

export default async function CameraCheckPage() {
  await requireUser("/app/practice/camera-check");
  return (
    <>
      <PageHeader eyebrow="Pratinjau teknis" title="Uji kamera dan visibilitas tubuh"
        description="Periksa apakah kamera dan pencahayaan Anda cukup untuk latihan di masa depan. Fitur penilaian gerakan belum tersedia: menunggu rubrik yang disetujui instruktur mitra.">
        <p className="mt-3 text-sm">Lebih suka tanpa kamera? <Link className="underline" href="/academy">Lanjut belajar lewat pelajaran teks</Link>.</p>
        <p className="mt-1 text-sm">Pengujian teknis: <Link className="underline" href="/app/practice/benchmark">benchmark mesin landmark</Link>.</p>
      </PageHeader>
      <CameraCheck />
    </>
  );
}
