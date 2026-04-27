from pydantic import BaseModel
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.contradiction import Contradiction
from backend.schemas.debate import DebatePoint


class DebateContradictionOutput(BaseModel):
    contradictions: list[Contradiction]


_SYSTEM = """You identify conflicts between bull and bear thesis points — mutually exclusive assertions
about the same fact or metric (not just different opinions).

Return JSON in exactly this shape (report at most 5 most significant):
{
  "contradictions": [
    {
      "claim_a": "<bull claim verbatim>",
      "claim_b": "<bear claim verbatim>",
      "source_refs": ["BULL-N", "BEAR-M"],
      "severity": "low" | "medium" | "high",
      "rationale": "<one sentence explaining the conflict>"
    }
  ]
}"""


def _format_points(points: list[DebatePoint], label: str) -> str:
    return "\n".join(f"[{label.upper()}-{i+1}] {p.claim} (confidence: {p.confidence:.2f})" for i, p in enumerate(points))


def debate_contradiction_agent(state: AgentState) -> dict:
    llm = get_structured_llm(DebateContradictionOutput, method="json_mode")
    bull_text = _format_points(state["bull_points"], "bull")
    bear_text = _format_points(state["bear_points"], "bear")
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\n\nBull points:\n{bull_text}\n\nBear points:\n{bear_text}"},
    ])
    return {"debate_contradictions": result.contradictions}
