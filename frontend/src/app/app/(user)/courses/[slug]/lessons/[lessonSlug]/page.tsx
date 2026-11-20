import Link from "next/link";
import { notFound } from "next/navigation";
import { LessonActions } from "@/components/LessonActions";
import { MovementDocumentView } from "@/components/MovementDocumentView";
import { Card, ErrorState, SourceBox } from "@/components/ui";
import { formatMinutes, paragraphs, PRACTICE_MODE_LABEL, SAFETY_LABEL } from "@/lib/format";
import { requireUser, sGet } from "@/lib/server-api";
import type { LessonDetail } from "@/lib/types";

export default async function LessonPage({ params }: { params: Promise<{ slug: string; lessonSlug: string }> }) {
  const { slug, lessonSlug } = await params;
  await requireUser(`/app/courses/${slug}/lessons/${lessonSlug}`);
  const r = await sGet<LessonDetail>(`/courses/${encodeURIComponent(slug)}/lessons/${encodeURIComponent(lessonSlug)}`);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/app/courses/${slug}/lessons/${lessonSlug}`} />;
  const l = r.data;
  const base = `/app/courses/${slug}/lessons`;
  return (
    <article>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href={`/academy/courses/${slug}`}>{l.course.title}</Link> / {l.module_title}</nav>
      <h1 className="font-serif text-3xl text-forest-900 sm:text-4xl">{l.title}</h1>
      {formatMinutes(l.estimated_minutes) && <p className="mt-1 text-sm text-slate-600">Perkiraan {formatMinutes(l.estimated_minutes)}</p>}
      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_18rem]">
        <div className="space-y-6">
          {l.objective && <section aria-labelledby="tujuan"><h2 id="tujuan" className="font-serif text-xl text-forest-900">Tujuan</h2><p className="text-slate-600">{l.objective}</p></section>}
          <section aria-label="Isi pelajaran" className="max-w-[72ch] space-y-4 text-lg leading-relaxed">
            {paragraphs(l.body).map((p, i) => <p key={i}>{p}</p>)}
          </section>
          {l.safety_notes && <Card className="border-bronze-500/40"><h2 className="font-serif text-xl text-forest-900">Keselamatan</h2><p className="text-slate-600">{l.safety_notes}</p></Card>}
          {l.movement && (
            <section aria-labelledby="gerakan" className="rounded-2xl border border-line-200 bg-paper-50 p-5">
              <h2 id="gerakan" className="font-serif text-xl text-forest-900">Gerakan yang dipelajari</h2>
              <p className="mt-1 text-lg font-medium">{l.movement.name_id}{l.movement.name_local ? <span className="font-normal text-slate-600"> · {l.movement.name_local}</span> : null}</p>
              <p className="text-sm text-slate-600">
                {l.movement.partner_name ? <>Perguruan sumber: <Link className="underline" href={`/community/${l.movement.partner_slug}`}>{l.movement.partner_name}</Link> · </> : null}
                {l.movement.safety_category ? `${SAFETY_LABEL[l.movement.safety_category]} · ` : ""}{PRACTICE_MODE_LABEL[l.movement.practice_mode] ?? l.movement.practice_mode}
                {l.movement.version_no ? ` · versi ${l.movement.version_no}` : ""}
              </p>
              {l.movement.document ? <div className="mt-4"><MovementDocumentView doc={l.movement.document} /></div> : <>
                {l.movement.description && <p className="mt-2 text-sm text-slate-600">{l.movement.description}</p>}
                {l.movement.safety_notes && <p className="mt-2 text-sm text-slate-600"><strong>Keselamatan:</strong> {l.movement.safety_notes}</p>}</>}
              <div className="mt-4"><SourceBox p={l.movement.provenance} /></div>
              <p className="mt-3 text-sm"><Link className="underline" href={`/library/${l.movement.id}`}>Lihat halaman gerakan beserta riwayat versi</Link>. Penilaian AI {l.movement.assessment_enabled ? "tersedia" : "belum tersedia untuk gerakan ini"}.</p>
            </section>)}
          {l.materials.length > 0 && (
            <section aria-labelledby="materi"><h2 id="materi" className="mb-2 font-serif text-xl text-forest-900">Materi pendukung</h2>
              <ul className="space-y-3">{l.materials.map((m) => (
                <li key={m.id}><Card><h3 className="font-medium">{m.title}</h3>
                  {m.content && <p className="text-sm text-slate-600">{m.content}</p>}
                  {m.url && <a className="text-sm underline" href={m.url} target="_blank" rel="noopener noreferrer nofollow">Buka tautan (situs luar)</a>}
                  <p className="mt-1 text-xs text-slate-600">Atribusi: {m.attribution_text}</p></Card></li>))}</ul></section>)}
          <section aria-labelledby="latihan" className="rounded-2xl border border-line-200 bg-paper-50 p-4" data-testid="practice-entry">
            <h2 id="latihan" className="font-serif text-xl text-forest-900">Latihan dengan kamera</h2>
            <p className="mt-1 text-sm text-slate-600">{l.practice.label}</p>
            {l.practice.available && l.enrolled && <Link data-testid="start-practice" href={`${base}/${l.slug}/practice`} className="mt-3 inline-block rounded-xl bg-forest-700 px-5 py-3 font-medium text-paper-50 hover:bg-forest-900">Mulai Latihan</Link>}
            {l.practice.available && !l.enrolled && <p className="mt-2 text-sm">Ikuti kurikulum ini terlebih dahulu untuk membuka latihan.</p>}
            {!l.practice.available && <p className="mt-2 text-sm text-slate-600">Latihan kamera belum tersedia untuk pelajaran ini.</p>}
            <p className="mt-2 text-xs text-slate-600">Studio hanya memeriksa keterlihatan tubuh; tidak ada penilaian gerakan. <Link className="underline" href={`/app/practice?lesson=${l.id}`}>Riwayat latihan pelajaran ini</Link></p>
          </section>
          <LessonActions lessonId={l.id} courseSlug={slug} enrolled={l.enrolled} completed={l.lesson_status === "completed"} />
          <nav aria-label="Navigasi pelajaran" className="flex justify-between gap-4 border-t border-line-200 pt-4">
            {l.prev_lesson ? <Link href={`${base}/${l.prev_lesson.slug}`} className="underline">← {l.prev_lesson.title}</Link> : <span />}
            {l.next_lesson ? <Link href={`${base}/${l.next_lesson.slug}`} className="underline">{l.next_lesson.title} →</Link> : <Link href={`/academy/courses/${slug}`} className="underline">Kembali ke kurikulum</Link>}
          </nav>
        </div>
        <SourceBox p={l.provenance} />
      </div>
    </article>
  );
}
