import { BrandLogo } from "@/components/Brand";
import { VerifyEmail } from "@/components/AuthFlows";
import { Card, PageHeader } from "@/components/ui";

export const metadata = { title: "Verifikasi email", robots: { index: false } };

export default async function Page({ searchParams }: { searchParams: Promise<{ token?: string }> }) {
  const { token } = await searchParams;
  return (
    <div className="mx-auto max-w-md">
      <div className="mb-6"><BrandLogo size={44} /></div>
      <PageHeader title="Verifikasi email" description="Satu langkah lagi untuk mengaktifkan akun Anda." />
      <Card><VerifyEmail token={token ?? null} /></Card>
    </div>
  );
}
