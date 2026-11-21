import Link from "next/link";
import { notFound } from "next/navigation";
import { Camera, CheckCircle2, ShieldCheck } from "lucide-react";
import { MovementStage } from "@/components/knowledge/MovementStage";
import { clipForSlug, type CharacterManifest } from "@/lib/character";
import { LessonActions } from "@/components/LessonActions";
import { Card, ErrorState } from "@/components/ui";
import { MovementVisual, SafetyPill } from "@/components/knowledge/Bits";
import { apiGet } from "@/lib/api";
import { formatMinutes, paragraphs } from "@/lib/format";
import { getCurrentUser, sGet } from "@/lib/server-api";
import type { LessonDetail as KLesson } from "@/lib/research";
import type { LessonDetail } from "@/lib/types";

type P = { params: Promise<{ slug: string; lessonSlug: string }> };
const kPath = (s: string, l: string) => `/research/curricula/${encodeURIComponent(s)}/${encodeURIComponent(l)}`;
const dbPath = (s: string, l: string) => `/courses/${encodeURIComponent(s)}/lessons/${encodeURIComponent(l)}`;

export async function generateMetadata({ params }: P) {
  const { slug, lessonSlug } = await params;
  const canonical = `/academy/courses/${slug}/lessons/${lessonSlug}`;
  const k = await apiGet<KLesson>(kPath(slug, lessonSlug));
  if (k.ok) return { title: `${k.data.title} — ${k.data.course.title}`, description: k.data.description.slice(0, 160), alternates: { canonical } };
  const d = await apiGet<LessonDetail>(dbPath(slug, lessonSlug));
  return { title: d.ok ? `${d.data.title} — ${d.data.course.title}` : "Pelajaran", alternates: { canonical } };
}

