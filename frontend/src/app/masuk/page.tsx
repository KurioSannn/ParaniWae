import { redirect } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { Card, PageHeader } from "@/components/ui";
import { getCurrentUser } from "@/lib/server-api";
import { safeNext } from "@/lib/validation";

export const metadata = { title: "Masuk" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  if (await getCurrentUser()) redirect(safeNext(next));
  return (
    <div className="mx-auto max-w-md">
      <PageHeader title="Masuk" description="Lanjutkan belajar dan lihat progres Anda." />
      <Card><AuthForm mode="login" next={safeNext(next)} /></Card>
    </div>
  );
}
