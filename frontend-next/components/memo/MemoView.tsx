import type { Artifacts, ResearchMemo } from "@/lib/types";
import { Topbar } from "@/components/ui/Topbar";
import { MemoHero } from "@/components/memo/MemoHero";
import { FactsStrip, type Fact } from "@/components/memo/FactsStrip";
import { Synthesis } from "@/components/memo/Synthesis";
import { ClaimGrid } from "@/components/memo/ClaimGrid";
import { AlertStrip } from "@/components/memo/AlertStrip";
import { WeightBar } from "@/components/viz/WeightBar";
import { ThesisMatrix, type MatrixClaim } from "@/components/viz/ThesisMatrix";

function fmtVerdict(memo: ResearchMemo): string {
  const bw = memo.bull_weight ?? 0, br = memo.bear_weight ?? 0;
  if (bw - br > 0.15) return "Strong Bull";
  if (bw - br > 0) return "Cautious Bull";
  if (br - bw > 0.15) return "Strong Bear";
  if (br - bw > 0) return "Cautious Bear";
  return "Neutral";
}

function paragraphsOf(synth: string): string[] {
  return synth.split(/\n{2,}/).map(s => s.trim()).filter(Boolean);
}

function matrixClaimsOf(arts: Artifacts): MatrixClaim[] {
  const bulls: MatrixClaim[] = (arts.bull_points ?? []).map(p => ({
    side: "bull", topic: p.claim.slice(0, 24), confidence: p.confidence,
  }));
  const bears: MatrixClaim[] = (arts.bear_points ?? []).map(p => ({
    side: "bear", topic: p.claim.slice(0, 24), confidence: p.confidence,
  }));
  return [...bulls, ...bears];
}

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  const company = [memo.company_name, memo.exchange, memo.sector].filter(Boolean).join(" · ");
  const series = Array.from({ length: 12 }, (_, i) => ({ date: `m${i}`, price: 180 + i * 3 }));
  const facts: Fact[] = [
    { label: "Mkt Cap", value: "—" }, { label: "P/E (Fwd)", value: "—" },
    { label: "EPS (TTM)", value: "—" }, { label: "Div Yield", value: "—" },
    { label: "52W Range", value: "—" }, { label: "Volume", value: "—" },
  ];
  const paras = paragraphsOf(memo.moderator_synthesis || "");
  const lede = paras.shift() || memo.research_summary;

  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar left="Equity Research Memo" right={`${memo.timestamp} · live`} />
      <MemoHero
        ticker={memo.ticker}
        companyLine={company || memo.ticker}
        price={214.82} changeAbs={2.94} changePct={1.39}
        verdict={fmtVerdict(memo)}
        high52w={238} low52w={164} series={series}
      />
      <FactsStrip facts={facts} />
      <Synthesis lede={lede} paragraphs={paras} />
      <WeightBar
        bullWeight={memo.bull_weight ?? 0}
        bearWeight={memo.bear_weight ?? 0}
        bullClaims={artifacts.bull_points?.length ?? 0}
        bearClaims={artifacts.bear_points?.length ?? 0}
      />
      <ClaimGrid
        bullPoints={artifacts.bull_points ?? []}
        bearPoints={artifacts.bear_points ?? []}
      />
      <div className="px-5 py-4 border-b-2 border-ink">
        <div className="label-section mb-3 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
          <span>Thesis Matrix</span>
          <span className="font-mono normal-case tracking-normal text-muted">all claims · saturation = confidence</span>
        </div>
        <ThesisMatrix claims={matrixClaimsOf(artifacts)} />
      </div>
      <AlertStrip
        contradictions={memo.contradictions_detected.length}
        unresolved={memo.unresolved_questions.length}
        agentCount={14}
        sourceCount={memo.citations.length}
        durationS={0}
      />
    </div>
  );
}
