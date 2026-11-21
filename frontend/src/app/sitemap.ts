import type { MetadataRoute } from "next";
import { apiGet } from "@/lib/api";
import type { Curricula, MovementItem, TraditionItem } from "@/lib/research";

export const dynamic = "force-dynamic";
const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

/** Peta situs: hanya halaman pengetahuan publik. Area akun (/app), Studio, dan halaman autentikasi tidak dicantumkan. */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [mv, tr, cur, dir] = await Promise.all([
    apiGet<{ items: MovementItem[] }>("/research/movements"),
    apiGet<TraditionItem[]>("/research/traditions"),
    apiGet<Curricula>("/research/curricula"),
    apiGet<{ items: { slug: string }[] }>("/directory/list?page_size=100"),
  ]);
  const url = (p: string, priority = 0.6) => ({ url: `${SITE}${p}`, changeFrequency: "weekly" as const, priority });
  const out: MetadataRoute.Sitemap = ["/", "/heritage", "/library", "/academy", "/community/peta"].map((p, i) => url(p, i === 0 ? 1 : 0.8));
  if (tr.ok) out.push(...tr.data.map((t) => url(`/heritage/${t.slug}`, 0.7)));
  if (mv.ok) out.push(...mv.data.items.map((m) => url(`/library/${m.slug}`)));
  if (cur.ok) for (const c of cur.data.items) {
    out.push(url(`/academy/courses/${c.slug}`, 0.7));
    for (const m of c.modules) for (const l of m.lessons) out.push(url(`/academy/courses/${c.slug}/lessons/${l.slug}`));
  }
  if (dir.ok) out.push(...dir.data.items.map((p) => url(`/community/tempat/${p.slug}`, 0.5)));
  return out;
}
