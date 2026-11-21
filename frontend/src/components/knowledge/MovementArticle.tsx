import Link from "next/link";
import { Card } from "@/components/ui";
import { MovementVisual, Pill, SafetyPill } from "@/components/knowledge/Bits";
import { Camera } from "lucide-react";
import { MovementStage } from "@/components/knowledge/MovementStage";
import type { ClipMeta } from "@/lib/character";
import type { MovementDetail, TextNode } from "@/lib/research";
import { LEVEL_ID } from "@/lib/research";

const SOLO_NOTE: Record<string, string> = {
  documented_solo: "Dapat dilatih sendiri.",
  inferred_not_documented: "Gerak pembelaan ini dipelajari sebagai pengetahuan; latihannya sebaiknya bersama pelatih.",
  partner_form: "Dilatih berpasangan bersama pelatih.",
};

function T({ n }: { n: TextNode }) {
  return <>{n.text}</>;
}

function H({ id, children }: { id: string; children: React.ReactNode }) {
  return <h2 id={id} className="mb-3 mt-10 scroll-mt-6 font-serif text-2xl text-forest-900">{children}</h2>;
}

/** Artikel gerakan (pengetahuan berbasis sumber) untuk Pustaka Gerakan. */
export function MovementArticle({ m, clip = null, practice = false }: { m: MovementDetail; clip?: ClipMeta | null; practice?: boolean }) {
  const mistakes = m.common_mistakes.map((x) => (typeof x === "string" ? x : x.text));
  const anatomy = m.anatomy.filter((a) => a.basis !== "needs_validation" || a.text !== "Tidak dirinci dalam sumber.");
  const hasMeaning = m.cultural.meaning.basis !== "gap";
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/library">Pustaka Gerakan</Link> / <Link className="underline" href={`/library?kategori=${encodeURIComponent(m.category)}`}>{m.category_label}</Link></nav>
      <div className="grid gap-8 lg:grid-cols-[1fr_22rem]">
        <aside className="space-y-4 lg:order-2 lg:sticky lg:top-6 lg:self-start">
          <MovementStage clip={clip} title={m.names.primary} twoD={<MovementVisual a={m.animation} title={m.names.primary} />} />
          {m.animation.status === "generated" && <p className="text-xs text-slate-600">Peraga gerak disusun dari uraian di halaman ini. Ukuran langkah dan kedalaman kuda-kuda dapat berbeda di setiap perguruan.</p>}
          {practice && (
            <Card>
              <p className="flex items-center gap-2 font-medium"><Camera aria-hidden className="h-4 w-4 text-bronze-700" />Coba latihan sekarang</p>
              <p className="mt-1 text-sm text-slate-600">Kamera membantu mengukur posisi tubuh Anda dan memberi skor kesesuaian serta saran perbaikan. Video tidak dikirim atau disimpan.</p>
              <Link href={`/library/${m.slug}/latihan`} className="mt-3 inline-flex rounded-xl bg-forest-700 px-4 py-2 text-sm font-medium text-paper-50 hover:bg-forest-900">Coba Latihan Sekarang</Link>
            </Card>
          )}
          {m.used_in.length > 0 && (
            <Card><p className="text-sm font-medium">Dipelajari di Akademi</p>
              <ul className="mt-2 space-y-1 text-sm">{m.used_in.map((u) => <li key={u.lesson_slug}><Link className="underline" href={`/academy/courses/${u.course_slug}/lessons/${u.lesson_slug}`}>{u.lesson_title}</Link></li>)}</ul></Card>
          )}
        </aside>
        <article className="lg:order-1">
          <p className="text-sm font-medium uppercase tracking-widest text-bronze-700">{m.category_label}</p>
          <h1 className="mt-1 font-serif text-3xl text-forest-900 sm:text-4xl">{m.names.primary}</h1>
          {m.names.aliases.length > 0 && <p className="mt-1 text-slate-600">Dikenal juga sebagai {m.names.aliases.join(", ")}</p>}
          <div className="mt-3 flex flex-wrap gap-2">
            <SafetyPill cls={m.safety_class} />
            <Pill>{LEVEL_ID[m.level] ?? m.level}</Pill>
            <Pill>{m.phases.length} fase</Pill>
            <Pill><Link href={`/heritage/${m.tradition_slug}`} className="hover:underline">{m.tradition}</Link></Pill>
          </div>
          <p className="mt-4 max-w-prose text-lg leading-relaxed text-slate-600"><T n={m.cultural.purpose} /></p>
          <p className="mt-2 text-sm text-slate-600">{SOLO_NOTE[m.solo_form_status] ?? ""}</p>


          <H id="langkah">Langkah demi langkah</H>
          <ol className="space-y-3">
            {m.phases.map((p) => (
              <li key={p.id}><Card>
                <p className="font-medium"><span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-forest-700 text-xs text-paper-50">{p.order}</span>{p.name}</p>
                <dl className="mt-2 grid gap-x-4 gap-y-1 text-sm sm:grid-cols-[8.5rem_1fr]">
                  <dt className="text-slate-600">Mulai dari</dt><dd>{p.start_position}</dd>
                  {p.change !== "—" && <><dt className="text-slate-600">Gerakan</dt><dd>{p.change}</dd></>}
                  {p.body_parts.length > 0 && <><dt className="text-slate-600">Bagian tubuh</dt><dd>{p.body_parts.join(", ")}</dd></>}
                  {p.direction !== "—" && <><dt className="text-slate-600">Arah</dt><dd>{p.direction}</dd></>}
                  <dt className="text-slate-600">Hasil akhir</dt><dd>{p.end_position}</dd>
                  {p.safety && <><dt className="text-slate-600">Perhatikan</dt><dd>{p.safety}</dd></>}
                </dl>
              </Card></li>
            ))}
          </ol>

          {anatomy.length > 0 && <>
            <H id="anatomi">Posisi tubuh</H>
            <dl className="grid gap-x-4 gap-y-2 text-sm sm:grid-cols-[10rem_1fr]">
              {anatomy.map((a) => <div key={a.key} className="contents"><dt className="text-slate-600">{a.label}</dt><dd>{a.text}</dd></div>)}
            </dl>
          </>}

          <H id="budaya">Konteks budaya</H>
          <div className="max-w-prose space-y-3">
            <p><T n={m.cultural.context} /></p>
            {hasMeaning && <p><T n={m.cultural.meaning} /></p>}
            {m.cultural.terminology.length > 0 && <p><strong>Istilah:</strong> {m.cultural.terminology.map((t) => `${t.term} — ${t.explanation}`).join("; ")}</p>}
            {m.cultural.variants.length > 0 && <div><p className="font-medium">Ragam uraian</p><ul className="mt-1 list-disc space-y-1 pl-5 text-slate-600">{m.cultural.variants.map((v, i) => <li key={i}><T n={v} /></li>)}</ul></div>}
            {m.cultural.differs_from.length > 0 && <div><p className="font-medium">Bandingkan dengan</p><ul className="mt-1 list-disc pl-5 text-slate-600">{m.cultural.differs_from.map((d) => { const s = d.movement_id.split(".").pop()!; return <li key={s}><Link className="underline" href={`/library/${s}`}>{s.replace(/-/g, " ")}</Link>: {d.text}</li>; })}</ul></div>}
          </div>

          <H id="latihan">Panduan latihan mandiri</H>
          <dl className="grid gap-x-4 gap-y-1.5 text-sm sm:grid-cols-[10rem_1fr]">
            <dt className="text-slate-600">Kemampuan awal</dt><dd>{m.prerequisites.abilities}</dd>
            <dt className="text-slate-600">Persiapan</dt><dd>{m.prerequisites.physical_prep}</dd>
            <dt className="text-slate-600">Ruang & lantai</dt><dd>{m.prerequisites.space} {m.prerequisites.surface}</dd>
            <dt className="text-slate-600">Mulai</dt><dd>{m.practice.start}</dd>
            <dt className="text-slate-600">Urutan</dt><dd>{m.practice.sequence}</dd>
            <dt className="text-slate-600">Tempo</dt><dd>{m.practice.tempo.text}</dd>
            <dt className="text-slate-600">Pengulangan</dt><dd>{m.practice.repetitions.text}</dd>
            {m.practice.easier !== "—" && <><dt className="text-slate-600">Versi lebih mudah</dt><dd>{m.practice.easier}</dd></>}
            {m.practice.progression !== "—" && <><dt className="text-slate-600">Langkah berikutnya</dt><dd>{m.practice.progression}</dd></>}
            <dt className="text-slate-600">Berhenti bila</dt><dd>{m.practice.stop_when.join(" ")}</dd>
          </dl>
          <p className="mt-3 text-sm text-slate-600">{m.prerequisites.limits}</p>

          {mistakes.length > 0 && <><H id="perhatian">Hal yang perlu diperhatikan</H><ul className="list-disc pl-5">{mistakes.map((x) => <li key={x}>{x}</li>)}</ul></>}
          {m.gaps.length > 0 && <p className="mt-6 text-sm text-slate-600"><strong className="font-medium text-ink-950">Belum dirinci sumber:</strong> {m.gaps.join(" ")} Tanyakan detail ini kepada pelatih Anda.</p>}
        </article>

      </div>
    </>
  );
}
