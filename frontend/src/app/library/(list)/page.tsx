import Link from "next/link";
import { PageHeader } from "@/components/ui";
import { MovementCard } from "@/components/knowledge/Bits";
import { apiGet } from "@/lib/api";
import type { MovementItem, TraditionItem } from "@/lib/research";
import { LEVEL_ID } from "@/lib/research";

export const metadata = {
  title: "Pustaka Gerakan",
  description: "Kenali gerakan pencak silat dari sikap dasar hingga pola langkah: posisi tubuh, urutan fase, panduan latihan, dan peraga 3D.",
  alternates: { canonical: "/library" },
};
type SP = { q?: string; tradisi?: string; kategori?: string; tingkat?: string; animasi?: string };
type KList = { categories: Record<string, string>; items: MovementItem[] };

export default async function LibraryPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const [k, tr] = await Promise.all([
    apiGet<KList>("/research/movements"),
    apiGet<TraditionItem[]>("/research/traditions"),
  ]);
  const q = (sp.q ?? "").trim().toLowerCase();
  const items = (k.ok ? k.data.items : []).filter((m) =>
    (!q || m.name.toLowerCase().includes(q) || m.aliases.some((a) => a.toLowerCase().includes(q)))
    && (!sp.tradisi || m.tradition_slug === sp.tradisi)
    && (!sp.kategori || m.category === sp.kategori)
    && (!sp.tingkat || m.level === sp.tingkat)
    && (sp.animasi !== "1" || m.animation.status === "generated"));
  const categories = k.ok ? k.data.categories : {};
  const groups = Object.entries(categories).map(([key, label]) => ({ key, label, items: items.filter((m) => m.category === key) })).filter((g) => g.items.length);
  const sel = "rounded-xl border border-line-200 bg-paper-50 px-3 py-2.5 text-sm";
  const total = k.ok ? k.data.items.length : 0;

  return (
    <>
      <PageHeader eyebrow="Pustaka Gerakan" title="Kenali setiap gerakan"
        description="Dari sikap tegak dan kuda-kuda hingga sikap pasang dan pola langkah. Setiap gerakan diuraikan fase demi fase: posisi tubuh, arah gerak, hal yang perlu diperhatikan, panduan latihan, dan rujukannya. Sebagian besar dilengkapi animasi yang bisa Anda jeda dan perlambat." />

      <form action="/library" method="get" role="search" aria-label="Cari & saring gerakan" className="mb-8 grid gap-3 rounded-2xl border border-line-200 bg-paper-50 p-4 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1fr_auto]">
        <label className="sr-only" htmlFor="q">Nama gerakan</label>
        <input id="q" name="q" defaultValue={sp.q} placeholder="Cari nama gerakan, mis. kuda-kuda" className={sel} />
        <label className="sr-only" htmlFor="tradisi">Tradisi</label>
        <select id="tradisi" name="tradisi" defaultValue={sp.tradisi ?? ""} className={sel}>
          <option value="">Semua tradisi</option>
          {tr.ok && tr.data.filter((t) => t.movement_count > 0).map((t) => <option key={t.slug} value={t.slug}>{t.name}</option>)}
        </select>
        <label className="sr-only" htmlFor="kategori">Kategori</label>
        <select id="kategori" name="kategori" defaultValue={sp.kategori ?? ""} className={sel}>
          <option value="">Semua kategori</option>
          {Object.entries(categories).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <label className="sr-only" htmlFor="tingkat">Tingkat</label>
        <select id="tingkat" name="tingkat" defaultValue={sp.tingkat ?? ""} className={sel}>
          <option value="">Semua tingkat</option>
          {Object.entries(LEVEL_ID).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <div className="flex items-center gap-3 sm:col-span-2 lg:col-span-1">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="animasi" value="1" defaultChecked={sp.animasi === "1"} />Beranimasi</label>
          <button className="rounded-xl bg-forest-700 px-4 py-2.5 text-sm font-medium text-paper-50 hover:bg-forest-900">Terapkan</button>
        </div>
      </form>

      <p className="mb-6 text-sm text-slate-600" aria-live="polite">
        Menampilkan {items.length} dari {total} gerakan.
        {(sp.q || sp.tradisi || sp.kategori || sp.tingkat || sp.animasi) && <> <Link className="underline" href="/library">Hapus saringan</Link></>}
      </p>

      {groups.map((g) => (
        <section key={g.key} aria-labelledby={`cat-${g.key}`} className="mb-12">
          <h2 id={`cat-${g.key}`} className="mb-4 font-serif text-2xl text-forest-900">{g.label}</h2>
          <ul className="grid grid-cols-2 gap-5 md:grid-cols-3 lg:grid-cols-4">
            {g.items.map((m) => <li key={m.slug}><MovementCard m={m} /></li>)}
          </ul>
        </section>
      ))}

      {items.length === 0 && (
        <p className="rounded-2xl border border-line-200 bg-paper-50 p-6 text-slate-600">Tidak ada gerakan yang cocok dengan saringan ini. <Link className="underline" href="/library">Lihat semua gerakan</Link>.</p>
      )}
    </>
  );
}
