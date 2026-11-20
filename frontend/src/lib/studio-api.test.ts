import { describe, expect, it } from "vitest";
import { describeError } from "@/lib/studio-api";
import { MANAGE_FIELDS } from "@/lib/manage-config";

describe("describeError", () => {
  it("menampilkan daftar yang belum terisi", () => {
    expect(describeError({ error: "Belum lengkap.", details: { missing: ["Nama", "Fase"] } })).toBe("Belum lengkap. Belum terisi: Nama; Fase.");
  });
  it("menampilkan galat validasi per-field", () => {
    expect(describeError({ error: "Tidak valid.", details: [{ field: "level", message: "salah" }] })).toBe("Tidak valid. (level: salah)");
  });
  it("tanpa detail -> pesan apa adanya", () => { expect(describeError({ error: "X" })).toBe("X"); });
});

describe("konfigurasi Kelola Konten setelah Studio", () => {
  it("gerakan tidak lagi dikelola di /manage (hanya di Studio)", () => { expect(Object.keys(MANAGE_FIELDS)).not.toContain("movements"); });
  it("form mitra tidak dapat mengisi status verifikasi atau persetujuan direktori", () => {
    const names = MANAGE_FIELDS.partners.map((f) => f.name);
    expect(names).not.toContain("verification_status");
    expect(names).not.toContain("public_listing_consent");
  });
});
