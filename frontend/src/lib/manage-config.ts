import { LEVEL_LABEL, PARTNER_TYPE_LABEL } from "@/lib/format";

export type Field = {
  name: string; label: string; help?: string; required?: boolean;
  type: "text" | "textarea" | "select" | "number" | "checkbox" | "ref" | "url";
  options?: { value: string; label: string }[]; ref?: string; labelKey?: string;
};
const opts = (m: Record<string, string>) => Object.entries(m).map(([value, label]) => ({ value, label }));
const source: Field[] = [
  { name: "source_citation", label: "Sumber / atribusi", type: "textarea", help: "Wajib sebelum diajukan review. Siapa/dokumen apa yang menjadi sumber materi ini?" },
  { name: "source_url", label: "Tautan sumber (opsional)", type: "url" },
];

export const MANAGE_FIELDS: Record<string, Field[]> = {
  traditions: [
    { name: "name", label: "Nama tradisi", type: "text", required: true },
    { name: "local_name", label: "Nama lokal", type: "text" },
    { name: "region", label: "Wilayah", type: "text" },
    { name: "public_summary", label: "Ringkasan publik", type: "textarea" },
    { name: "access_scope", label: "Cakupan akses", type: "select", options: [{ value: "restricted", label: "Terbatas" }, { value: "community", label: "Komunitas" }, { value: "public", label: "Publik" }], help: "Hanya cakupan Publik yang dapat diterbitkan." },
    ...source,
  ],
  partners: [
    { name: "name", label: "Nama perguruan/komunitas", type: "text", required: true },
    { name: "partner_type", label: "Jenis", type: "select", required: true, options: opts(PARTNER_TYPE_LABEL) },
    { name: "region", label: "Wilayah", type: "text" }, { name: "city", label: "Kota", type: "text" },
    { name: "official_description", label: "Deskripsi resmi", type: "textarea" },
    ...source,
  ],
  instructors: [
    { name: "name", label: "Nama instruktur (atribusi publik)", type: "text", required: true },
    { name: "partner_id", label: "Perguruan", type: "ref", ref: "partners", labelKey: "name", required: true },
    { name: "bio", label: "Bio (hanya pernyataan terverifikasi)", type: "textarea" },
    { name: "preferred_attribution", label: "Atribusi yang diinginkan", type: "text" },
    { name: "public_profile_consent", label: "Instruktur menyetujui profil publik", type: "checkbox" },
    ...source,
  ],
  courses: [
    { name: "title", label: "Judul kurikulum", type: "text", required: true },
    { name: "tradition_id", label: "Tradisi", type: "ref", ref: "traditions", labelKey: "name", required: true },
    { name: "partner_id", label: "Perguruan", type: "ref", ref: "partners", labelKey: "name", required: true },
    { name: "instructor_id", label: "Instruktur (opsional)", type: "ref", ref: "instructors", labelKey: "name" },
    { name: "level", label: "Tingkat", type: "select", options: opts(LEVEL_LABEL) },
    { name: "estimated_minutes", label: "Perkiraan durasi (menit)", type: "number" },
    { name: "summary", label: "Ringkasan", type: "textarea" },
    { name: "safety_notes", label: "Catatan keselamatan", type: "textarea" },
    ...source,
  ],
  lessons: [
    { name: "title", label: "Judul pelajaran", type: "text", required: true },
    { name: "course_id", label: "Kurikulum", type: "ref", ref: "courses", labelKey: "title", required: true },
    { name: "module_id", label: "Modul", type: "ref", ref: "modules", required: true, help: "Pilih kurikulum dahulu. Buat modul di halaman kurikulum." },
    { name: "movement_id", label: "Gerakan terkait (opsional)", type: "ref", ref: "movements", labelKey: "name_id" },
    { name: "order_index", label: "Urutan dalam modul", type: "number" },
    { name: "estimated_minutes", label: "Perkiraan durasi (menit)", type: "number" },
    { name: "objective", label: "Tujuan", type: "textarea" },
    { name: "body", label: "Isi pelajaran (teks polos; pisahkan paragraf dengan baris kosong)", type: "textarea" },
    { name: "safety_notes", label: "Catatan keselamatan", type: "textarea" },
    ...source,
  ],
};

/** Ubah nilai form -> payload API: string kosong -> null (opsional) / dihilangkan (create). */
export function toPayload(fields: Field[], values: Record<string, unknown>, mode: "create" | "patch"): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const f of fields) {
    let v = values[f.name];
    if (v === undefined) continue;
    if (f.type === "number") v = v === "" || v === null ? null : Number(v);
    if (typeof v === "string") v = v.trim();
    if (v === "" || v === null) {
      if (mode === "patch" && !f.required) out[f.name] = null;
      continue;
    }
    out[f.name] = v;
  }
  return out;
}
