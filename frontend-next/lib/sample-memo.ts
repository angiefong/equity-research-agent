import type { Artifacts, ResearchMemo } from "@/lib/types";

export const sampleMemo = {
  id: "sample-aapl-research-memo",
  ticker: "AAPL",
  timestamp: "2026-06-26T17:00:00.000Z",
  research_summary:
    "Apple remains a quality compounder, but the memo frames the setup as balanced rather than one-sided: Services durability and capital returns support the bull case, while iPhone replacement cycles and AI monetization timing keep the bear case relevant.",
  bull_case:
    "Services mix, installed-base retention, and buybacks can support earnings per share even if hardware growth is uneven.",
  bear_case:
    "The valuation leaves limited room for delayed AI monetization, slower China demand, or an iPhone cycle that fails to accelerate.",
  moderator_synthesis:
    "Apple's strongest evidence is not a single product catalyst; it is the combination of recurring Services revenue, ecosystem retention, and disciplined capital return.\n\nThe main risk is timing. If investors price near-term Apple Intelligence upside before revenue contribution is visible, the multiple can compress even while the operating business remains healthy.\n\nFor a live investment memo, the next evidence to verify would be segment-level Services growth, Greater China revenue trajectory, and management commentary on AI-related monetization.",
  contradictions_detected: [
    "Services durability supports margin resilience, but hardware concentration still drives near-term revenue variability.",
    "Capital returns improve per-share metrics, but they do not fully offset a multiple that already prices high execution quality.",
  ],
  unresolved_questions: [
    "How quickly can Apple Intelligence features convert into measurable Services revenue?",
    "Is Greater China demand stabilizing or still a drag on the next iPhone cycle?",
  ],
  thesis_drift_summary: null,
  confidence_notes:
    "Sample memo for product demonstration only. It illustrates the memo structure, citation style, and bull/bear weighting without running live agents.",
  citations: [
    "sec:AAPL-10K-2025:services-net-sales",
    "market:AAPL-snapshot:price-and-valuation",
    "news:AAPL-ai-monetization:industry-coverage",
    "quant:AAPL-peer-comps:forward-pe",
  ],
  bull_weight: 0.56,
  bear_weight: 0.44,
  company_name: "Apple Inc.",
  exchange: "NASDAQ",
  sector: "Technology",
} satisfies ResearchMemo;

export const sampleArtifacts = {
  bull_points: [
    {
      claim: "Services mix supports margin resilience",
      confidence: 0.78,
      rationale:
        "Recurring Services revenue can cushion hardware cyclicality and creates a cleaner bridge from installed-base growth to profit durability.",
      evidence_span_ids: ["sec:AAPL-10K-2025:services-net-sales"],
    },
    {
      claim: "Capital returns support EPS growth",
      confidence: 0.72,
      rationale:
        "Buybacks and dividend growth help convert stable free cash flow into per-share value even when unit growth is modest.",
      evidence_span_ids: ["market:AAPL-capital-return:buybacks"],
    },
    {
      claim: "AI features can deepen ecosystem lock-in",
      confidence: 0.58,
      rationale:
        "The upside case is less about immediate subscription revenue and more about retention, upgrade intent, and Services attachment.",
      evidence_span_ids: ["news:AAPL-ai-monetization:industry-coverage"],
    },
  ],
  bear_points: [
    {
      claim: "Valuation prices high execution quality",
      confidence: 0.74,
      rationale:
        "A premium multiple limits upside if AI contribution is slow or if Services growth normalizes faster than expected.",
      evidence_span_ids: ["quant:AAPL-peer-comps:forward-pe"],
    },
    {
      claim: "iPhone cycle remains the near-term swing factor",
      confidence: 0.69,
      rationale:
        "Hardware still drives a large share of revenue, so weak replacement demand can pressure total company growth despite Services strength.",
      evidence_span_ids: ["sec:AAPL-10K-2025:iphone-net-sales"],
    },
    {
      claim: "China demand is an unresolved risk",
      confidence: 0.62,
      rationale:
        "Competitive and macro pressure in Greater China could offset gains from other geographies if the next cycle disappoints.",
      evidence_span_ids: ["sec:AAPL-10K-2025:greater-china"],
    },
  ],
  evidence: [],
  evidence_contradictions: [],
  debate_contradictions: [],
  verification_issues: [],
  market_snapshot: {
    ticker: "AAPL",
    current_price: 214.82,
    change_abs: 2.94,
    change_pct: 1.39,
    high_52w: 237.49,
    low_52w: 164.08,
    market_cap: 3290000000000,
    pe_forward: 27.8,
    eps_ttm: 6.42,
    dividend_yield: 0.0048,
    volume: 48120000,
    series: [
      { date: "2026-01-02", price: 187.22 },
      { date: "2026-02-02", price: 195.41 },
      { date: "2026-03-02", price: 202.16 },
      { date: "2026-04-02", price: 198.73 },
      { date: "2026-05-02", price: 207.64 },
      { date: "2026-06-02", price: 214.82 },
    ],
  },
  duration_s: 126,
  agent_count: 15,
} satisfies Artifacts;
