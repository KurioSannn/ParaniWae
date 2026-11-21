import Link from "next/link";
import { MapPinned, Send } from "lucide-react";
import { DirectoryExplorer } from "@/components/directory/DirectoryExplorer";
import { Card, ErrorState, PageHeader } from "@/components/ui";
import { apiGet } from "@/lib/api";
import { shortRegion, type DirectoryStats, type Facets } from "@/lib/directory";

export const metadata = {
  title: "Peta Tempat Latihan Pencak Silat",
  description: "Peta nasional perguruan, padepokan, pusat latihan, dan organisasi pencak silat di Indonesia, dengan saringan wilayah, jenis, dan lokasi terdekat.",
  alternates: { canonical: "/community/peta" },
};
export const dynamic = "force-dynamic";

export default async function DirectoryMapPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const sp = await searchParams;
  const [facets, stats] = await Promise.all([apiGet<Facets>("/directory/facets"), apiGet<DirectoryStats>("/directory/stats")]);
  if (!facets.ok || !stats.ok) return <ErrorState message={(!facets.ok ? facets.error : !stats.ok ? stats.error : "")} retryHref="/community/peta" />;
  const s = stats.data;
  const initial = new URLSearchParams(Object.entries(sp).filter(([, v]) => typeof v === "string") as [string, string][]).toString();
  const maxProv = Math.max(1, ...s.by_province.map((p) => p.count));
  return (
    <>
      
      <PageHeader eyebrow="Peta nasional" title="Temukan tempat belajar pencak silat"
        description="Perguruan, padepokan, pusat latihan, dan organisasi pencak silat yang terdata di seluruh Indonesia. Titik yang alamatnya belum diketahui ditampilkan pada tingkat kabupaten/kota, bukan di titik tebakan." />

      <dl className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          [String(s.total_places), "lokasi terdata"],
          [String(s.training_locations), "tempat latihan"],
          [`${s.provinces_with_places}/${s.provinces_total}`, "provinsi tercakup"],
          [`${s.regencies_with_places}/${s.regencies_total}`, "kabupaten/kota tercakup"],
        ].map(([n, l]) => (
          <div key={l} className="rounded-2xl border border-line-200 bg-paper-50 p-4">
            <dt className="text-sm text-slate-600">{l}</dt><dd className="font-serif text-3xl text-forest-900">{n}</dd>
          </div>
        ))}
      </dl>

      <DirectoryExplorer facets={facets.data} initialParams={initial} />

      <section aria-labelledby="jelajah" className="mb-12">
        <h2 id="jelajah" className="mb-1 font-serif text-2xl text-forest-900">Jelajahi menurut wilayah</h2>
        <p className="mb-4 max-w-prose text-sm text-slate-600">{s.note}</p>
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <h3 className="mb-3 font-semibold">Lokasi terdata per provinsi</h3>
            <ul className="space-y-1.5 text-sm">
              {s.by_province.filter((p) => p.count > 0).sort((a, b) => b.count - a.count).map((p) => (
                <li key={p.code} className="grid grid-cols-[10rem_1fr_2rem] items-center gap-2">
                  <Link className="truncate underline-offset-2 hover:underline" href={`/community/peta?provinsi=${p.code}`}>{p.name}</Link>
                  <span aria-hidden className="h-2 rounded-full bg-forest-700" style={{ width: `${(p.count / maxProv) * 100}%` }} />
                  <span className="text-right tabular-nums">{p.count}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-slate-600">
              Belum ada lokasi terdata di {s.by_province.filter((p) => p.count === 0).length} provinsi: {s.by_province.filter((p) => p.count === 0).map((p) => p.name).join(", ")}.
            </p>
          </Card>
          <div className="space-y-6">
            <Card>
              <h3 className="mb-3 font-semibold">Kabupaten/kota dengan beberapa lokasi</h3>
              <ul className="flex flex-wrap gap-2 text-sm">
                {s.regencies_multi.map((r) => (
                  <li key={r.code}><Link className="inline-block rounded-full border border-line-200 px-3 py-1 hover:bg-parchment-100"
                    href={`/community/peta?provinsi=${r.code.slice(0, 2)}&kabkota=${r.code}`}>{shortRegion(r.name)} · {r.count}</Link></li>
                ))}
              </ul>
            </Card>
            <Card>
              <h3 className="mb-3 font-semibold">Menurut jenis tempat</h3>
              <ul className="grid grid-cols-2 gap-1 text-sm">
                {s.by_category.map((c) => <li key={c.key}><Link className="hover:underline" href={`/community/peta?jenis=${c.key}`}>{c.label}</Link> <span className="text-slate-600">({c.count})</span></li>)}
              </ul>
              <h3 className="mb-2 mt-4 font-semibold">Menurut perguruan/organisasi induk</h3>
              <ul className="flex flex-wrap gap-2 text-sm">
                {s.by_organization.map((o) => <li key={o.key}><Link className="inline-block rounded-full border border-line-200 px-3 py-1 hover:bg-parchment-100" href={`/community/peta?organisasi=${o.key}`}>{o.short_name ?? o.name} · {o.count}</Link></li>)}
              </ul>
            </Card>
          </div>
        </div>
      </section>

      <section aria-labelledby="lengkap" className="mb-12">
        <h2 id="lengkap" className="mb-1 font-serif text-2xl text-forest-900">Lokasi dengan informasi paling lengkap</h2>
        <p className="mb-4 text-sm text-slate-600">Diurutkan menurut kelengkapan sumber, alamat, dan ketepatan titik, bukan menurut mutu perguruan.</p>
        <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {s.featured.map((p) => (
            <li key={p.slug}><Card className="h-full">
              <MapPinned aria-hidden className="mb-2 h-5 w-5 text-bronze-700" />
              <Link href={`/community/tempat/${p.slug}`} className="font-medium hover:underline">{p.name}</Link>
              <p className="text-sm text-slate-600">{p.category_label} · {shortRegion(p.regency)}</p>
              <p className="mt-1 text-xs text-slate-600">{p.source_count} sumber: {p.source_types.join(", ")}</p>
            </Card></li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="kirim" className="mb-6">
        <Card className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 id="kirim" className="font-serif text-xl text-forest-900">Mengelola atau mengetahui tempat latihan?</h2>
            <p className="text-sm text-slate-600">Kirim tempat baru, koreksi alamat, jadwal, atau kabar tempat yang sudah tutup. Redaksi memeriksa setiap kiriman sebelum tampil.</p>
          </div>
          <Link href="/community/kirim-tempat" className="inline-flex items-center gap-2 rounded-xl bg-forest-700 px-4 py-2.5 text-sm font-medium text-paper-50 hover:bg-forest-900"><Send aria-hidden className="h-4 w-4" />Kirim informasi</Link>
        </Card>
        <p className="mt-4 text-xs text-slate-600">Data lokasi: {s.attribution.join(" · ")}. Peta dasar: © kontributor OpenStreetMap.</p>
      </section>
    </>
  );
}
