/** Tipe & helper murni direktori nasional (kontrak: docs/NATIONAL_DIRECTORY_CONTRACT.md). */

export type Precision = "exact" | "district" | "regency" | "province";

export interface PlaceSummary {
  slug: string; name: string; category: string; category_label: string;
  organization: { key: string; name: string; short_name: string | null } | null;
  province_code: string; province: string | null; regency_code: string; regency: string | null;
  district: string | null; address: string | null; locality_text: string | null;
  lat: number; lng: number; precision: Precision; precision_label: string;
  is_training_location: boolean | null; is_organization_office: boolean | null;
  website: string | null; has_contact: boolean; has_schedule: boolean; operational_status: string;
  source_types: string[]; source_count: number; attribution: string | null; distance_km?: number;
}

export interface PlaceSource {
  type: string; type_label: string; title: string | null; publisher: string | null; year: number | null;
  url: string | null; license: string | null; attribution: string | null; retrieved_at: string | null; supports: string[];
}

export interface PlaceDetail extends PlaceSummary {
  official_name: string; aliases: string[]; village: string | null; venue_type: string | null;
  contact: { email: string | null; phone: string | null; source: string | null } | null;
  practice_schedule: { day: string; time: string; note?: string }[] | null;
  training_categories: string[]; sports_listed: string[]; facilities: string[]; accessibility: string | null;
  public_access: string; evidence: string[]; data_conflicts: string[]; entity_id: string | null;
  last_verified_at: string | null; record_updated_at: string; sources: PlaceSource[];
  directions_url: string | null; map_search_url: string; same_regency: PlaceSummary[];
}

export interface Cluster { lat: number; lng: number; count: number; bbox: [number, number, number, number]; single: PlaceSummary | null }

export interface PlacesResponse { mode: "clusters" | "points"; total: number; clusters: Cluster[]; items: PlaceSummary[]; truncated?: boolean }

export interface Facets {
  provinces: { code: string; name: string; count: number; bbox: [number, number, number, number] | null }[];
  regencies: { code: string; name: string; province_code: string; count: number; bbox: [number, number, number, number] | null }[];
  categories: { key: string; label: string; count: number }[];
  organizations: { key: string; name: string; short_name: string | null; count: number }[];
  activities: { key: string; label: string }[];
  precisions: { key: string; label: string }[];
}

export interface DirectoryStats {
  total_places: number; training_locations: number; provinces_with_places: number; provinces_total: number;
  regencies_with_places: number; regencies_total: number;
  by_province: { code: string; name: string; count: number }[];
  regencies_multi: { code: string; name: string; count: number }[];
  by_category: { key: string; label: string; count: number }[];
  by_precision: { key: string; label: string; count: number }[];
  by_organization: { key: string; name: string; short_name: string | null; count: number }[];
  featured: (PlaceSummary & { completeness: number })[];
  heritage_areas: number; note: string; attribution: string[];
}

export interface HeritageArea {
  entity_id: string; name: string; category: string; regency_codes: string[];
  points: { lat: number; lng: number; regency_code: string }[]; locality_text: string | null; public_note: string | null;
  sources: { title: string | null; publisher: string | null; year: number | null; url: string | null }[];
}

export interface DirectoryFilters {
  q: string; province: string; regency: string; categories: string[]; organization: string;
  activity: "" | "training" | "office" | "heritage"; has_contact: boolean; open_public: boolean; precision: "" | "exact" | "regency";
}

export const EMPTY_FILTERS: DirectoryFilters = {
  q: "", province: "", regency: "", categories: [], organization: "", activity: "", has_contact: false, open_public: false, precision: "",
};

/** Warna & huruf penanda per kategori (token DESIGN.md). Bentuk + huruf membedakan, bukan warna saja. */
export const CATEGORY_STYLE: Record<string, { color: string; glyph: string; group: string }> = {
  perguruan_center: { color: "#4a0d0d", glyph: "P", group: "Perguruan" },
  perguruan_branch: { color: "#7c1d1d", glyph: "C", group: "Perguruan" },
  padepokan: { color: "#9a3412", glyph: "D", group: "Padepokan" },
  training_center: { color: "#c2410c", glyph: "L", group: "Pusat latihan" },
  ipsi: { color: "#1f0505", glyph: "I", group: "Organisasi IPSI" },
  organization_office: { color: "#475569", glyph: "K", group: "Kantor organisasi" },
  campus_unit: { color: "#3d2a6b", glyph: "U", group: "Kampus/UKM" },
  community: { color: "#a16207", glyph: "S", group: "Sanggar/komunitas" },
  sports_venue: { color: "#0f766e", glyph: "G", group: "Gelanggang" },
  cultural_center: { color: "#b45309", glyph: "B", group: "Budaya & pelestarian" },
  cultural_landmark: { color: "#b45309", glyph: "M", group: "Budaya & pelestarian" },
};

