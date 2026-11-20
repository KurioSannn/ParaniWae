import { describe, expect, it } from "vitest";
import { MANAGE_FIELDS, toPayload } from "@/lib/manage-config";

describe("toPayload", () => {
  const f = MANAGE_FIELDS.courses;
  it("create: membuang kosong, mengubah angka, memangkas spasi", () => {
    const p = toPayload(f, { title: "  Judul ", summary: "", estimated_minutes: "30", level: "beginner" }, "create");
    expect(p).toEqual({ title: "Judul", estimated_minutes: 30, level: "beginner" });
  });
  it("patch: field opsional yang dikosongkan menjadi null, wajib tidak", () => {
    const p = toPayload(f, { title: "", summary: "", estimated_minutes: "" }, "patch");
    expect(p).toEqual({ summary: null, estimated_minutes: null });
  });
  it("tidak pernah memuat field sensitif (status, is_demo, approved_by)", () => {
    for (const fields of Object.values(MANAGE_FIELDS)) {
      const names = fields.map((x) => x.name);
      for (const bad of ["status", "is_demo", "approved_by_user_id", "created_by_user_id", "assessment_enabled"]) expect(names).not.toContain(bad);
    }
  });
});
