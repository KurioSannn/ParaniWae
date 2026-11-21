import Link from "next/link";
import { PageHeader } from "@/components/ui";

export default function NotFound() {
  const b = "rounded-full px-6 py-3 text-sm font-semibold transition-all hover:-translate-y-0.5";
  return (
    <>
      <PageHeader eyebrow="404" title="Halaman tidak ditemukan"
        description="Konten yang Anda cari tidak ada, sudah dipindahkan, atau bukan untuk akun Anda." />
      <div className="flex flex-wrap gap-3">
        <Link href="/" className={`${b} bg-gradient-to-r from-[#4a0d0d] via-[#7c1d1d] to-[#c2410c] text-white shadow-md`}>Kembali ke beranda</Link>
        <Link href="/library" className={`${b} border border-slate-300 bg-white text-slate-800 hover:bg-slate-50`}>Pustaka Gerakan</Link>
        <Link href="/community/peta" className={`${b} border border-slate-300 bg-white text-slate-800 hover:bg-slate-50`}>Peta Perguruan</Link>
      </div>
    </>
  );
}
