"use client";
import Link from "next/link";
import { useState } from "react";
import { apiGet } from "@/lib/api";
import { clientRequest } from "@/lib/client-api";
import type { Facets } from "@/lib/directory";

type Kind = "new_place" | "correction" | "contact_update" | "schedule_update" | "closed_report";
const KIND_LABEL: Record<Kind, string> = {
  new_place: "Tempat baru", correction: "Koreksi nama/alamat", contact_update: "Perbarui kontak/situs",
  schedule_update: "Perbarui jadwal latihan", closed_report: "Laporkan tempat sudah tutup",
};
const inp = "w-full rounded-xl border border-line-200 bg-paper-50 px-3 py-2 text-sm";

export function SubmissionForm({ facets, place }: { facets: Facets; place: { slug: string; name: string } | null }) {
  const [kind, setKind] = useState<Kind>(place ? "correction" : "new_place");
  const [province, setProvince] = useState("");
  const [regencies, setRegencies] = useState<Facets["regencies"]>([]);
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [msg, setMsg] = useState<string | null>(null);

  const onProvince = async (code: string) => {
    setProvince(code);
    setRegencies([]);
    if (!code) return;
    const r = await apiGet<Facets>(`/directory/facets?province=${code}`);
    if (r.ok) setRegencies(r.data.regencies.filter((x) => x.province_code === code));
  };

  const submit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const s = (k: string) => { const v = String(fd.get(k) ?? "").trim(); return v || undefined; };
    const num = (k: string) => { const v = s(k); return v === undefined ? undefined : Number(v.replace(",", ".")); };
    const schedule = s("schedule")?.split("\n").map((l) => l.trim()).filter(Boolean).slice(0, 14).map((l) => {
      const [day, ...rest] = l.split(/\s+/);
      return { day: day.slice(0, 20), time: rest.join(" ").slice(0, 40) || "-" };
    });
    const payload = Object.fromEntries(Object.entries({
      name: s("name"), category: s("category"), regency_code: s("regency_code"), district: s("district"), address: s("address"),
      lat: num("lat"), lng: num("lng"), website: s("website"), contact_email: s("org_email"), contact_phone: s("org_phone"),
      is_training_location: fd.get("training") === "on" ? true : undefined, schedule, note: s("note"),
    }).filter(([, v]) => v !== undefined && !(Array.isArray(v) && !v.length)));
    setState("sending"); setMsg(null);
    const r = await clientRequest<{ message: string }>("POST", "/directory/submissions", {
      kind, place_slug: place?.slug, payload, source_url: s("source_url"), submitter_relation: s("relation") ?? "publik",
      contact_email: s("my_email"), website_hp: s("website_hp"),
    });
    if (r.ok) { setState("done"); setMsg(r.data.message); } else { setState("error"); setMsg(r.error); }
  };

  if (state === "done") {
    return (
      <div role="status" className="rounded-2xl border border-line-200 bg-paper-50 p-6">
        <p className="font-medium">{msg}</p>
        <p className="mt-2 text-sm text-slate-600">Kiriman tidak langsung tampil. Redaksi memeriksa kemungkinan duplikasi, sumber, dan koordinat terlebih dahulu.</p>
        <Link className="mt-4 inline-block underline" href="/community/peta">Kembali ke peta</Link>
      </div>
    );
  }
  const needsPlaceFields = kind === "new_place" || kind === "correction";
  return (
    <form onSubmit={submit} className="space-y-5 rounded-2xl border border-line-200 bg-paper-50 p-5" noValidate={false}>
      {place && <p className="text-sm">Tempat: <strong>{place.name}</strong></p>}
      <fieldset>
        <legend className="mb-2 text-sm font-medium">Jenis kiriman</legend>
        <div className="grid gap-1 sm:grid-cols-2">
          {(Object.keys(KIND_LABEL) as Kind[]).filter((k) => (place ? k !== "new_place" : k === "new_place")).map((k) => (
            <label key={k} className="flex items-center gap-2 text-sm"><input type="radio" name="kind" checked={kind === k} onChange={() => setKind(k)} />{KIND_LABEL[k]}</label>
          ))}
        </div>
        {!place && <p className="mt-1 text-xs text-slate-600">Untuk mengoreksi tempat yang sudah ada, buka halaman tempat tersebut lalu pilih “Kirim koreksi”.</p>}
      </fieldset>

      {needsPlaceFields && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2"><label htmlFor="name" className="mb-1 block text-sm font-medium">Nama tempat{kind === "new_place" && " *"}</label>
            <input id="name" name="name" required={kind === "new_place"} minLength={3} maxLength={200} className={inp} /></div>
          {kind === "new_place" && <>
            <div><label htmlFor="category" className="mb-1 block text-sm font-medium">Jenis tempat</label>
              <select id="category" name="category" className={inp}><option value="">Pilih</option>
                {[["perguruan_branch", "Cabang/ranting perguruan"], ["padepokan", "Padepokan"], ["training_center", "Pusat latihan"], ["campus_unit", "Kampus/UKM"],
                  ["community", "Sanggar/komunitas"], ["ipsi", "Organisasi IPSI"], ["organization_office", "Kantor organisasi"]].map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </select></div>
            <div><label htmlFor="prov" className="mb-1 block text-sm font-medium">Provinsi *</label>
              <select id="prov" required value={province} onChange={(e) => void onProvince(e.target.value)} className={inp}><option value="">Pilih</option>
                {facets.provinces.map((p) => <option key={p.code} value={p.code}>{p.name}</option>)}</select></div>
            <div><label htmlFor="regency_code" className="mb-1 block text-sm font-medium">Kabupaten/kota *</label>
              <select id="regency_code" name="regency_code" required disabled={!province} className={inp}><option value="">Pilih</option>
                {regencies.map((r) => <option key={r.code} value={r.code}>{r.name}</option>)}</select></div>
          </>}
          <div><label htmlFor="district" className="mb-1 block text-sm font-medium">Kecamatan</label><input id="district" name="district" maxLength={120} className={inp} /></div>
          <div className="sm:col-span-2"><label htmlFor="address" className="mb-1 block text-sm font-medium">Alamat</label><input id="address" name="address" maxLength={400} className={inp} /></div>
          {kind === "new_place" && <>
            <div><label htmlFor="lat" className="mb-1 block text-sm font-medium">Garis lintang (opsional)</label><input id="lat" name="lat" inputMode="decimal" placeholder="-7.6298" className={inp} /></div>
            <div><label htmlFor="lng" className="mb-1 block text-sm font-medium">Garis bujur (opsional)</label><input id="lng" name="lng" inputMode="decimal" placeholder="111.5239" className={inp} /></div>
            <p className="text-xs text-slate-600 sm:col-span-2">Isi koordinat hanya bila Anda berada di tempat itu atau menyalinnya dari peta. Tanpa koordinat, tempat ditampilkan pada tingkat kabupaten/kota.</p>
            <label className="flex items-center gap-2 text-sm sm:col-span-2"><input type="checkbox" name="training" />Tempat ini dipakai untuk latihan</label>
          </>}
        </div>
      )}

      {(kind === "contact_update" || kind === "new_place") && (
        <div className="grid gap-4 sm:grid-cols-3">
          <div><label htmlFor="website" className="mb-1 block text-sm font-medium">Situs resmi</label><input id="website" name="website" type="url" placeholder="https://" className={inp} /></div>
          <div><label htmlFor="org_email" className="mb-1 block text-sm font-medium">Surel organisasi</label><input id="org_email" name="org_email" type="email" className={inp} /></div>
          <div><label htmlFor="org_phone" className="mb-1 block text-sm font-medium">Telepon organisasi</label><input id="org_phone" name="org_phone" inputMode="tel" className={inp} /></div>
          <p className="text-xs text-slate-600 sm:col-span-3">Hanya kontak resmi organisasi yang boleh ditampilkan, bukan nomor pribadi tanpa izin pemiliknya.</p>
        </div>
      )}

      {kind === "schedule_update" && (
        <div><label htmlFor="schedule" className="mb-1 block text-sm font-medium">Jadwal latihan (satu baris per hari)</label>
          <textarea id="schedule" name="schedule" rows={4} placeholder={"Selasa 19.00–21.00\nJumat 19.00–21.00"} className={inp} /></div>
      )}

      <div><label htmlFor="note" className="mb-1 block text-sm font-medium">Keterangan</label>
        <textarea id="note" name="note" rows={3} maxLength={1000} className={inp} placeholder={kind === "closed_report" ? "Sejak kapan tempat ini tidak lagi dipakai? Dari mana Anda mengetahuinya?" : ""} /></div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div><label htmlFor="source_url" className="mb-1 block text-sm font-medium">Tautan sumber</label>
          <input id="source_url" name="source_url" type="url" placeholder="Situs resmi, laman organisasi, atau berita" className={inp} /></div>
        <div><label htmlFor="relation" className="mb-1 block text-sm font-medium">Hubungan Anda dengan tempat ini</label>
          <select id="relation" name="relation" className={inp} defaultValue="publik"><option value="pengelola">Pengelola/pengurus</option><option value="anggota">Anggota/peserta latihan</option><option value="publik">Masyarakat umum</option></select></div>
        <div className="sm:col-span-2"><label htmlFor="my_email" className="mb-1 block text-sm font-medium">Surel Anda (opsional, untuk konfirmasi redaksi)</label>
          <input id="my_email" name="my_email" type="email" className={inp} />
          <p className="mt-1 text-xs text-slate-600">Surel ini tidak ditampilkan di situs.</p></div>
      </div>
      <div aria-hidden className="hidden"><label>Jangan diisi<input name="website_hp" tabIndex={-1} autoComplete="off" /></label></div>
      {state === "error" && <p role="alert" className="text-sm text-clay-600">{msg}</p>}
      <button disabled={state === "sending"} className="rounded-xl bg-forest-700 px-5 py-2.5 text-sm font-medium text-paper-50 hover:bg-forest-900 disabled:opacity-60">
        {state === "sending" ? "Mengirim…" : "Kirim untuk ditinjau"}
      </button>
    </form>
  );
}
