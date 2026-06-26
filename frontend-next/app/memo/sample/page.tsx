import { MemoView } from "@/components/memo/MemoView";
import { sampleArtifacts, sampleMemo } from "@/lib/sample-memo";

export default function SampleMemoPage() {
  return <MemoView memo={sampleMemo} artifacts={sampleArtifacts} label="sample" />;
}
