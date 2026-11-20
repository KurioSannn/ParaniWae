import { ForgotPassword } from "@/components/AuthFlows";
import { Card, PageHeader } from "@/components/ui";

export const metadata = { title: "Lupa kata sandi", robots: { index: false } };

export default async function Page() {
  return (
    <div className="mx-auto max-w-md">
      <PageHeader title="Lupa kata sandi" description="Masukkan email akun Anda. Kami akan mengirim tautan atur ulang bila akun tersebut ada." />
      <Card><ForgotPassword /></Card>
    </div>
  );
}
