// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { clientRequest, readCookie } from "@/lib/client-api";

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe("readCookie", () => {
  it("membaca nilai persis (bukan awalan)", () => {
    expect(readCookie("silatara_csrf", "a=1; silatara_csrf=tok%20en; b=2")).toBe("tok en");
    expect(readCookie("csrf", "silatara_csrf=x")).toBeNull();
  });
});

describe("clientRequest", () => {
  it("mutasi menyertakan X-CSRF-Token dan credentials same-origin; GET tidak", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    document.cookie = "silatara_csrf=abc123";
    const f = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", f);
    await clientRequest("POST", "/courses/x/enroll");
    expect(f.mock.calls[0][1].headers["X-CSRF-Token"]).toBe("abc123");
    expect(f.mock.calls[0][1].credentials).toBe("same-origin");
    await clientRequest("GET", "/auth/me");
    expect(f.mock.calls[1][1].headers["X-CSRF-Token"]).toBeUndefined();
    expect(f.mock.calls[0][0]).toBe("/api/v1/courses/x/enroll"); // relatif -> proxy same-origin
  });
  it("tidak menyimpan apa pun di localStorage", async () => {
    const set = vi.fn();
    vi.stubGlobal("localStorage", { setItem: set, getItem: vi.fn() });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200 })));
    await clientRequest("POST", "/auth/login", { email: "a@b.id", password: "rahasia-rahasia" });
    expect(set).not.toHaveBeenCalled();
  });
});
