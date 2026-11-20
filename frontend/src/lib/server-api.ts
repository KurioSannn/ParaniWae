import "server-only";
import { cookies } from "next/headers";
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { apiGet, type ApiResult } from "@/lib/api";
import type { AuthPayload, Role, User } from "@/lib/types";
import { safeNext } from "@/lib/validation";

/** GET dari Server Component dengan meneruskan cookie sesi pengguna ke backend. */
export async function sGet<T>(path: string): Promise<ApiResult<T>> {
  const cookie = (await cookies()).toString();
  return apiGet<T>(path, { headers: cookie ? { cookie } : {} });
}

export async function getCurrentUser(): Promise<User | null> {
  const r = await sGet<AuthPayload>("/auth/me");
  return r.ok ? r.data.user : null;
}

/** Proteksi halaman: arahkan ke login bila belum masuk, atau ke /app bila peran tidak cukup. */
export async function requireUser(next: string, roles?: Role[]): Promise<User> {
  const user = await getCurrentUser();
  if (!user) redirect(`/masuk?next=${encodeURIComponent(safeNext(next))}`);
  if (roles && !roles.includes(user.role)) redirect("/app?akses=ditolak");
  return user;
}

/** Path permintaan saat ini (diset proxy.ts untuk /app/*); dipakai layout agar redirect login kembali ke asal. */
export async function currentPath(fallback = "/app"): Promise<string> {
  return safeNext((await headers()).get("x-silatara-path"), fallback);
}
