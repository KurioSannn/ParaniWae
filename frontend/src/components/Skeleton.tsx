import { BrandMark } from "@/components/Brand";

export function ListSkeleton() {
  return (
    <div role="status" aria-live="polite" className="animate-pulse space-y-4">
      <span className="sr-only">Memuat…</span>
      <BrandMark size={40} className="brand-breathe" />
      <div className="h-8 w-1/2 rounded-lg bg-line-200" />
      <div className="h-4 w-2/3 rounded bg-line-200" />
      <div className="grid gap-4 sm:grid-cols-3">{[0, 1, 2].map((i) => <div key={i} className="h-32 rounded-2xl bg-line-200" />)}</div>
    </div>
  );
}
