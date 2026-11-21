import Link from "next/link";
import { notFound } from "next/navigation";
import { CheckCircle2, Circle } from "lucide-react";
import { Card, ErrorState, PageHeader, ProgressBar } from "@/components/ui";
import { EnrollButton } from "@/components/EnrollButton";
import { formatMinutes, LEVEL_LABEL } from "@/lib/format";
import { getCurrentUser, sGet } from "@/lib/server-api";
import type { CourseDetail } from "@/lib/types";
import { apiGet } from "@/lib/api";
import type { CourseDetailK } from "@/lib/research";
import { KnowledgeCourse } from "@/components/knowledge/KnowledgeCourse";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const k = await apiGet<CourseDetailK>(`/research/courses/${encodeURIComponent(slug)}`);
  if (k.ok) return { title: `${k.data.title} — Akademi`, description: k.data.summary.slice(0, 160), alternates: { canonical: `/academy/courses/${slug}` } };
  return { title: "Kurikulum — Akademi", alternates: { canonical: `/academy/courses/${slug}` } };
}

export default async function CoursePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const k = await apiGet<CourseDetailK>(`/research/courses/${encodeURIComponent(slug)}`);
  if (k.ok) return <KnowledgeCourse c={k.data} />;
  const [r, user] = await Promise.all([sGet<CourseDetail>(`/courses/${encodeURIComponent(slug)}`), getCurrentUser()]);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/academy/courses/${slug}`} />;
  const c = r.data;
  const enrolled = !!c.enrollment;
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/academy">Akademi</Link> / {c.title}</nav>
      <PageHeader eyebrow={`${LEVEL_LABEL[c.level] ?? c.level} · ${c.lesson_count} pelajaran${formatMinutes(c.estimated_minutes) ? ` · ${formatMinutes(c.estimated_minutes)}` : ""}`}
        title={c.title} description={c.summary ?? undefined} />
      <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-8">
          {c.enrollment && <Card><ProgressBar progress={c.enrollment.progress} label="Progres Anda" />
            {c.enrollment.next_lesson_slug && <Link className="mt-3 inline-block rounded-xl bg-forest-700 px-4 py-2 font-medium text-paper-50" href={`/app/courses/${c.slug}/lessons/${c.enrollment.next_lesson_slug}`}>
              {c.enrollment.progress.completed ? "Lanjutkan belajar" : "Mulai belajar"}</Link>}</Card>}
          {c.safety_notes && <Card className="border-bronze-500/40"><h2 className="font-semibold">Catatan keselamatan</h2><p className="mt-1 text-sm text-slate-600">{c.safety_notes}</p></Card>}
          <section aria-labelledby="isi"><h2 id="isi" className="mb-4 font-serif text-2xl text-forest-900">Isi kurikulum</h2>
            {c.modules.map((m) => (
              <div key={m.id} className="mb-5"><h3 className="mb-2 font-semibold">{m.title}</h3>
                <ol className="divide-y divide-line-200 rounded-2xl border border-line-200 bg-paper-50">
                  {m.lessons.map((l) => (
                    <li key={l.id} className="flex items-center gap-3 px-4 py-3">
                      {l.completed ? <CheckCircle2 aria-label="Selesai" className="h-5 w-5 text-forest-700" /> : <Circle aria-hidden className="h-5 w-5 text-line-200" />}
                      <Link className="flex-1 hover:underline" href={`/academy/courses/${c.slug}/lessons/${l.slug}`}>{l.title}</Link>
                      {formatMinutes(l.estimated_minutes) && <span className="text-sm text-slate-600">{formatMinutes(l.estimated_minutes)}</span>}
                    </li>))}
                </ol></div>))}
          </section>
        </div>
        <div className="space-y-4">
          <EnrollButton slug={c.slug} enrolled={enrolled} loggedIn={!!user} />
          <Card className="text-sm text-slate-600">
            {c.tradition_name && <p>Tradisi: <Link className="underline" href={`/heritage/${c.tradition_slug}`}>{c.tradition_name}</Link></p>}
            {c.instructor && <p>Instruktur: {c.instructor.name}</p>}
          </Card>
        </div>
      </div>
    </>
  );
}
