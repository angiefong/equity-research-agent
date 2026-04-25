import type { Artifacts, ResearchMemo } from "@/lib/types";
import { Topbar } from "@/components/ui/Topbar";
import { MemoHero } from "@/components/memo/MemoHero";
import { FactsStrip, type Fact } from "@/components/memo/FactsStrip";

function fmtVerdict(memo: ResearchMemo): string {
  const bw = memo.bull_weight ?? 0, br = memo.bear_weight ?? 0;
  if (bw - br > 0.15) return "Strong Bull";
  if (bw - br > 0) return "Cautious Bull";
  if (br - bw > 0.15) return "Strong Bear";
  if (br - bw > 0) return "Cautious Bear";
  return "Neutral";
}

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  const company = [memo.company_name, memo.exchange, memo.sector].filter(Boolean).join(" · ");

  // TODO Task 14 — wire real series + facts from artifacts/evidence; placeholder for now
  const series = Array.from({ length: 12 }, (_, i) => ({ date: `m${i}`, price: 180 + i * 3 }));
  const facts: Fact[] = [
    { label: "Mkt Cap", value: "—" },
    { label: "P/E (Fwd)", value: "—" },
    { label: "EPS (TTM)", value: "—" },
    { label: "Div Yield", value: "—" },
    { label: "52W Range", value: "—" },
    { label: "Volume", value: "—" },
  ];

  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar left="Equity Research Memo" right={`${memo.timestamp} · live`} />
      <MemoHero
        ticker={memo.ticker}
        companyLine={company || memo.ticker}
        price={214.82}
        changeAbs={2.94}
        changePct={1.39}
        verdict={fmtVerdict(memo)}
        high52w={238}
        low52w={164}
        series={series}
      />
      <FactsStrip facts={facts} />
      <pre className="p-4 text-[11px]">{JSON.stringify({ bull: artifacts.bull_points?.length, bear: artifacts.bear_points?.length }, null, 2)}</pre>
    </div>
  );
}
