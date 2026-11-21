import { BrandLogo } from "@/components/Brand";
import { redirect } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { DemoLogin, type DemoAccount } from "@/components/DemoLogin";
import { Card, PageHeader } from "@/components/ui";
import { getCurrentUser, sGet } from "@/lib/server-api";
import { safeNext } from "@/lib/validation";

export const metadata = { title: "Masuk" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  if (await getCurrentUser()) redirect(safeNext(next));
  // Daftar akun demo diambil di server: 404 di luar pengembangan -> panel tidak dirender sama sekali.
  const demo = await sGet<DemoAccount[]>("/auth/demo-accounts");
  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6"><BrandLogo size={44} /></div>
      <PageHeader title="Masuk" description="Lanjutkan belajar dan lihat progres Anda." />
      <Card><AuthForm mode="login" next={safeNext(next)} /></Card>
      {demo.ok && demo.data.length > 0 && <DemoLogin accounts={demo.data} next={safeNext(next)} />}
    </div>
  );
}
