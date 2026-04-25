import type { Artifacts, ResearchMemo } from "@/lib/types";

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <pre className="p-4 text-[11px]">{JSON.stringify({ ticker: memo.ticker, bull: artifacts.bull_points?.length, bear: artifacts.bear_points?.length }, null, 2)}</pre>
    </div>
  );
}
