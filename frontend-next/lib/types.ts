export type ResearchMemo = {
  id: string;
  ticker: string;
  timestamp: string;
  research_summary: string;
  bull_case: string;
  bear_case: string;
  moderator_synthesis: string;
  contradictions_detected: string[];
  unresolved_questions: string[];
  thesis_drift_summary: string | null;
  confidence_notes: string;
  citations: string[];
  bull_weight: number | null;
  bear_weight: number | null;
  company_name: string | null;
  exchange: string | null;
  sector: string | null;
};

export type ClaimPoint = {
  claim: string;
  confidence: number;
  rationale: string;
  evidence_span_ids?: string[];
};

export type Artifacts = {
  bull_points?: ClaimPoint[];
  bear_points?: ClaimPoint[];
  evidence?: unknown[];
  evidence_contradictions?: unknown[];
  debate_contradictions?: unknown[];
  verification_issues?: unknown[];
  thesis_delta?: unknown;
  market_snapshot?: MarketSnapshot;
  duration_s?: number;
  agent_count?: number;
};

export type RunSummary = {
  run_id: string;
  ticker: string;
  verdict: string;
  bull_weight: number | null;
  bear_weight: number | null;
  lede: string;
  duration_s: number;
  agent_count: number;
  created_at: string;
};

export type AgentStatus = "pending" | "running" | "completed" | "failed";

export type PricePoint = { date: string; price: number };

export type MarketSnapshot = {
  ticker: string;
  current_price: number;
  change_abs: number | null;
  change_pct: number | null;
  high_52w: number | null;
  low_52w: number | null;
  market_cap: number | null;
  pe_forward: number | null;
  eps_ttm: number | null;
  dividend_yield: number | null;
  volume: number | null;
  series: PricePoint[];
};
