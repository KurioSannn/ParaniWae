import { describe, expect, it } from "vitest";
import { safeNext, validateLogin, validateRegister } from "@/lib/validation";

describe("validateRegister", () => {
  const ok = { email: "a@b.id", password: "kata-sandi-12345", display_name: "Sari", confirm: "kata-sandi-12345" };
  it("lolos untuk data valid", () => expect(validateRegister(ok)).toEqual({}));
  it("menolak sandi pendek, konfirmasi beda, email/nama tidak valid", () => {
    const e = validateRegister({ email: "x", password: "pendek", display_name: "S", confirm: "lain" });
    expect(Object.keys(e).sort()).toEqual(["confirm", "display_name", "email", "password"]);
  });
});
describe("validateLogin", () => {
  it("wajib email valid dan sandi", () => {
    expect(validateLogin({ email: "", password: "" })).toHaveProperty("email");
    expect(validateLogin({ email: "a@b.id", password: "x" })).toEqual({});
  });
});
describe("safeNext (anti open-redirect)", () => {
  it("mengizinkan kembali ke halaman undangan pilot (path + token), menolak host asing", () => {
    expect(safeNext("/undangan?token=abc123")).toBe("/undangan?token=abc123");
    expect(safeNext("/undangan/../evil")).toBe("/app");
    expect(safeNext("//evil.example/undangan")).toBe("/app");
  });
  it.each([
    ["//evil.com"], ["https://evil.com"], ["/\\evil"], [""], [null], ["javascript:alert(1)"], ["/%2F/evil.com"],
    ["/%5Cevil.com"], ["/app\n/evil"], ["/app\t"], ["/ app"], ["///evil.com"], ["/\\/evil.com"], ["/masuk"],
    ["/api/v1/auth/logout"], ["/app/../../evil"], ["app/progress"], ["/%2e%2e//evil"], ["/%"], ["/" + "a".repeat(600)],
    ["/http://evil.com"], ["/app@evil.com"],
  ])("menolak %j -> fallback /app", (v) => {
    expect(safeNext(v as string | null)).toBe("/app");
  });
  it("menerima path internal yang diizinkan beserta query", () => {
    expect(safeNext("/app/progress?x=1")).toBe("/app/progress?x=1");
    expect(safeNext("/academy/courses/demo-kurikulum-a")).toBe("/academy/courses/demo-kurikulum-a");
    expect(safeNext("/app/courses/a/lessons/b", "/x")).toBe("/app/courses/a/lessons/b");
  });
  it("fallback khusus dihormati", () => expect(safeNext("//x", "/academy")).toBe("/academy"));
  it("path tidak di-allowlist ditolak walau internal", () => {
    expect(safeNext("/masuk")).toBe("/app");
    expect(safeNext("/api/v1/auth/logout")).toBe("/app");
  });
});
