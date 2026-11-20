import Link from "next/link";
import { BookOpenCheck, Camera, ShieldCheck } from "lucide-react";
import { CourseCard } from "@/components/Cards";
import { Card, Grid } from "@/components/ui";
import { qs } from "@/lib/api";
import { sGet } from "@/lib/server-api";
import type { CourseSummary, Page } from "@/lib/types";

const principles = [
  { icon: BookOpenCheck, title: "Dipandu mitra budaya", body: "Materi hanya terbit setelah sumber dan persetujuan tercatat. Selama belum ada mitra yang menyetujui, materi ditandai belum diverifikasi." },
  { icon: Camera, title: "Kamera opt-in, di perangkat", body: "Kamera hanya menyala atas pilihan Anda dan dapat dihentikan kapan saja. Video tidak direkam atau dikirim." },
  { icon: ShieldCheck, title: "Alat bantu, bukan penentu", body: "Instruktur tetap otoritas atas gerakan dan tingkatan. AI hanyalah bantuan latihan, dan penilaian gerakan belum tersedia." },
];

export default async function Home() {
  const courses = await sGet<Page<CourseSummary>>(`/courses${qs({ page_size: 3, sort: "newest" })}`);
  return (
    <div className="space-y-16">
      <section className="max-w-3xl space-y-5">
        <p className="text-sm font-medium uppercase tracking-widest text-bronze-700">Warisan Nusantara</p>
        <h1 className="font-serif text-4xl leading-tight text-forest-900 sm:text-5xl">Pelajari Gerak. Pahami Warisan.</h1>
        <p className="text-lg text-slate-600">SILATARA sedang dibangun bersama perguruan dan instruktur mitra sebagai ruang belajar dan pelestarian pencak silat. Saat ini tersedia alur belajar dasar dengan <strong>konten contoh [DEMO]</strong>; belum ada materi budaya resmi.</p>
        <div className="flex flex-wrap gap-3">
          <Link href="/academy" className="rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900">Lihat akademi</Link>
          <Link href="/heritage" className="rounded-xl border border-line-200 bg-paper-50 px-5 py-3 font-medium hover:bg-parchment-100">Jelajahi warisan</Link>
        </div>
      </section>
      <section aria-labelledby="alur"><h2 id="alur" className="mb-4 font-serif text-2xl text-forest-900">Alur belajar</h2>
        <ol className="grid gap-4 md:grid-cols-4">{["Jelajahi tradisi dan perguruan", "Pilih kurikulum dan ikuti", "Buka pelajaran dan tandai selesai", "Pantau progres belajar"].map((t, i) => (
          <li key={t}><Card className="h-full"><span className="font-serif text-2xl text-bronze-700">{i + 1}</span><p className="mt-1 font-medium">{t}</p></Card></li>))}</ol></section>
      <section aria-labelledby="kur"><div className="mb-4 flex items-end justify-between"><h2 id="kur" className="font-serif text-2xl text-forest-900">Kurikulum terbaru</h2><Link className="underline" href="/academy">Semua kurikulum</Link></div>
        {courses.ok && courses.data.items.length > 0 ? <Grid>{courses.data.items.map((c) => <CourseCard key={c.id} c={c} />)}</Grid>
          : <Card className="text-slate-600">{courses.ok ? "Belum ada kurikulum terbit." : "Daftar kurikulum belum dapat dimuat saat ini."}</Card>}</section>
      <section aria-labelledby="prinsip"><h2 id="prinsip" className="mb-4 font-serif text-2xl text-forest-900">Prinsip kami</h2>
        <ul className="grid gap-4 md:grid-cols-3">{principles.map(({ icon: Icon, title, body }) => (
          <li key={title}><Card className="h-full"><Icon aria-hidden className="mb-3 h-6 w-6 text-forest-700" /><h3 className="font-semibold">{title}</h3><p className="mt-1 text-sm text-slate-600">{body}</p></Card></li>))}</ul></section>
    </div>
  );
}
