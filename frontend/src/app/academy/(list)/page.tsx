import Link from "next/link";
import { BookOpen, Clock, Layers } from "lucide-react";
import { PageHeader } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { formatMinutes } from "@/lib/format";
import type { Curricula } from "@/lib/research";
import { LEVEL_ID } from "@/lib/research";

export const metadata = {
  title: "Akademi",
  description: "Belajar pencak silat selangkah demi selangkah: kursus terstruktur dengan animasi, uraian fase, panduan latihan mandiri, dan kuis — terbuka untuk semua.",
  alternates: { canonical: "/academy" },
};

export default async function AcademyPage() {
  const k = await apiGet<Curricula>("/research/curricula");
  const courses = k.ok ? k.data.items : [];
  return (
    <>
      <PageHeader eyebrow="Akademi" title="Belajar pencak silat selangkah demi selangkah"
        description="Mulai dari pengetahuan dasar, pahami setiap gerakan lewat animasi dan uraian fase, lalu berlatih dengan panduan yang jelas. Semua kelas dapat dibaca tanpa mendaftar; masuk akun hanya bila Anda ingin menyimpan progres." />

      <ul className="space-y-6">
        {courses.map((c) => {
          const lessons = c.modules.reduce((n, m) => n + m.lessons.length, 0);
          const first = c.modules[0]?.lessons[0];
          return (
            <li key={c.slug} className="overflow-hidden rounded-3xl border border-line-200 bg-paper-50">
              <div className="grid gap-6 p-6 md:grid-cols-[1.4fr_1fr] md:p-8">
                <div>
                  <p className="text-sm font-medium uppercase tracking-widest text-bronze-700">{c.tradition}</p>
                  <h2 className="mt-1 font-serif text-3xl text-forest-900"><Link className="hover:underline" href={`/academy/courses/${c.slug}`}>{c.title}</Link></h2>
                  <p className="mt-3 text-lg leading-relaxed text-slate-600">{c.summary}</p>
                  <p className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-600">
                    <span className="inline-flex items-center gap-1.5"><Layers aria-hidden className="h-4 w-4" />{c.modules.length} modul</span>
                    <span className="inline-flex items-center gap-1.5"><BookOpen aria-hidden className="h-4 w-4" />{lessons} pelajaran</span>
                    <span className="inline-flex items-center gap-1.5"><Clock aria-hidden className="h-4 w-4" />{formatMinutes(c.estimated_minutes)}</span>
                    <span>{LEVEL_ID[c.level] ?? c.level}</span>
                  </p>
                  <div className="mt-6 flex flex-wrap gap-3">
                    <Link href={`/academy/courses/${c.slug}`} className="rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900">Lihat kurikulum</Link>
                    {first && <Link href={`/academy/courses/${c.slug}/lessons/${first.slug}`} className="rounded-xl border border-line-200 px-5 py-3 font-medium hover:bg-parchment-100">Mulai pelajaran pertama</Link>}
                  </div>
                </div>
                <ol className="space-y-2 self-start rounded-2xl bg-parchment-100 p-5 text-sm">
                  {c.modules.map((m) => <li key={m.id}><span className="mr-2 font-serif text-bronze-700">{String(m.order).padStart(2, "0")}</span>{m.title}</li>)}
                </ol>
              </div>
            </li>
          );
        })}
      </ul>

    </>
  );
}
