"use client";
import "leaflet/dist/leaflet.css";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import type * as Leaflet from "leaflet";
import { Crosshair, Layers, List as ListIcon, MapPin, RotateCcw, Search, SlidersHorizontal } from "lucide-react";
import { apiGet } from "@/lib/api";
import {
  activeFilterCount, bboxParam, EMPTY_FILTERS, escapeHtml, filtersFromParams, filtersToPageParams, filtersToQuery,
  groupByCoordinate, INDONESIA_BOUNDS, shortRegion, styleOf, TILE_ATTRIBUTION, TILE_URL,
  type DirectoryFilters, type Facets, type HeritageArea, type PlaceSummary, type PlacesResponse,
} from "@/lib/directory";

type MapState = "loading" | "ready" | "error";
type Near = { lat: number; lng: number } | null;

const sel = "w-full rounded-xl border border-line-200 bg-paper-50 px-3 py-2 text-sm";

function markerHtml(p: PlaceSummary): string {
  const s = styleOf(p.category);
  const area = p.precision !== "exact";
  return `<span class="sil-pin${area ? " sil-pin--area" : " sil-pin--drop"}" style="--pin:${s.color}" aria-hidden="true"><b>${s.glyph}</b></span>`;
}

function popupHtml(items: PlaceSummary[]): string {
  const one = (p: PlaceSummary) => {
    const rows = [
      `<p class="sil-pop__meta">${escapeHtml(p.category_label)}${p.organization ? ` · ${escapeHtml(p.organization.short_name ?? p.organization.name)}` : ""}</p>`,
      `<p class="sil-pop__place">${escapeHtml([p.district, shortRegion(p.regency), p.province].filter(Boolean).join(", "))}</p>`,
      p.address ? `<p>${escapeHtml(p.address)}</p>` : "",
      p.is_training_location ? `<p>Tempat latihan</p>` : "",
      p.website ? `<p><a href="${escapeHtml(p.website)}" target="_blank" rel="noopener noreferrer">Situs web</a></p>` : "",
      `<p class="sil-pop__actions"><a href="/community/tempat/${encodeURIComponent(p.slug)}">Lihat detail</a>${p.precision === "exact"
        ? ` · <a href="https://www.openstreetmap.org/directions?to=${p.lat.toFixed(6)}%2C${p.lng.toFixed(6)}" target="_blank" rel="noopener noreferrer">Arah</a>` : ""}</p>`,
    ];
    return `<div class="sil-pop__item"><h3>${escapeHtml(p.name)}</h3>${rows.join("")}</div>`;
  };
  if (items.length === 1) return `<div class="sil-pop">${one(items[0])}</div>`;
  return `<div class="sil-pop"><p class="sil-pop__group">${items.length} lokasi tercatat di ${escapeHtml(shortRegion(items[0].regency))} (tingkat wilayah)</p>${items.map(one).join("")}</div>`;
}

