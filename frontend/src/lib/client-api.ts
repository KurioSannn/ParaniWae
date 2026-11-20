"use client";
import { apiBaseUrl, NETWORK_ERROR, parseResponse, type ApiResult } from "@/lib/api";

export function readCookie(name: string, source: string = typeof document !== "undefined" ? document.cookie : ""): string | null {
  for (const part of source.split("; ")) {
    const i = part.indexOf("=");
    if (i > 0 && part.slice(0, i) === name) return decodeURIComponent(part.slice(i + 1));
  }
  return null;
}

/** Request dari browser: cookie sesi (HttpOnly) ikut otomatis; mutasi menyertakan X-CSRF-Token. */
export async function clientRequest<T>(method: string, path: string, body?: unknown, opts: { keepalive?: boolean } = {}): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") {
    const csrf = readCookie("silatara_csrf");
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }
  try {
    const res = await fetch(`${apiBaseUrl()}/api/v1${path}`, {
      method, headers, credentials: "same-origin", cache: "no-store", keepalive: opts.keepalive,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return await parseResponse<T>(res);
  } catch {
    return NETWORK_ERROR;
  }
}
