import Link from "next/link";
import { ArrowRight, MapPin } from "lucide-react";
import { TraditionCard } from "@/components/Cards";
import { Card, Grid, PageHeader } from "@/components/ui";
import { Pill } from "@/components/knowledge/Bits";
import { apiGet, qs } from "@/lib/api";
import { sGet } from "@/lib/server-api";
import type { Coverage, Entity, Inventory, TraditionItem } from "@/lib/research";
import { CATEGORY_ENTITY_LABEL, COVERAGE_LABEL, HERITAGE_CATEGORIES, INSTITUTION_CATEGORIES } from "@/lib/research";
import type { Page, TraditionSummary } from "@/lib/types";

export const metadata = {
  title: "Jelajahi Warisan",
  description: "Jelajahi keberagaman pencak silat Nusantara: tradisi, aliran, sebutan lokal, dan persebarannya di 38 provinsi Indonesia.",
  alternates: { canonical: "/heritage" },
};
type SP = { wilayah?: string; jenis?: string };
type Ents = { items: Entity[] };

export default async function HeritagePage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const [tr, cov, ents, inv, db] = await Promise.all([
    apiGet<TraditionItem[]>("/research/traditions"),
    apiGet<Coverage>("/research/coverage"),
    apiGet<Ents>("/research/entities"),
    apiGet<Inventory>("/research/inventory"),
    sGet<Page<TraditionSummary>>("/traditions?page_size=50"),
  ]);
  const official = db.ok ? db.data.items.filter((t) => t.content_basis !== "source_backed") : [];
  const all = (ents.ok ? ents.data.items : []).filter((e) => e.sources.length > 0); // hanya yang bersumber
  const heritageEnts = all.filter((e) => HERITAGE_CATEGORIES.includes(e.category) && (!sp.jenis || e.category === sp.jenis));
  const provinces = cov.ok ? cov.data.provinces : [];
  const sel = provinces.find((p) => p.name === sp.wilayah);
  const selEnts = sel ? all.filter((e) => e.provinces.includes(sel.name)) : [];
  const regional = inv.ok ? inv.data.groups.filter((g) => g.tradition !== "trd.psdp") : [];
  const documented = provinces.filter((p) => p.status !== "no_documentation_found").length;

  return (
    <>
      <PageHeader eyebrow="Jelajahi Warisan" title="Pencak silat dari Sabang sampai Merauke"
        description="Setiap daerah memiliki cerita, sebutan, dan cara tersendiri dalam mewariskan pencak silat. Telusuri tradisinya, kenali ragam namanya, dan lihat di mana saja pengetahuan itu tercatat." />

      <section aria-labelledby="tradisi" className="mb-14">
        <h2 id="tradisi" className="mb-4 font-serif text-2xl text-forest-900">Tradisi yang dapat Anda pelajari</h2>
        <ul className="grid gap-5 md:grid-cols-2">
          {(tr.ok ? tr.data : []).map((t) => (
            <li key={t.slug}><Link href={`/heritage/${t.slug}`} className="group flex h-full flex-col rounded-3xl border border-line-200 bg-paper-50 p-6 hover:border-forest-700">
              <p className="text-sm font-medium uppercase tracking-widest text-bronze-700">{t.region}</p>
              <h3 className="mt-1 font-serif text-2xl text-forest-900 group-hover:underline">{t.name}</h3>
              <p className="mt-2 line-clamp-4 text-slate-600">{t.public_summary}</p>
              <p className="mt-auto flex flex-wrap gap-2 pt-4">
                {t.movement_count > 0 && <Pill tone="ok">{t.movement_count} gerakan</Pill>}
                {t.course_count > 0 && <Pill>{t.course_count} kursus</Pill>}
                {t.related_entity_count > 0 && <Pill>{t.related_entity_count} catatan terkait</Pill>}
              </p>
            </Link></li>
          ))}
        </ul>
        {official.length > 0 && <div className="mt-6"><Grid>{official.map((t) => <TraditionCard key={t.id} t={t} level={3} />)}</Grid></div>}
      </section>

      <section id="wilayah" aria-labelledby="wilayah-h" className="mb-14 scroll-mt-6">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <h2 id="wilayah-h" className="font-serif text-2xl text-forest-900">Jelajahi per wilayah</h2>
          <p className="text-sm text-slate-600">{documented} dari {provinces.length} provinsi memiliki catatan</p>
        </div>
        <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
          {provinces.map((p) => {
            const on = sel?.name === p.name;
            const dot = p.status === "sources_adequate" ? "bg-forest-700" : p.status === "sources_limited" ? "bg-bronze-500" : "bg-line-200";
            return (
              <li key={p.name}><Link href={`/heritage${qs({ wilayah: p.name, jenis: sp.jenis })}#wilayah`} aria-current={on ? "true" : undefined}
                className={`flex h-full items-start gap-2 rounded-xl border px-3 py-2.5 text-sm ${on ? "border-forest-700 bg-forest-700 text-paper-50" : "border-line-200 bg-paper-50 hover:border-forest-700"}`}>
                <span aria-hidden className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${on ? "bg-paper-50" : dot}`} />
                <span><span className="block font-medium">{p.name}</span><span className={`text-xs ${on ? "text-paper-50/80" : "text-slate-600"}`}>{p.entities.length ? `${p.entities.length} catatan` : COVERAGE_LABEL[p.status]}</span></span>
              </Link></li>
            );
          })}
        </ul>
        <p className="mt-3 flex flex-wrap gap-4 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-forest-700" />{COVERAGE_LABEL.sources_adequate}</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-bronze-500" />{COVERAGE_LABEL.sources_limited}</span>
          <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-line-200" />{COVERAGE_LABEL.no_documentation_found}</span>
        </p>

        {sel && (
          <Card className="mt-6">
            <h3 className="flex items-center gap-2 font-serif text-2xl text-forest-900"><MapPin aria-hidden className="h-5 w-5 text-bronze-700" />{sel.name}</h3>
            {selEnts.length > 0 ? (
              <ul className="mt-4 grid gap-3 md:grid-cols-2">
                {selEnts.map((e) => (
                  <li key={e.id} className="rounded-xl bg-parchment-100 p-3">
                    <p className="font-medium">{e.name}</p>
                    <p className="text-xs text-slate-600">{CATEGORY_ENTITY_LABEL[e.category]}{e.localities?.length ? ` · ${e.localities.join("; ")}` : ""}</p>
                    {e.notes && <p className="mt-1 text-sm text-slate-600">{e.notes}</p>}
                  </li>
                ))}
              </ul>
            ) : <p className="mt-2 text-slate-600">Kami masih menelusuri tradisi pencak silat di provinsi ini. Bila Anda mengenal perguruan atau tradisi setempat, kami ingin mendengarnya.</p>}
            {sel.gap && selEnts.length > 0 && <p className="mt-4 text-sm text-slate-600"><strong className="font-medium text-ink-950">Yang sedang kami dalami:</strong> {sel.gap}</p>}
            {selEnts.some((e) => INSTITUTION_CATEGORIES.includes(e.category)) && <Link className="mt-4 inline-flex items-center gap-1 text-sm underline" href="/community/peta">Perguruan & lembaga di {sel.name}<ArrowRight aria-hidden className="h-3.5 w-3.5" /></Link>}
          </Card>
        )}
      </section>

      <section id="ragam" aria-labelledby="ragam-h" className="mb-14 scroll-mt-6">
        <h2 id="ragam-h" className="mb-2 font-serif text-2xl text-forest-900">Ragam tradisi, aliran, dan sebutan lokal</h2>
        <p className="mb-4 max-w-prose text-slate-600">Pencak silat dikenal dengan banyak nama: silek di Sumatera Barat, maenpo dan ulin di Jawa Barat, maen pukulan di Betawi, kuntau di Kalimantan, langga di Gorontalo, manca&apos; di Sulawesi Selatan. Sebagian telah tercatat sebagai Warisan Budaya Takbenda Indonesia.</p>
        <div className="mb-5 flex flex-wrap gap-2">
          {[["", "Semua"], ...HERITAGE_CATEGORIES.map((c) => [c, CATEGORY_ENTITY_LABEL[c]])].map(([v, l]) => (
            <Link key={v} href={`/heritage${qs({ wilayah: sp.wilayah, jenis: v })}#ragam`} className={`rounded-full border px-3 py-1 text-sm ${(sp.jenis ?? "") === v ? "border-forest-700 bg-forest-700 text-paper-50" : "border-line-200 bg-paper-50 hover:border-forest-700"}`}>{l}</Link>
          ))}
        </div>
        <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {heritageEnts.map((e) => (
            <li key={e.id}><Card className="h-full">
              <p className="text-xs uppercase tracking-wider text-bronze-700">{CATEGORY_ENTITY_LABEL[e.category]}</p>
              <h3 className="mt-1 font-medium">{e.name}</h3>
              {e.aliases && e.aliases.length > 0 && <p className="text-xs text-slate-600">Juga disebut {e.aliases.join(", ")}</p>}
              <p className="mt-2 text-sm">{e.provinces.filter((x) => x !== "needs_verification").join(", ") || "Wilayah belum dipastikan"}{e.localities?.length ? <span className="text-slate-600"> · {e.localities.join("; ")}</span> : null}</p>
              {e.wbtb?.inventory_ref && <p className="mt-1 text-xs text-forest-900">Tercatat dalam inventaris Warisan Budaya Takbenda Indonesia{e.wbtb.recorded ? ` (${e.wbtb.recorded.slice(0, 4)})` : ""}</p>}
              {e.notes && <p className="mt-2 text-sm text-slate-600">{e.notes}</p>}
            </Card></li>
          ))}
        </ul>
      </section>

      {regional.length > 0 && (
        <section aria-labelledby="jurus" className="mb-14">
          <h2 id="jurus" className="mb-2 font-serif text-2xl text-forest-900">Nama jurus dari tradisi daerah</h2>
          <p className="mb-4 max-w-prose text-slate-600">Nama-nama jurus dan langkah yang tercatat dalam sumber. Cara memperagakannya diwariskan langsung oleh guru di setiap perguruan, sehingga di sini kami hanya mencatat namanya.</p>
          <div className="grid gap-4 md:grid-cols-2">
            {regional.map((g) => (
              <Card key={g.label}>
                <h3 className="font-medium">{g.label.replace(/ \(nama saja\)| — nama saja|\(nama dari Wikipedia; sumber primer belum diverifikasi\)/g, "").replace(/ — konsep langkah$/, " — konsep langkah")}</h3>
                <ul className="mt-2 flex flex-wrap gap-1.5">{g.items.filter((i) => i.safety !== "restricted").map((i) => <li key={i.name} className="rounded-full bg-parchment-100 px-2.5 py-1 text-xs">{i.name}</li>)}</ul>
              </Card>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