export function DirectoryExplorer({ facets: initialFacets, initialParams }: { facets: Facets; initialParams: string }) {
  const [filters, setFilters] = useState<DirectoryFilters>(() => filtersFromParams(new URLSearchParams(initialParams)));
  const [draftQ, setDraftQ] = useState(filters.q);
  const [facets, setFacets] = useState<Facets>(initialFacets);
  const [mapState, setMapState] = useState<MapState>("loading");
  const [viewport, setViewport] = useState<{ bbox: string; zoom: number } | null>(null);
  const [mapData, setMapData] = useState<PlacesResponse | null>(null);
  const [list, setList] = useState<{ total: number; items: PlaceSummary[] } | null>(null);
  const [totalAll, setTotalAll] = useState<number | null>(null);
  const [listScope, setListScope] = useState<"viewport" | "all">("viewport");
  const [near, setNear] = useState<Near>(null);
  const [geoMsg, setGeoMsg] = useState<string | null>(null);
  const [showHeritage, setShowHeritage] = useState(false);
  const [heritage, setHeritage] = useState<HeritageArea[] | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const mapEl = useRef<HTMLDivElement>(null);
  const L = useRef<typeof Leaflet | null>(null);
  const map = useRef<Leaflet.Map | null>(null);
  const layer = useRef<Leaflet.LayerGroup | null>(null);
  const heritageLayer = useRef<Leaflet.LayerGroup | null>(null);
  const userLayer = useRef<Leaflet.LayerGroup | null>(null);
  const markers = useRef(new Map<string, Leaflet.Marker>());
  const reqId = useRef(0);

  // ---------- inisialisasi peta (sekali)
  useEffect(() => {
    let disposed = false;
    import("leaflet").then((mod) => {
      if (disposed || !mapEl.current) return;
      const Lf = (mod.default ?? mod) as typeof Leaflet;
      L.current = Lf;
      const m = Lf.map(mapEl.current, { zoomControl: true, minZoom: 4, maxZoom: 18, worldCopyJump: false, keyboard: true })
        .fitBounds(INDONESIA_BOUNDS);
      Lf.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: 19 }).addTo(m);
      layer.current = Lf.layerGroup().addTo(m);
      heritageLayer.current = Lf.layerGroup();
      userLayer.current = Lf.layerGroup().addTo(m);
      const update = () => {
        const b = m.getBounds();
        setViewport({ bbox: bboxParam({ west: b.getWest(), south: b.getSouth(), east: b.getEast(), north: b.getNorth() }), zoom: m.getZoom() });
      };
      let t: ReturnType<typeof setTimeout> | undefined;
      m.on("moveend", () => { clearTimeout(t); t = setTimeout(update, 200); });
      map.current = m;
      update();
      setMapState("ready");
    }).catch(() => { if (!disposed) setMapState("error"); });
    return () => {
      disposed = true;
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // ---------- sinkron URL (tanpa reload)
  useEffect(() => {
    const qs = filtersToPageParams(filters);
    window.history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
  }, [filters]);

  // ---------- data peta (viewport)
  useEffect(() => {
    if (!viewport) return;
    const id = ++reqId.current;
    const extra = { bbox: viewport.bbox, zoom: viewport.zoom, ...(near ? { near: `${near.lat},${near.lng}`, sort: "distance" } : {}) };
    apiGet<PlacesResponse>(`/directory/places?${filtersToQuery(filters, extra)}`).then((r) => {
      if (id !== reqId.current) return;
      if (r.ok) { setMapData(r.data); setFetchError(null); } else setFetchError(r.error);
    });
  }, [viewport, filters, near]);

  // ---------- daftar (sinkron dengan filter; cakupan viewport atau semua)
  useEffect(() => {
    const extra: Record<string, string | number | undefined> = { page_size: 60 };
    if (listScope === "viewport" && viewport) extra.bbox = viewport.bbox;
    if (near) { extra.near = `${near.lat},${near.lng}`; extra.sort = "distance"; }
    let alive = true;
    queueMicrotask(() => { if (alive) setBusy(true); });
    Promise.all([
      apiGet<{ total: number; items: PlaceSummary[] }>(`/directory/list?${filtersToQuery(filters, extra)}`),
      apiGet<{ total: number }>(`/directory/list?${filtersToQuery(filters, { page_size: 1 })}`),
    ]).then(([a, b]) => {
      if (!alive) return;
      setBusy(false);
      if (a.ok) setList(a.data); else setFetchError(a.error);
      if (b.ok) setTotalAll(b.data.total);
    });
    return () => { alive = false; };
  }, [filters, viewport, listScope, near]);

  // ---------- facets kab/kota bila provinsi berubah
  useEffect(() => {
    if (!filters.province) return;
    let alive = true;
    apiGet<Facets>(`/directory/facets?province=${filters.province}`).then((r) => { if (alive && r.ok) setFacets((f) => ({ ...f, regencies: r.data.regencies })); });
    return () => { alive = false; };
  }, [filters.province]);

  // ---------- gambar layer
  useEffect(() => {
    const Lf = L.current, m = map.current, lg = layer.current;
    if (!Lf || !m || !lg || !mapData) return;
    lg.clearLayers();
    markers.current.clear();
    const addPlaces = (g: PlaceSummary[]) => {
      const p = g[0];
      const html = g.length > 1 ? `<span class="sil-pin sil-pin--area sil-pin--group" style="--pin:#315c4d" aria-hidden="true">${g.length}</span>` : markerHtml(p);
      const icon = Lf.divIcon({ className: "", html, iconSize: [30, 30], iconAnchor: [15, 15], popupAnchor: [0, -14] });
      const title = g.length > 1 ? `${g.length} lokasi di ${shortRegion(p.regency)}` : p.name;
      const mk = Lf.marker([p.lat, p.lng], { icon, keyboard: true, title, alt: title, riseOnHover: true })
        .bindPopup(popupHtml(g), { maxWidth: 300, autoPanPadding: [24, 24], className: "sil-popup" })
        .bindTooltip(title, { direction: "top", offset: [0, -14] });
      mk.addTo(lg);
      for (const it of g) markers.current.set(it.slug, mk);
    };
    if (mapData.mode === "clusters") {
      for (const c of mapData.clusters) {
        if (c.single) { addPlaces([c.single]); continue; }
        const size = Math.min(64, 30 + Math.log2(c.count + 1) * 6);
        const icon = Lf.divIcon({ className: "", html: `<span class="sil-cluster" style="width:${size}px;height:${size}px">${c.count}</span>`, iconSize: [size, size] });
        const mk = Lf.marker([c.lat, c.lng], { icon, keyboard: true, title: `${c.count} lokasi — perbesar`, alt: `${c.count} lokasi` });
        mk.on("click", () => {
          const [a, b, cc, d] = c.bbox;
          if (a === cc && b === d) m.setView([b, a], Math.min(m.getZoom() + 3, 14));
          else m.fitBounds([[b, a], [d, cc]], { padding: [40, 40], maxZoom: 14 });
        });
        mk.addTo(lg);
      }
      return;
    }
    for (const g of groupByCoordinate(mapData.items)) addPlaces(g);
  }, [mapData]);

  // ---------- layer area warisan
  useEffect(() => {
    const Lf = L.current, m = map.current, hl = heritageLayer.current;
    if (!Lf || !m || !hl) return;
    if (!showHeritage) { hl.remove(); return; }
    if (!heritage) {
      apiGet<{ items: HeritageArea[] }>("/directory/heritage-areas").then((r) => { if (r.ok) setHeritage(r.data.items); });
      return;
    }
    hl.clearLayers();
    for (const a of heritage) {
      for (const pt of a.points) {
        Lf.circle([pt.lat, pt.lng], { radius: 18000, color: "#b9854f", weight: 1.5, dashArray: "4 4", fillColor: "#b9854f", fillOpacity: 0.12 })
          .bindPopup(`<div class="sil-pop"><div class="sil-pop__item"><h3>${escapeHtml(a.name)}</h3><p class="sil-pop__meta">Area warisan terdokumentasi</p><p>${escapeHtml(a.locality_text ?? "")}</p>${a.public_note ? `<p>${escapeHtml(a.public_note)}</p>` : ""}</div></div>`, { maxWidth: 300, className: "sil-popup" })
          .addTo(hl);
      }
    }
    hl.addTo(m);
  }, [showHeritage, heritage, mapState]);

  const update = useCallback((patch: Partial<DirectoryFilters>) => setFilters((f) => ({ ...f, ...patch })), []);

  const flyToRegion = (code: string, kind: "province" | "regency") => {
    const rec = kind === "province" ? facets.provinces.find((p) => p.code === code) : facets.regencies.find((r) => r.code === code);
    const b = rec?.bbox;
    if (b && map.current) map.current.fitBounds([[b[1], b[0]], [b[3], b[2]]], { padding: [20, 20] });
  };

  const locate = () => {
    if (!("geolocation" in navigator)) { setGeoMsg("Peramban ini tidak mendukung lokasi."); return; }
    setGeoMsg("Meminta izin lokasi…");
    navigator.geolocation.getCurrentPosition((pos) => {
      const n = { lat: Number(pos.coords.latitude.toFixed(4)), lng: Number(pos.coords.longitude.toFixed(4)) };
      setNear(n);
      setGeoMsg("Daftar diurutkan dari yang terdekat. Lokasi Anda tidak dikirim untuk disimpan.");
      setListScope("all");
      const Lf = L.current;
      if (Lf && userLayer.current && map.current) {
        userLayer.current.clearLayers();
        Lf.circleMarker([n.lat, n.lng], { radius: 8, color: "#fcfbf7", weight: 3, fillColor: "#a95743", fillOpacity: 1 }).bindTooltip("Lokasi Anda").addTo(userLayer.current);
        map.current.setView([n.lat, n.lng], 9);
      }
    }, (err) => setGeoMsg(err.code === err.PERMISSION_DENIED ? "Izin lokasi ditolak. Anda tetap dapat mencari berdasarkan wilayah." : "Lokasi tidak dapat ditentukan."),
    { enableHighAccuracy: false, timeout: 10_000, maximumAge: 300_000 });
  };

  const reset = () => {
    setFilters(EMPTY_FILTERS); setDraftQ(""); setNear(null); setGeoMsg(null); userLayer.current?.clearLayers();
    map.current?.fitBounds(INDONESIA_BOUNDS);
  };

  const focusPlace = (p: PlaceSummary) => {
    const m = map.current;
    if (!m) return;
    m.setView([p.lat, p.lng], Math.max(m.getZoom(), p.precision === "exact" ? 15 : 10));
    setTimeout(() => markers.current.get(p.slug)?.openPopup(), 450);
    mapEl.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  const nActive = activeFilterCount(filters);
  const regencies = facets.regencies.filter((r) => r.province_code === filters.province);

  return (
    <section aria-labelledby="peta-judul" className="mb-12">
      <h2 id="peta-judul" className="sr-only">Peta dan daftar lokasi</h2>
      <div className="grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        {/* ---------- filter ---------- */}
        <details open className="group rounded-2xl border border-line-200 bg-paper-50 p-4 lg:row-span-2 lg:self-start [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer items-center justify-between font-medium lg:cursor-default">
            <span className="flex items-center gap-2"><SlidersHorizontal aria-hidden className="h-4 w-4" />Saring lokasi{nActive > 0 && <span className="rounded-full bg-forest-700 px-2 text-xs text-paper-50">{nActive}</span>}</span>
          </summary>
          <form className="mt-3 space-y-3" role="search" aria-label="Cari lokasi pencak silat"
            onSubmit={(e) => { e.preventDefault(); update({ q: draftQ }); }}>
            <div>
              <label htmlFor="dir-q" className="mb-1 block text-sm font-medium">Nama, perguruan, atau wilayah</label>
              <div className="flex gap-2">
                <input id="dir-q" value={draftQ} onChange={(e) => setDraftQ(e.target.value)} placeholder="mis. PSHT, Madiun" className={sel} />
                <button className="rounded-xl bg-forest-700 px-3 text-paper-50 hover:bg-forest-900" aria-label="Cari"><Search aria-hidden className="h-4 w-4" /></button>
              </div>
            </div>
            <div>
              <label htmlFor="dir-prov" className="mb-1 block text-sm font-medium">Provinsi</label>
              <select id="dir-prov" className={sel} value={filters.province}
                onChange={(e) => { update({ province: e.target.value, regency: "" }); if (e.target.value) flyToRegion(e.target.value, "province"); }}>
                <option value="">Semua provinsi</option>
                {facets.provinces.map((p) => <option key={p.code} value={p.code}>{p.name} ({p.count})</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="dir-reg" className="mb-1 block text-sm font-medium">Kabupaten/kota</label>
              <select id="dir-reg" className={sel} value={filters.regency} disabled={!filters.province}
                onChange={(e) => { update({ regency: e.target.value }); if (e.target.value) flyToRegion(e.target.value, "regency"); }}>
                <option value="">{filters.province ? "Semua kabupaten/kota" : "Pilih provinsi dahulu"}</option>
                {regencies.map((r) => <option key={r.code} value={r.code}>{r.name}{r.count ? ` (${r.count})` : ""}</option>)}
              </select>
            </div>
            <fieldset>
              <legend className="mb-1 text-sm font-medium">Jenis tempat</legend>
              <div className="grid grid-cols-1 gap-1">
                {facets.categories.map((c) => {
                  const st = styleOf(c.key);
                  const on = filters.categories.includes(c.key);
                  return (
                    <label key={c.key} className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={on} onChange={() => update({ categories: on ? filters.categories.filter((x) => x !== c.key) : [...filters.categories, c.key] })} />
                      <span aria-hidden className="sil-pin sil-pin--sm" style={{ "--pin": st.color } as React.CSSProperties}>{st.glyph}</span>
                      {c.label} <span className="text-slate-600">({c.count})</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
            <div>
              <label htmlFor="dir-org" className="mb-1 block text-sm font-medium">Perguruan/organisasi induk</label>
              <select id="dir-org" className={sel} value={filters.organization} onChange={(e) => update({ organization: e.target.value })}>
                <option value="">Semua</option>
                {facets.organizations.map((o) => <option key={o.key} value={o.key}>{o.short_name ?? o.name} ({o.count})</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="dir-act" className="mb-1 block text-sm font-medium">Aktivitas</label>
              <select id="dir-act" className={sel} value={filters.activity} onChange={(e) => update({ activity: e.target.value as DirectoryFilters["activity"] })}>
                <option value="">Semua</option>
                {facets.activities.map((a) => <option key={a.key} value={a.key}>{a.label}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="dir-prec" className="mb-1 block text-sm font-medium">Ketepatan lokasi</label>
              <select id="dir-prec" className={sel} value={filters.precision} onChange={(e) => update({ precision: e.target.value as DirectoryFilters["precision"] })}>
                <option value="">Semua</option>
                <option value="exact">Titik tempat</option>
                <option value="regency">Tingkat kabupaten/kota</option>
              </select>
            </div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={filters.has_contact} onChange={(e) => update({ has_contact: e.target.checked })} />Punya kontak/situs bersumber</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={filters.open_public} onChange={(e) => update({ open_public: e.target.checked })} />Terbuka untuk umum (menurut sumber)</label>
            <button type="button" onClick={reset} className="inline-flex items-center gap-2 rounded-xl border border-line-200 px-3 py-2 text-sm hover:bg-parchment-100">
              <RotateCcw aria-hidden className="h-4 w-4" />Atur ulang
            </button>
          </form>
        </details>

        {/* ---------- peta ---------- */}
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
            <button type="button" onClick={locate} className="inline-flex items-center gap-2 rounded-xl border border-line-200 bg-paper-50 px-3 py-2 hover:bg-parchment-100">
              <Crosshair aria-hidden className="h-4 w-4" />Lokasi terdekat
            </button>
            <label className="inline-flex items-center gap-2 rounded-xl border border-line-200 bg-paper-50 px-3 py-2">
              <input type="checkbox" checked={showHeritage} onChange={(e) => setShowHeritage(e.target.checked)} />
              <Layers aria-hidden className="h-4 w-4" />Area warisan terdokumentasi
            </label>
            <p aria-live="polite" className="text-slate-600">
              {mapData ? <>{mapData.total} lokasi di area peta{totalAll !== null && ` · ${totalAll} sesuai saringan`}</> : "Memuat lokasi…"}
            </p>
          </div>
          {geoMsg && <p role="status" className="mb-2 text-sm text-slate-600">{geoMsg}</p>}
          <div className="relative overflow-hidden rounded-2xl border border-line-200 bg-parchment-100">
            <div ref={mapEl} className="h-[58vh] min-h-[360px] w-full" role="region" aria-label="Peta lokasi pencak silat di Indonesia" />
            {mapState === "loading" && <div className="absolute inset-0 grid place-items-center text-sm text-slate-600">Memuat peta…</div>}
            {mapState === "error" && (
              <div role="alert" className="absolute inset-0 grid place-items-center bg-paper-50 p-6 text-center text-sm">
                Peta tidak dapat dimuat. Daftar lokasi di bawah tetap dapat digunakan.
              </div>
            )}
          </div>
          <Legend />
          {fetchError && <p role="alert" className="mt-2 text-sm text-clay-600">Gagal memuat data: {fetchError}</p>}
        </div>

        {/* ---------- daftar ---------- */}
        <div className="lg:col-start-2">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h3 className="flex items-center gap-2 font-serif text-xl text-forest-900"><ListIcon aria-hidden className="h-5 w-5" />Daftar lokasi</h3>
            <div role="radiogroup" aria-label="Cakupan daftar" className="flex rounded-xl border border-line-200 bg-paper-50 p-1 text-sm">
              {(["viewport", "all"] as const).map((s) => (
                <button key={s} role="radio" aria-checked={listScope === s} onClick={() => setListScope(s)}
                  className={`rounded-lg px-3 py-1 ${listScope === s ? "bg-forest-700 text-paper-50" : ""}`}>
                  {s === "viewport" ? "Di area peta" : "Semua hasil"}
                </button>
              ))}
            </div>
          </div>
          {!list ? <p className="text-sm text-slate-600">Memuat daftar…</p>
            : list.total === 0 ? (
              <div className="rounded-2xl border border-dashed border-line-200 bg-paper-50 p-6 text-sm">
                <p className="font-medium">Belum ada lokasi yang terdata untuk saringan ini.</p>
                <p className="mt-1 text-slate-600">Direktori ini masih bertumbuh. Jika Anda mengetahui tempat latihan di wilayah ini, <Link className="underline" href="/community/kirim-tempat">kirimkan informasinya</Link>.</p>
              </div>
            ) : (
              <ul className={`grid gap-2 md:grid-cols-2 ${busy ? "opacity-70" : ""}`} aria-busy={busy}>
                {list.items.map((p) => {
                  const st = styleOf(p.category);
                  return (
                    <li key={p.slug} className="rounded-xl border border-line-200 bg-paper-50 p-3">
                      <div className="flex items-start gap-3">
                        <span aria-hidden className={`sil-pin sil-pin--sm ${p.precision !== "exact" ? "sil-pin--area" : ""}`} style={{ "--pin": st.color } as React.CSSProperties}>{st.glyph}</span>
                        <div className="min-w-0 flex-1">
                          <Link href={`/community/tempat/${p.slug}`} className="font-medium underline-offset-2 hover:underline">{p.name}</Link>
                          <p className="text-xs text-slate-600">{p.category_label}{p.organization ? ` · ${p.organization.short_name ?? p.organization.name}` : ""}</p>
                          <p className="text-xs text-slate-600">{[shortRegion(p.regency), p.province].filter(Boolean).join(", ")}{p.distance_km !== undefined && ` · ±${p.distance_km} km`}</p>
                          {p.precision !== "exact" && <p className="text-xs text-bronze-700">{p.precision_label}</p>}
                        </div>
                        <button type="button" onClick={() => focusPlace(p)} className="rounded-lg p-2 hover:bg-parchment-100" aria-label={`Tampilkan ${p.name} di peta`}>
                          <MapPin aria-hidden className="h-4 w-4" />
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          {list && list.total > list.items.length && <p className="mt-2 text-sm text-slate-600">Menampilkan {list.items.length} dari {list.total}. Perbesar peta atau persempit saringan untuk melihat lainnya.</p>}
        </div>
      </div>
    </section>
  );
}

function Legend() {
  const groups = new Map<string, { color: string; glyph: string }>();
  for (const k of ["perguruan_center", "perguruan_branch", "padepokan", "training_center", "ipsi", "organization_office", "campus_unit", "community", "sports_venue", "cultural_center"]) {
    const s = styleOf(k);
    if (!groups.has(s.group)) groups.set(s.group, s);
  }
  return (
    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600" aria-label="Keterangan penanda">
      {[...groups.entries()].map(([g, s]) => (
        <span key={g} className="inline-flex items-center gap-1"><span aria-hidden className="sil-pin sil-pin--sm" style={{ "--pin": s.color } as React.CSSProperties}>{s.glyph}</span>{g}</span>
      ))}
      <span className="inline-flex items-center gap-1"><span aria-hidden className="sil-pin sil-pin--sm sil-pin--area" style={{ "--pin": "#52605a" } as React.CSSProperties}>•</span>Tingkat wilayah (alamat belum terdata)</span>
    </div>
  );
}
