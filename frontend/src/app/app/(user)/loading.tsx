import { ListSkeleton } from "@/components/Skeleton";

// Di dalam layout /app (sudah terproteksi), sehingga redirect login tetap berstatus 307.
export default function Loading() {
  return <ListSkeleton />;
}
