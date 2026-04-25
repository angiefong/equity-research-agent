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