function Sec({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return <section aria-labelledby={id} className="mt-10"><h2 id={id} className="mb-3 font-serif text-2xl text-forest-900">{title}</h2>{children}</section>;
}

/** Pelajaran publik: terbuka tanpa login. Bila pengguna masuk & mengikuti kursus, progres dapat disimpan. */
export default async function PublicLessonPage({ params }: P) {
  const { slug, lessonSlug } = await params;
  const [k, db, user, ch, pr] = await Promise.all([apiGet<KLesson>(kPath(slug, lessonSlug)), sGet<LessonDetail>(dbPath(slug, lessonSlug)), getCurrentUser(),
    apiGet<CharacterManifest>("/research/character"), apiGet<{ items: { movement_id: string; status: string }[] }>("/research/assessment/protocols")]);
  const manifest = ch.ok ? ch.data : null;
  const practicable = (mslug: string) => pr.ok && pr.data.items.some((x) => x.status === "active" && x.movement_id.endsWith(`.${mslug}`));
  if (!k.ok && !db.ok) return (k.status === 404 && db.status === 404) ? notFound() : <ErrorState message={db.ok ? k.error : db.error} retryHref={`/academy/courses/${slug}/lessons/${lessonSlug}`} />;
  const base = `/academy/courses/${slug}/lessons`;
  const progress = db.ok && user ? <div className="mt-10"><LessonActions lessonId={db.data.id} courseSlug={slug} enrolled={db.data.enrolled} completed={db.data.lesson_status === "completed"} /></div> : null;

  if (!k.ok && db.ok) {
    // Pelajaran dari kurikulum mitra (Studio)
    const l = db.data;
    return (
      <article>
        <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href={`/academy/courses/${slug}`}>{l.course.title}</Link> / {l.module_title}</nav>
        <h1 className="font-serif text-3xl text-forest-900 sm:text-4xl">{l.title}</h1>
        {formatMinutes(l.estimated_minutes) && <p className="mt-1 text-sm text-slate-600">Perkiraan {formatMinutes(l.estimated_minutes)}</p>}
        {l.objective && <p className="mt-4 text-lg text-slate-600">{l.objective}</p>}
        <div className="mt-6 max-w-[72ch] space-y-4 text-lg leading-relaxed">{paragraphs(l.body).map((p, i) => <p key={i}>{p}</p>)}</div>
        {l.safety_notes && <Card className="mt-6 border-bronze-500/40"><h2 className="font-serif text-xl text-forest-900">Keselamatan</h2><p className="text-slate-600">{l.safety_notes}</p></Card>}
        {l.movement && <p className="mt-6"><Link className="underline" href={`/library/${l.movement.id}`}>Gerakan: {l.movement.name_id}</Link></p>}
        {user && l.practice.available && <p className="mt-4"><Link className="underline" href={`/app/courses/${slug}/lessons/${l.slug}`}>Buka latihan dengan kamera</Link></p>}
        {progress}
        <nav aria-label="Navigasi pelajaran" className="mt-10 flex justify-between gap-4 border-t border-line-200 pt-4">
          {l.prev_lesson ? <Link href={`${base}/${l.prev_lesson.slug}`} className="underline">← {l.prev_lesson.title}</Link> : <span />}
          {l.next_lesson ? <Link href={`${base}/${l.next_lesson.slug}`} className="underline">{l.next_lesson.title} →</Link> : <Link href={`/academy/courses/${slug}`} className="underline">Kembali ke kurikulum</Link>}
        </nav>
      </article>
    );
  }

  const l = (k as { ok: true; data: KLesson }).data;
  return (
    <article>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/academy">Akademi</Link> / <Link className="underline" href={`/academy/courses/${slug}`}>{l.course.title}</Link> / {l.module}</nav>
      <p className="text-sm font-medium uppercase tracking-widest text-bronze-700">{l.module}</p>
      <h1 className="mt-1 font-serif text-3xl text-forest-900 sm:text-4xl">{l.title}</h1>
      <p className="mt-3 max-w-prose text-lg leading-relaxed text-slate-600">{l.description}</p>
      <p className="mt-2 text-sm text-slate-600">±{l.duration_min} menit · Peralatan: {l.equipment} · Ruang: {l.space}</p>

      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <Card><p className="font-medium">Tujuan belajar</p><ul className="mt-2 space-y-1.5 text-sm">{l.objectives.map((o) => <li key={o} className="flex gap-2"><CheckCircle2 aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-forest-700" />{o}</li>)}</ul></Card>
        <Card><p className="font-medium">Sebelum mulai</p><p className="mt-2 text-sm"><strong className="font-medium">Prasyarat:</strong> {l.prior_competence}</p>
          <p className="mt-3 flex gap-2 text-sm"><ShieldCheck aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-forest-700" />{l.safety_briefing}</p></Card>
      </div>

      <Sec id="teori" title="Materi"><div className="max-w-prose space-y-4 text-lg leading-relaxed">{paragraphs(l.theory).map((p, i) => <p key={i}>{p}</p>)}</div></Sec>
      <Sec id="budaya" title="Konteks budaya"><div className="max-w-prose space-y-4 leading-relaxed">{paragraphs(l.cultural_explanation).map((p, i) => <p key={i}>{p}</p>)}</div></Sec>

      {l.movements.length > 0 && (
        <Sec id="gerakan" title={l.movements.length > 1 ? `Gerakan dalam pelajaran ini (${l.movements.length})` : "Gerakan dalam pelajaran ini"}>
          <div className="space-y-6">
            {l.movements.map((m) => {
              const mistakes = m.common_mistakes.map((x) => (typeof x === "string" ? x : x.text));
              return (
                <Card key={m.slug}>
                  <div className="grid gap-6 md:grid-cols-[15rem_1fr]">
                    <MovementStage clip={clipForSlug(manifest, m.slug)} title={m.name} twoD={<MovementVisual a={m.animation} title={m.name} />} />
                    <div>
                      <h3 className="font-serif text-xl text-forest-900"><Link className="hover:underline" href={`/library/${m.slug}`}>{m.name}</Link></h3>
                      <div className="mt-1"><SafetyPill cls={m.safety_class} /></div>
                      <ol className="mt-4 space-y-2">{m.phases.map((p) => (
                        <li key={p.id} className="flex gap-3 text-sm"><span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-forest-700 text-[11px] text-paper-50">{p.order}</span>
                          <span><strong className="font-medium">{p.name}.</strong> {p.change !== "—" ? p.change : p.start_position} <span className="text-slate-600">→ {p.end_position}</span></span></li>))}</ol>
                      {mistakes.length > 0 && <p className="mt-3 text-sm"><strong className="font-medium">Perhatikan:</strong> {mistakes.join("; ")}</p>}
                      <Link className="mt-3 inline-block text-sm underline" href={`/library/${m.slug}`}>Uraian lengkap & posisi tubuh →</Link>
                      {practicable(m.slug) && (
                        <Link href={`/library/${m.slug}/latihan?pelajaran=${encodeURIComponent(`${slug}/${lessonSlug}`)}`}
                          className="mt-3 flex w-fit items-center gap-2 rounded-xl bg-forest-700 px-4 py-2 text-sm font-medium text-paper-50 hover:bg-forest-900">
                          <Camera aria-hidden className="h-4 w-4" />Coba Latihan Sekarang</Link>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </Sec>
      )}

      {l.practice_steps.length > 0 && <Sec id="latihan" title="Latihan mandiri"><ol className="list-decimal space-y-1.5 pl-5">{l.practice_steps.map((s) => <li key={s}>{s}</li>)}</ol></Sec>}
      <Sec id="rangkuman" title="Rangkuman"><p className="max-w-prose text-lg">{l.summary}</p></Sec>
      <Sec id="refleksi" title="Refleksi"><ul className="list-disc space-y-1 pl-5">{l.reflection.map((x) => <li key={x}>{x}</li>)}</ul></Sec>

      {l.quiz.length > 0 && (
        <Sec id="kuis" title="Uji pemahaman">
          <ol className="space-y-3">{l.quiz.map((q, i) => (
            <li key={q.q}><Card>
              <p className="font-medium">{i + 1}. {q.q}</p>
              <ul className="mt-2 space-y-1 text-sm">{q.options.map((o, j) => <li key={o}>{"ABCD"[j]}. {o}</li>)}</ul>
              <details className="mt-2 text-sm"><summary className="cursor-pointer text-forest-700 underline">Lihat jawaban</summary>
                <p className="mt-1">{"ABCD"[q.answer_index]}. {q.options[q.answer_index]}</p></details>
            </Card></li>))}</ol>
        </Sec>
      )}

      {progress}

      <nav aria-label="Navigasi pelajaran" className="mt-10 flex justify-between gap-4 border-t border-line-200 pt-4">
        {l.prev ? <Link className="underline" href={`${base}/${l.prev.slug}`}>← {l.prev.title}</Link> : <Link className="underline" href={`/academy/courses/${slug}`}>← Kurikulum</Link>}
        {l.next ? <Link className="underline" href={`${base}/${l.next.slug}`}>{l.next.title} →</Link> : <Link className="underline" href={`/academy/courses/${slug}`}>Selesai — kembali ke kurikulum</Link>}
      </nav>
    </article>
  );
}
