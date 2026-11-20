"use client";
import { apiBaseUrl, NETWORK_ERROR, parseResponse, type ApiResult } from "@/lib/api";
import { readCookie } from "@/lib/client-api";

/** Unggah multipart (media referensi / dokumen persetujuan). Cookie sesi + CSRF ikut; Content-Type diatur browser. */
export async function clientUpload<T>(path: string, form: FormData): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {};
  const csrf = readCookie("silatara_csrf");
  if (csrf) headers["X-CSRF-Token"] = csrf;
  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1${path}`, { method: "POST", headers, body: form, credentials: "same-origin", cache: "no-store" });
    return await parseResponse<T>(res);
  } catch {
    return NETWORK_ERROR;
  }
}

/** Pesan galat validasi/`INCOMPLETE` menjadi teks yang dapat dibaca. */
export function describeError(r: { error: string; details?: unknown }): string {
  const d = r.details as { missing?: string[] } | Array<{ field: string; message: string }> | undefined;
  if (d && !Array.isArray(d) && d.missing?.length) return `${r.error} Belum terisi: ${d.missing.join("; ")}.`;
  if (Array.isArray(d) && d.length) return `${r.error} (${d.map((x) => `${x.field}: ${x.message}`).join("; ")})`;
  return r.error;
}
