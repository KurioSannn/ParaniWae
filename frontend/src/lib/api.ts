/**
 * Klien API dasar (aman dipakai di server maupun browser).
 * - Server (SSR, dalam jaringan Docker): INTERNAL_API_URL, mis. http://backend:8000
 * - Browser: NEXT_PUBLIC_API_URL; bila kosong -> relatif ("/api/v1/..."), diproksikan Next ke backend
 *   sehingga cookie sesi first-party.
 */
import type { ApiErrorBody } from "@/lib/types";

export function apiBaseUrl(): string {
  if (typeof window === "undefined") return process.env.INTERNAL_API_URL ?? "http://backend:8000";
  return process.env.NEXT_PUBLIC_API_URL ?? "";
}

export type ApiResult<T> =
  | { ok: true; data: T; status: number }
  | { ok: false; error: string; code: string; status: number; details?: unknown };

export async function parseResponse<T>(res: Response): Promise<ApiResult<T>> {
  if (res.ok) {
    if (res.status === 204) return { ok: true, data: undefined as T, status: 204 };
    return { ok: true, data: (await res.json()) as T, status: res.status };
  }
  let body: { error?: ApiErrorBody } | null = null;
  try {
    body = await res.json();
  } catch {
    /* bukan JSON */
  }
  return {
    ok: false, status: res.status,
    code: body?.error?.code ?? `HTTP_${res.status}`,
    error: body?.error?.message ?? `Permintaan gagal (HTTP ${res.status}).`,
    details: body?.error?.details,
  };
}

export const NETWORK_ERROR = {
  ok: false as const, status: 0, code: "NETWORK_ERROR",
  error: "Tidak dapat terhubung ke server. Periksa koneksi lalu coba lagi.",
};

export async function apiGet<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  try {
    return await parseResponse<T>(await fetch(`${apiBaseUrl()}/api/v1${path}`, { cache: "no-store", ...init }));
  } catch {
    return NETWORK_ERROR;
  }
}

export function qs(params: Record<string, string | number | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  const s = sp.toString();
  return s ? `?${s}` : "";
}
