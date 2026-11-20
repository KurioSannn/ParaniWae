import { BenchmarkRunner } from "@/components/BenchmarkRunner";
import { PageHeader } from "@/components/ui";
import { requireUser } from "@/lib/server-api";

export const metadata = { title: "Benchmark kamera", robots: { index: false } };

export default async function BenchmarkPage() {
  await requireUser("/app/practice/benchmark");
  return (
    <>
      <PageHeader eyebrow="Pengujian teknis" title="Benchmark mesin landmark"
        description="Membandingkan implementasi lama (main thread) dan Web Worker pada perangkat Anda. Mengukur kinerja jalur komputasi, bukan akurasi dan bukan penilaian gerakan." />
      <BenchmarkRunner />
    </>
  );
}
