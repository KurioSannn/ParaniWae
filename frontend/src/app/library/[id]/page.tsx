import Link from "next/link";
import { notFound } from "next/navigation";
import { MovementDocumentView } from "@/components/MovementDocumentView";
import { ErrorState, SourceBox } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { formatDate, LEVEL_LABEL, SAFETY_LABEL } from "@/lib/format";
import type { MovementOut, PublicVersion } from "@/lib/types";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const r = await apiGet<MovementOut>(`/movements/${id}`);
  return { title: r.ok ? `${r.data.name_id} — Pustaka Gerakan SILATARA` : "Gerakan — SILATARA" };
}

export default async function LibraryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [r, v] = await Promise.all([apiGet<MovementOut>(`/movements/${id}`), apiGet<PublicVersion[]>(`/movements/${id}/versions`)]);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/library/${id}`} />;
  const m = r.data;
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
      <div>
        <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/library">Pustaka Gerakan</Link>{m.tradition_slug && <> / <Link className="underline" href={`/heritage/${m.tradition_slug}`}>{m.tradition_name}</Link></>}</nav>
        <h1 className="font-serif text-3xl text-forest-900 sm:text-4xl">{m.name_id}</h1>
        {m.name_local && <p className="mt-1 text-lg text-slate-600">{m.name_local}</p>}
        <p className="mt-2 text-sm text-slate-600">{m.partner_name && <>Perguruan sumber: {m.partner_slug ? <Link className="underline" href={`/community/${m.partner_slug}`}>{m.partner_name}</Link> : m.partner_name}</>}{m.level ? ` · ${LEVEL_LABEL[m.level]}` : ""}{m.safety_category ? ` · ${SAFETY_LABEL[m.safety_category]}` : ""}</p>
        <div className="mt-6">
          {m.document ? <MovementDocumentView doc={m.document} /> : <>
            {m.description && <p className="max-w-prose">{m.description}</p>}
            {m.safety_notes && <p className="mt-3 text-sm text-slate-600"><strong>Keselamatan:</strong> {m.safety_notes}</p>}</>}
        </div>
      </div>
      <aside className="space-y-6">
        <SourceBox p={m.provenance} />
        {v.ok && v.data.length > 0 && (
          <section aria-labelledby="versi" className="rounded-xl border border-line-200 bg-paper-50 p-4 text-sm">
            <h2 id="versi" className="mb-2 font-semibold">Riwayat versi</h2>
            <ol className="space-y-2">{v.data.map((x) => (
              <li key={x.version_no}><span className="font-medium">Versi {x.version_no}</span>{x.is_current && <span className="ml-2 rounded-full bg-forest-700/10 px-2 py-0.5 text-xs">tayang</span>}
                <span className="block text-xs text-slate-600">{formatDate(x.published_at)}{x.status === "archived" ? " · diarsipkan" : ""}</span>
                {x.changelog && <span className="block text-slate-600">{x.changelog}</span>}</li>))}</ol></section>)}
        <p className="text-xs text-slate-600">Penilaian gerakan oleh AI {m.assessment_enabled ? "tersedia" : "belum tersedia"} untuk gerakan ini. Selalu belajar bersama instruktur; SILATARA adalah alat bantu, bukan pengganti guru.</p>
      </aside>
    </div>
  );
}
