from pydantic import BaseModel, Field, model_validator
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
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


_SYSTEM = """You are a bull-case analyst. Given evidence about a company, build the strongest possible
upside thesis focusing on: revenue growth, margin expansion, competitive moats, catalysts, undervaluation.
All claims must be tied to evidence. Do not invent facts.

Return JSON with exactly ONE top-level key: "debate_points" (an array). Do NOT add outer wrappers
like "bull_case" or "bear_case" — this is the BULL agent only, so only return bull points. Report at
most 5 strongest points. Shape:
{
  "debate_points": [
    {
      "claim": "<specific upside claim>",
      "rationale": "<cite specific evidence>",
      "confidence": <float 0.0-1.0>,
      "evidence_span_ids": ["1", "3", "7"]
    }
  ]
}
evidence_span_ids must be strings referencing the [N] labels in the evidence list."""


def bull_agent(state: AgentState) -> dict:
    llm = get_structured_llm(BullOutput, method="json_mode")
    evidence_text = format_evidence(state["evidence"])
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\nQuery: {state['query']}\n\nEvidence:\n{evidence_text}"},
    ])
    points = [DebatePoint(**{**p.model_dump(), "side": DebateSide.BULL}) for p in result.debate_points]
    return {"bull_points": points}
