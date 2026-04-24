from pydantic import BaseModel
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.debate import DebatePoint, DebateSide


class BullOutput(BaseModel):
    debate_points: list[DebatePoint]


_SYSTEM = """You are a bull-case analyst. Given evidence about a company, build the strongest possible
upside thesis. For each debate point:
- state a clear, specific claim (not vague optimism)
- list the evidence_span_ids (numbers from the evidence list) that support it
- assign a confidence score 0.0-1.0 based on evidence quality
- write a rationale citing specific evidence
Focus on: revenue growth, margin expansion, competitive moats, catalysts, undervaluation.
All claims must be tied to evidence. Do not invent facts."""


def bull_agent(state: AgentState) -> dict:
    llm = get_structured_llm(BullOutput)
    evidence_text = format_evidence(state["evidence"])
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\nQuery: {state['query']}\n\nEvidence:\n{evidence_text}"},
    ])
    for point in result.debate_points:
        point.side = DebateSide.BULL
    return {"bull_points": result.debate_points}
