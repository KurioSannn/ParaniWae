import Link from "next/link";
import { BookOpen, Clock, Layers, ShieldCheck } from "lucide-react";
import { EnrollButton } from "@/components/EnrollButton";
import { Card, ProgressBar } from "@/components/ui";
import { MovementVisual } from "@/components/knowledge/Bits";
import { formatMinutes } from "@/lib/format";
import { getCurrentUser, sGet } from "@/lib/server-api";
import type { CourseDetailK } from "@/lib/research";
import { LEVEL_ID } from "@/lib/research";
import type { CourseDetail } from "@/lib/types";

/** Halaman kursus pengetahuan publik. Pendaftaran & progres hanya tampil bila kursus juga aktif di akun pelajar. */
export async function KnowledgeCourse({ c }: { c: CourseDetailK }) {
  const [db, user] = await Promise.all([sGet<CourseDetail>(`/courses/${encodeURIComponent(c.slug)}`), getCurrentUser()]);
  const first = c.modules[0]?.lessons[0];
  const enrollment = db.ok ? db.data.enrollment : null;
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/academy">Akademi</Link> / {c.title}</nav>
      <header className="mb-8 max-w-3xl">
        <p className="mb-2 text-sm font-medium uppercase tracking-widest text-bronze-700"><Link className="hover:underline" href={`/heritage/${c.tradition.slug}`}>{c.tradition.name}</Link></p>
        <h1 className="font-serif text-3xl leading-tight text-forest-900 sm:text-4xl">{c.title}</h1>
        <p className="mt-3 text-lg leading-relaxed text-slate-600">{c.summary}</p>
        <p className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-600">
          <span className="inline-flex items-center gap-1.5"><Layers aria-hidden className="h-4 w-4" />{c.module_count} modul</span>
          <span className="inline-flex items-center gap-1.5"><BookOpen aria-hidden className="h-4 w-4" />{c.lesson_count} pelajaran</span>
          <span className="inline-flex items-center gap-1.5"><Clock aria-hidden className="h-4 w-4" />{formatMinutes(c.estimated_minutes)}</span>
          <span>{LEVEL_ID[c.level] ?? c.level}</span>
        </p>
      </header>

      <div className="grid gap-10 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-10">
          {c.goals.length > 0 && (
            <section aria-labelledby="tujuan"><h2 id="tujuan" className="mb-3 font-serif text-2xl text-forest-900">Yang akan Anda pelajari</h2>
              <ul className="grid gap-2 sm:grid-cols-2">{c.goals.map((g) => <li key={g} className="rounded-xl bg-parchment-100 p-3 text-sm">{g}</li>)}</ul></section>
          )}

          <section aria-labelledby="kurikulum"><h2 id="kurikulum" className="mb-4 font-serif text-2xl text-forest-900">Kurikulum</h2>
            <ol className="space-y-5">
              {c.modules.map((m) => (
                <li key={m.order}>
                  <h3 className="font-semibold"><span className="mr-2 font-serif text-bronze-700">{String(m.order).padStart(2, "0")}</span>{m.title}</h3>
                  <p className="text-sm text-slate-600">{m.summary}</p>
                  <ol className="mt-2 divide-y divide-line-200 rounded-2xl border border-line-200 bg-paper-50">
                    {m.lessons.map((l) => (
                      <li key={l.slug} className="flex items-start gap-3 px-4 py-3">
                        <span className="mt-0.5 w-6 shrink-0 text-sm text-slate-600">{l.order}</span>
                        <div className="flex-1"><Link className="font-medium hover:underline" href={`/academy/courses/${c.slug}/lessons/${l.slug}`}>{l.title}</Link>
                          <p className="text-sm text-slate-600">{l.description}</p></div>
                        <span className="shrink-0 text-sm text-slate-600">{l.duration_min} mnt</span>
                      </li>
                    ))}
                  </ol>
                </li>
              ))}
            </ol>
          </section>

          {c.movements.length > 0 && (
            <section aria-labelledby="gerakan"><h2 id="gerakan" className="mb-4 font-serif text-2xl text-forest-900">Gerakan yang diajarkan ({c.movements.length})</h2>
              <ul className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6">
                {c.movements.map((m) => (
                  <li key={m.slug}><Link href={`/library/${m.slug}`} className="block text-xs hover:underline">
                    <MovementVisual a={m.animation} title={m.name} compact /><span className="mt-1 block">{m.name}</span></Link></li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <Card>
            {first && <Link href={`/academy/courses/${c.slug}/lessons/${first.slug}`} className="block rounded-xl bg-forest-700 px-5 py-3 text-center font-medium text-paper-50 hover:bg-forest-900">Mulai belajar</Link>}
            <p className="mt-3 text-sm text-slate-600">Semua pelajaran terbuka untuk dibaca. {db.ok ? "Masuk dan ikuti kursus ini bila ingin menyimpan progres." : ""}</p>
            {db.ok && <div className="mt-3"><EnrollButton slug={c.slug} enrolled={!!enrollment} loggedIn={!!user} /></div>}
            {enrollment && <div className="mt-4"><ProgressBar progress={enrollment.progress} label="Progres Anda" /></div>}
          </Card>
          <Card className="text-sm text-slate-600"><p className="flex gap-2"><ShieldCheck aria-hidden className="h-5 w-5 shrink-0 text-forest-700" />{c.safety_notes}</p></Card>
        </aside>
      </div>
    </>
  );
}
