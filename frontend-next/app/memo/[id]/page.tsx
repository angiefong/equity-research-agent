import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { MemoView } from "@/components/memo/MemoView";

export default async function MemoPage({ params }: { params: { id: string } }) {
  try {
    const [memo, artifacts] = await Promise.all([
      api.memo(params.id),
      api.artifacts(params.id),
    ]);
    return <MemoView memo={memo} artifacts={artifacts} />;
  } catch {
    notFound();
  }
}
