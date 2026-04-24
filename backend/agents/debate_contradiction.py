from pydantic import BaseModel
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.contradiction import Contradiction
from backend.schemas.debate import DebatePoint


class DebateContradictionOutput(BaseModel):
    contradictions: list[Contradiction]


_SYSTEM = """You identify conflicts between bull and bear thesis points.
A debate contradiction is where one side's claim directly conflicts with the other —
not just different opinions, but mutually exclusive assertions about the same fact or metric.
For each conflict, cite the specific bull and bear claims, rate severity, and explain the conflict."""


def _format_points(points: list[DebatePoint], label: str) -> str:
    return "\n".join(f"[{label.upper()}-{i+1}] {p.claim} (confidence: {p.confidence:.2f})" for i, p in enumerate(points))


def debate_contradiction_agent(state: AgentState) -> dict:
    llm = get_structured_llm(DebateContradictionOutput)
    bull_text = _format_points(state["bull_points"], "bull")
    bear_text = _format_points(state["bear_points"], "bear")
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\n\nBull points:\n{bull_text}\n\nBear points:\n{bear_text}"},
    ])
    return {"debate_contradictions": result.contradictions}
