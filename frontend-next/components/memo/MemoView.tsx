import type { Artifacts, ResearchMemo, MarketSnapshot } from "@/lib/types";
import { Topbar } from "@/components/ui/Topbar";
import { MemoHero } from "@/components/memo/MemoHero";
import { FactsStrip, type Fact } from "@/components/memo/FactsStrip";
import { Synthesis } from "@/components/memo/Synthesis";
import { ClaimGrid } from "@/components/memo/ClaimGrid";
import { AlertStrip } from "@/components/memo/AlertStrip";
import { WeightBar } from "@/components/viz/WeightBar";
import { ThesisMatrix, type MatrixClaim } from "@/components/viz/ThesisMatrix";
import { fmtCompact, fmtCurrency, fmtPct, fmtVolume, fmtOrDash } from "@/lib/format";

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

function factsFromSnapshot(snap: MarketSnapshot | undefined): Fact[] {
  const high = snap?.high_52w, low = snap?.low_52w;
  const range = (high != null && low != null) ? `${low.toFixed(0)} – ${high.toFixed(0)}` : "—";
  return [
    { label: "Mkt Cap",  value: fmtOrDash(snap?.market_cap,     fmtCompact) },
    { label: "P/E (Fwd)", value: fmtOrDash(snap?.pe_forward,    (n) => n.toFixed(2)) },
    { label: "EPS (TTM)", value: fmtOrDash(snap?.eps_ttm,       (n) => `$${n.toFixed(2)}`) },
    { label: "Div Yield", value: fmtOrDash(snap?.dividend_yield, fmtPct) },
    { label: "52W Range", value: range },
    { label: "Volume",   value: fmtOrDash(snap?.volume,         fmtVolume) },
  ];
}

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  const snap = artifacts.market_snapshot;
  const company = [memo.company_name, memo.exchange, memo.sector].filter(Boolean).join(" · ");
  const series = snap?.series.map(p => ({ date: p.date, price: p.price })) ?? [];
  const facts = factsFromSnapshot(snap);
  const paras = paragraphsOf(memo.moderator_synthesis || "");
  const lede = paras.shift() || memo.research_summary;

  const price = snap?.current_price ?? 0;
  const changeAbs = snap?.change_abs ?? 0;
  const changePct = snap?.change_pct ?? 0;
  const high52w = snap?.high_52w ?? (series.length ? Math.max(...series.map(p => p.price)) : price);
  const low52w  = snap?.low_52w  ?? (series.length ? Math.min(...series.map(p => p.price)) : price);

  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar left="Equity Research Memo" right={`${memo.timestamp} · live`} />
      <MemoHero
        ticker={memo.ticker}
        companyLine={company || memo.ticker}
        price={price}
        changeAbs={changeAbs}
        changePct={changePct}
        verdict={fmtVerdict(memo)}
        high52w={high52w}
        low52w={low52w}
        series={series}
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
        agentCount={artifacts.agent_count ?? 0}
        sourceCount={memo.citations.length}
        durationS={artifacts.duration_s ?? 0}
      />
    </div>
  );
}
