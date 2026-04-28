from pydantic import BaseModel, Field, model_validator
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState, resolve_query
from backend.schemas.debate import DebatePoint, DebateSide


class _BullPointRaw(BaseModel):
    claim: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_span_ids: list[str]


class BullOutput(BaseModel):
    debate_points: list[_BullPointRaw]

    @model_validator(mode="before")
    @classmethod
    def _unwrap_llm_drift(cls, data):
        if not isinstance(data, dict) or "debate_points" in data:
            return data
        for key in ("bull_case", "bull", "points"):
            if key in data:
                v = data[key]
                return {"debate_points": v.get("debate_points", []) if isinstance(v, dict) else v}
        return data


_SYSTEM = """You are a bull-case analyst. Build the strongest possible upside thesis ANCHORED ONLY in the provided evidence.

RULES — every claim must:
1. Be specific and metric-anchored. Banned without a number or evidence span: "strong", "robust",
   "healthy", "premium", "solid", "dominant". If you can't cite a metric, drop the claim.
2. Cover one of: revenue driver (by segment/geography where evidence supports), margin TREND
   (direction and magnitude, not just level), named catalyst within ~12 months, valuation vs
   growth (PEG-style, not raw P/E), durable moat with quantifiable evidence.
3. Use a causal chain in rationale:
     driver (what is changing) → mechanism (why it moves P&L) →
     financial impact (which line item, rough magnitude) → valuation impact.
4. Cite evidence_span_ids for every factual assertion. No span = no claim.

AVOID:
- Generic statements that apply to any peer ("strong ecosystem", "premium brand").
- Level comparisons without trend ("margin is 47%" alone is not a thesis).
- Raw P/E comparisons without growth context.
- Restating evidence as a claim — synthesize into a causal argument.

ARITHMETIC SANITY (CRITICAL — before submitting any cross-ticker comparison):
If you make a directional claim about two numbers (e.g. "AAPL P/E 34.35 is LOWER than GOOGL P/E
31.86"), the math must match the direction word. 34.35 > 31.86, so AAPL would be HIGHER. State
the direction word (higher / lower / cheaper / more expensive) only after verifying it matches
the numbers. If your claim's direction contradicts the arithmetic, drop the claim — do NOT submit.

Return JSON with exactly ONE top-level key: "debate_points" (an array). Do NOT add outer wrappers
like "bull_case" or "bear_case" — this is the BULL agent only, so only return bull points. Report at
most 5 strongest points. Shape:
{
  "debate_points": [
    {
      "claim": "<specific, metric-anchored upside claim, one sentence>",
      "rationale": "<driver → mechanism → financial impact → valuation impact, with [N] citations>",
      "confidence": <float 0.0-1.0>,
      "evidence_span_ids": ["1", "3", "7"]
    }
  ]
}

ALL FOUR FIELDS ARE REQUIRED on every debate_point. Do NOT omit any.
- "confidence" must be a numeric float between 0.0 and 1.0 (your subjective confidence in this
  claim given the evidence). Never skip this field.
- "evidence_span_ids" must be a SEPARATE ARRAY of string ids (e.g. ["1", "7"]) — citations
  embedded inline in the rationale ("...impact. [6], [22]") DO NOT COUNT. The dedicated array
  is required even if you also reference the same ids inline. evidence_span_ids must be strings
  referencing the [N] labels in the evidence list."""


def bull_agent(state: AgentState) -> dict:
    llm = get_structured_llm(BullOutput, method="json_mode")
    evidence_text = format_evidence(state["evidence"])
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\nQuery: {resolve_query(state)}\n\nEvidence:\n{evidence_text}"},
    ])
    points = [DebatePoint(**{**p.model_dump(), "side": DebateSide.BULL}) for p in result.debate_points]
    return {"bull_points": points}
