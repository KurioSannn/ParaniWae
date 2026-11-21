import { BrandLogo } from "@/components/Brand";
import { redirect } from "next/navigation";
import { AuthForm } from "@/components/AuthForm";
import { Card, PageHeader } from "@/components/ui";
import { getCurrentUser } from "@/lib/server-api";

export const metadata = { title: "Daftar" };

export default async function RegisterPage() {
  if (await getCurrentUser()) redirect("/app");
  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6"><BrandLogo size={44} /></div>
      <PageHeader title="Buat akun" description="Akun pelajar gratis. Kamera tidak diminta saat mendaftar." />
      <Card><AuthForm mode="register" /></Card>
    </div>
  );
}