export const styleOf = (cat: string) => CATEGORY_STYLE[cat] ?? { color: "#52605a", glyph: "•", group: "Lainnya" };

/** Query string untuk API (urutan stabil; nilai kosong dibuang). */
export function filtersToQuery(f: DirectoryFilters, extra: Record<string, string | number | undefined> = {}): string {
  const p = new URLSearchParams();
  if (f.q.trim()) p.set("q", f.q.trim());
  if (f.province) p.set("province", f.province);
  if (f.regency) p.set("regency", f.regency);
  if (f.categories.length) p.set("category", [...f.categories].sort().join(","));
  if (f.organization) p.set("organization", f.organization);
  if (f.activity) p.set("activity", f.activity);
  if (f.has_contact) p.set("has_contact", "true");
  if (f.open_public) p.set("open_public", "true");
  if (f.precision) p.set("precision", f.precision);
  for (const [k, v] of Object.entries(extra)) if (v !== undefined && v !== "") p.set(k, String(v));
  return p.toString();
}

/** Filter dari URLSearchParams halaman (param publik berbahasa Indonesia). */
export function filtersFromParams(sp: URLSearchParams): DirectoryFilters {
  const act = sp.get("aktivitas") ?? "";
  const prec = sp.get("presisi") ?? "";
  return {
    q: sp.get("q") ?? "", province: sp.get("provinsi") ?? "", regency: sp.get("kabkota") ?? "",
    categories: (sp.get("jenis") ?? "").split(",").filter(Boolean), organization: sp.get("organisasi") ?? "",
    activity: (["training", "office", "heritage"].includes(act) ? act : "") as DirectoryFilters["activity"],
    has_contact: sp.get("kontak") === "1", open_public: sp.get("umum") === "1",
    precision: (["exact", "regency"].includes(prec) ? prec : "") as DirectoryFilters["precision"],
  };
}

export function filtersToPageParams(f: DirectoryFilters): string {
  const p = new URLSearchParams();
  if (f.q.trim()) p.set("q", f.q.trim());
  if (f.province) p.set("provinsi", f.province);
  if (f.regency) p.set("kabkota", f.regency);
  if (f.categories.length) p.set("jenis", f.categories.join(","));
  if (f.organization) p.set("organisasi", f.organization);
  if (f.activity) p.set("aktivitas", f.activity);
  if (f.has_contact) p.set("kontak", "1");
  if (f.open_public) p.set("umum", "1");
  if (f.precision) p.set("presisi", f.precision);
  return p.toString();
}

export const activeFilterCount = (f: DirectoryFilters) =>
  [f.q.trim(), f.province, f.regency, f.organization, f.activity, f.precision].filter(Boolean).length
  + f.categories.length + (f.has_contact ? 1 : 0) + (f.open_public ? 1 : 0);

/** Kelompokkan tempat berkoordinat identik (penanda wilayah sering berbagi titik ibu kota). */
export function groupByCoordinate<T extends { lat: number; lng: number }>(items: T[]): T[][] {
  const m = new Map<string, T[]>();
  for (const it of items) {
    const k = `${it.lat.toFixed(5)},${it.lng.toFixed(5)}`;
    const g = m.get(k);
    if (g) g.push(it); else m.set(k, [it]);
  }
  return [...m.values()];
}

/** bbox Leaflet → string API minLng,minLat,maxLng,maxLat (dibulatkan agar cache-friendly). */
export function bboxParam(b: { west: number; south: number; east: number; north: number }): string {
  const c = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  return [c(b.west, -180, 180), c(b.south, -90, 90), c(b.east, -180, 180), c(b.north, -90, 90)].map((v) => v.toFixed(3)).join(",");
}

export const INDONESIA_BOUNDS: [[number, number], [number, number]] = [[-11.2, 94.7], [6.3, 141.1]];

/** URL tile peta. OSM standar hanya untuk pemakaian ringan (lihat kebijakan tile OSMF); produksi wajib penyedia sendiri. */
export const TILE_URL = process.env.NEXT_PUBLIC_MAP_TILE_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
export const TILE_ATTRIBUTION = process.env.NEXT_PUBLIC_MAP_TILE_ATTRIBUTION
  || '&copy; <a href="https://www.openstreetmap.org/copyright">kontributor OpenStreetMap</a>';

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));
}

export function shortRegion(name: string | null): string {
  return (name ?? "").replace(/^Kota Administrasi /, "").replace(/^Kabupaten Administrasi /, "Kab. ").replace(/^Kabupaten /, "Kab. ");
}
