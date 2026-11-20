import { LEVEL_LABEL, LICENSE_LABEL, SAFETY_HINT, SAFETY_LABEL, formatClock, paragraphs } from "@/lib/format";
import { RefImage } from "@/components/studio/bits";
import type { PublicDocument } from "@/lib/types";

function Block({ title, text }: { title: string; text: string | null | undefined }) {
  const ps = paragraphs(text);
  if (!ps.length) return null;
  return <section className="mb-6"><h3 className="mb-2 font-serif text-lg text-forest-900">{title}</h3>{ps.map((p, i) => <p key={i} className="mb-2 max-w-prose">{p}</p>)}</section>;
}

/** Tampilan dokumentasi gerakan (publik/pratinjau). Semua isi = teks yang ditulis instruktur; tidak ada HTML dirender. */
export function MovementDocumentView({ doc, preview = false }: { doc: PublicDocument; preview?: boolean }) {
  return (
    <article aria-label={`Dokumentasi ${doc.name_id}`}>
      <dl className="mb-6 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
        {doc.level && <div><dt className="inline font-medium text-ink-950">Tingkat: </dt><dd className="inline">{LEVEL_LABEL[doc.level]}</dd></div>}
        {doc.safety_category && <div><dt className="inline font-medium text-ink-950">Kategori keselamatan: </dt><dd className="inline">{SAFETY_LABEL[doc.safety_category]}</dd></div>}
        <div><dt className="inline font-medium text-ink-950">Versi: </dt><dd className="inline">{doc.version_no}{preview ? " (pratinjau)" : ""}</dd></div>
        {doc.authors.length > 0 && <div><dt className="inline font-medium text-ink-950">Disusun oleh: </dt><dd className="inline">{doc.authors.join(", ")}</dd></div>}
      </dl>
      {doc.safety_category && <p className="mb-6 rounded-xl border border-line-200 bg-parchment-100 px-4 py-3 text-sm text-slate-600">{SAFETY_HINT[doc.safety_category]} Kategori ini adalah klasifikasi administratif, bukan sertifikasi keselamatan.</p>}
      <Block title="Deskripsi" text={doc.description} />
      <Block title="Konteks belajar" text={doc.learning_context} />
      <Block title="Prasyarat" text={doc.prerequisites} />
      {doc.phases.length > 0 && (
        <section className="mb-6"><h3 className="mb-3 font-serif text-lg text-forest-900">Fase gerakan</h3>
          <ol className="space-y-3">{doc.phases.map((p, i) => (
            <li key={p.id ?? i} className="rounded-xl border border-line-200 bg-paper-50 p-4">
              <p className="font-medium"><span className="mr-2 text-bronze-700">{i + 1}.</span>{p.name}</p>
              {paragraphs(p.instruction).map((t, j) => <p key={j} className="mt-1 max-w-prose">{t}</p>)}
              {p.body_focus.length > 0 && <p className="mt-2 text-sm text-slate-600">Fokus tubuh: {p.body_focus.join(", ")}</p>}
              {p.safety_note && <p className="mt-1 text-sm text-slate-600"><strong>Keselamatan:</strong> {p.safety_note}</p>}
              {(p.start_ms !== null || p.end_ms !== null) && <p className="mt-1 text-xs text-slate-600">Penanda waktu referensi: {p.start_ms !== null ? formatClock(p.start_ms) : "—"} – {p.end_ms !== null ? formatClock(p.end_ms) : "—"}</p>}
            </li>))}</ol></section>)}
      {doc.common_mistakes.length > 0 && (
        <section className="mb-6"><h3 className="mb-2 font-serif text-lg text-forest-900">Kesalahan umum (menurut instruktur)</h3>
          <ul className="list-disc space-y-1 pl-5">{doc.common_mistakes.map((m, i) => <li key={i}>{m}</li>)}</ul></section>)}
      <Block title="Arahan keselamatan" text={doc.safety_guidance} />
      <Block title="Catatan istilah dan variasi" text={doc.terminology_notes} />
      {doc.relevant_body_parts.length > 0 && <p className="mb-6 text-sm text-slate-600"><strong className="text-ink-950">Bagian tubuh relevan:</strong> {doc.relevant_body_parts.join(", ")}</p>}
      {doc.media.length > 0 && (
        <section className="mb-6"><h3 className="mb-3 font-serif text-lg text-forest-900">Media referensi</h3>
          <ul className="space-y-4">{doc.media.map((m) => (
            <li key={m.id} className="rounded-xl border border-line-200 bg-paper-50 p-4">
              {m.kind === "video"
                ? <video controls preload="metadata" src={m.url} className="mb-2 max-h-[28rem] w-full rounded-lg bg-ink-950" aria-label={m.title} />
                : <RefImage src={m.url} alt={m.title} className="mb-2 max-h-[28rem] rounded-lg" />}
              <p className="font-medium">{m.is_demo ? "[DEMO] " : ""}{m.title}</p>
              <p className="text-xs text-slate-600">Pemegang hak: {m.rights_holder} · Sumber: {m.source_description} · Lingkup izin: {m.usage_scope}</p></li>))}</ul></section>)}
      <footer className="mt-8 border-t border-line-200 pt-4 text-xs text-slate-600">
        {doc.rights_holder && <p>Hak dokumentasi: {doc.rights_holder}{doc.license_type ? ` (${LICENSE_LABEL[doc.license_type]})` : ""}{doc.usage_scope ? ` — ${doc.usage_scope}` : ""}</p>}
        {doc.changelog && <p className="mt-1">Catatan perubahan versi ini: {doc.changelog}</p>}
      </footer>
    </article>
  );
}
