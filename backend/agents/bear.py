from pydantic import BaseModel, Field, model_validator
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState, resolve_query
from backend.schemas.debate import DebatePoint, DebateSide


class _BearPointRaw(BaseModel):
    claim: str
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_span_ids: list[str]


class BearOutput(BaseModel):
    debate_points: list[_BearPointRaw]

    @model_validator(mode="before")
    @classmethod
    def _unwrap_llm_drift(cls, data):
        if not isinstance(data, dict) or "debate_points" in data:
            return data
        for key in ("bear_case", "bear", "points"):
            if key in data:
                v = data[key]
                return {"debate_points": v.get("debate_points", []) if isinstance(v, dict) else v}
        return data


_SYSTEM = """You are a bear-case analyst. Build the strongest possible downside thesis ANCHORED ONLY in the provided evidence.

RULES — every claim must:
1. Be specific and metric-anchored. Banned without a number or evidence span: "weakening",
   "pressured", "challenging", "concerning", "risky". If you can't cite a metric, drop the claim.
2. Cover one of: valuation risk (e.g., PEG > peers, multiple contraction), competitive threat
   (named competitor, quantified share/margin impact), margin pressure TREND (direction and
   magnitude), execution risk (named catalyst or miss), macro/FX/regulatory headwind with
   mechanism and P&L line item affected.
3. Use a causal chain in rationale:
     driver (what is changing) → mechanism (why it hurts P&L) →
     financial impact (which line item, rough magnitude) → valuation impact.
4. Cite evidence_span_ids for every factual assertion. No span = no claim.

AVOID:
- Generic risks that apply to any peer ("macro uncertainty", "competitive industry").
- Level comparisons without trend — a high P/E alone is not bearish without growth context.
- Using a 90-day price decline as a thesis — name the fundamental driver, not the price action.
- Flipping the same metric the bull uses without resolving the tension.
- Treating a NEGATIVE ratio as bullish or bearish in the same direction as a positive one.
  EV/EBITDA below zero, P/E below zero, etc. mean the underlying is negative — these CANNOT be
  compared on the same number line as positive multiples. If the only available multiple is
  negative, state the underlying loss directly ("EBITDA is -$X.YB") and discuss the path to
  positive territory; do not call the ratio "cheaper" or "expensive".

ARITHMETIC SANITY (CRITICAL — before submitting any cross-ticker comparison):
If you make a directional claim about two numbers ("X has HIGHER margin than peer Y at..."), the
math must match the direction word. State direction words only after verifying they match the
arithmetic. If your claim's direction contradicts the numbers, drop the claim.

Return JSON with exactly ONE top-level key: "debate_points" (an array). Do NOT add outer wrappers
like "bull_case" or "bear_case" — this is the BEAR agent only, so only return bear points. Report at
most 5 strongest points. Shape:
{
  "debate_points": [
    {
      "claim": "<specific, metric-anchored downside claim, one sentence>",
      "rationale": "<driver → mechanism → financial impact → valuation impact, with [N] citations>",
      "confidence": <float 0.0-1.0>,
      "evidence_span_ids": ["1", "3", "7"]
    }
  ]
}
evidence_span_ids must be strings referencing the [N] labels in the evidence list."""


def bear_agent(state: AgentState) -> dict:
    llm = get_structured_llm(BearOutput, method="json_mode")
    evidence_text = format_evidence(state["evidence"])
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\nQuery: {resolve_query(state)}\n\nEvidence:\n{evidence_text}"},
    ])
    points = [DebatePoint(**{**p.model_dump(), "side": DebateSide.BEAR}) for p in result.debate_points]
    return {"bear_points": points}
