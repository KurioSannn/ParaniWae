import Link from "next/link";
import { notFound } from "next/navigation";
import { Card, EmptyState, ErrorState, Grid, PageHeader, ProvenanceBadge, SourceBox } from "@/components/ui";
import { CourseCard, TraditionCard } from "@/components/Cards";
import { PARTNER_TYPE_LABEL } from "@/lib/format";
import { sGet } from "@/lib/server-api";
import type { PartnerDetail } from "@/lib/types";

export default async function PartnerPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const r = await sGet<PartnerDetail>(`/partners/${encodeURIComponent(slug)}`);
  if (!r.ok) return r.status === 404 ? notFound() : <ErrorState message={r.error} retryHref={`/community/${slug}`} />;
  const p = r.data;
  return (
    <>
      <nav aria-label="Jejak halaman" className="mb-4 text-sm"><Link className="underline" href="/community">Perguruan</Link> / {p.name}</nav>
      <PageHeader eyebrow={PARTNER_TYPE_LABEL[p.partner_type] ?? p.partner_type} title={p.name} description={p.official_description ?? undefined} />
      <div className="grid gap-8 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-10">
          <section aria-labelledby="ins"><h2 id="ins" className="mb-4 font-serif text-2xl text-forest-900">Instruktur</h2>
            {p.instructors.length ? <ul className="space-y-3">{p.instructors.map((i) => (
              <li key={i.id}><Card><h3 className="font-semibold">{i.name}</h3><div className="my-1"><ProvenanceBadge p={i.provenance} /></div>
                {i.bio && <p className="text-sm text-slate-600">{i.bio}</p>}</Card></li>))}</ul>
              : <EmptyState title="Belum ada profil instruktur yang dipublikasikan" />}</section>
          <section aria-labelledby="tra"><h2 id="tra" className="mb-4 font-serif text-2xl text-forest-900">Tradisi</h2>
            {p.traditions.length ? <Grid>{p.traditions.map((t) => <TraditionCard key={t.id} t={t} />)}</Grid> : <EmptyState title="Belum ada tradisi terkait" />}</section>
          <section aria-labelledby="kur"><h2 id="kur" className="mb-4 font-serif text-2xl text-forest-900">Kurikulum</h2>
            {p.courses.length ? <Grid>{p.courses.map((c) => <CourseCard key={c.id} c={c} />)}</Grid> : <EmptyState title="Belum ada kurikulum terbit" />}</section>
        </div>
        <div className="space-y-4">
          <Card className="text-sm text-slate-600">{[p.city, p.region].filter(Boolean).join(", ") || "Lokasi belum dicantumkan."}<br />Kontak resmi dan jadwal kelas belum tersedia.</Card>
          <SourceBox p={p.provenance} />
        </div>
      </div>
    </>
  );
}
