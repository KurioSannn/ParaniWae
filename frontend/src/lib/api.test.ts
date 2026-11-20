import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet, parseResponse, qs } from "@/lib/api";

afterEach(() => vi.unstubAllGlobals());

describe("apiGet / parseResponse", () => {
  it("mengembalikan data bila respons ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "ok" }), { status: 200 })));
    expect(await apiGet("/health")).toMatchObject({ ok: true, data: { status: "ok" } });
  });
  it("mengembalikan error jaringan (bukan melempar)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    expect(await apiGet("/health")).toMatchObject({ ok: false, code: "NETWORK_ERROR" });
  });
  it("membaca envelope error API", async () => {
    const body = { error: { code: "INVALID_CREDENTIALS", message: "Email atau kata sandi salah.", request_id: "r1" } };
    const r = await parseResponse(new Response(JSON.stringify(body), { status: 401 }));
    expect(r).toMatchObject({ ok: false, status: 401, code: "INVALID_CREDENTIALS", error: "Email atau kata sandi salah." });
  });
  it("tahan terhadap error non-JSON", async () => {
    const r = await parseResponse(new Response("<html>", { status: 502 }));
    expect(r).toMatchObject({ ok: false, code: "HTTP_502" });
  });
  it("204 -> ok tanpa body", async () => {
    expect(await parseResponse(new Response(null, { status: 204 }))).toMatchObject({ ok: true, status: 204 });
  });
});

describe("qs", () => {
  it("membuang nilai kosong dan meng-encode", () => {
    expect(qs({ q: "a b", page: 2, kosong: "", n: undefined })).toBe("?q=a+b&page=2");
    expect(qs({})).toBe("");
  });
});
