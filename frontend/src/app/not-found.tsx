import Link from "next/link";
import { PageHeader } from "@/components/ui";

export default function NotFound() {
  return (
    <PageHeader eyebrow="404" title="Halaman tidak ditemukan"
      description="Konten yang Anda cari tidak ada, belum diterbitkan, atau bukan untuk akun Anda.">
      <Link href="/" className="mt-4 inline-block underline">Kembali ke beranda</Link>
    </PageHeader>
  );
}
