import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { MemoView } from "@/components/memo/MemoView";

export default async function MemoPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams?: { access_code?: string };
}) {
  const accessCode = searchParams?.access_code;
  try {
    const [memo, artifacts] = await Promise.all([
      api.memo(params.id, accessCode),
      api.artifacts(params.id, accessCode),
    ]);
    return <MemoView memo={memo} artifacts={artifacts} />;
  } catch {
    notFound();
  }
}
