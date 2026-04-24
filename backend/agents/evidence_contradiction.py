from pydantic import BaseModel
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.contradiction import Contradiction


class EvidenceContradictionOutput(BaseModel):
    contradictions: list[Contradiction]


_SYSTEM = """You are a contradiction detector. Review the evidence spans and identify factual conflicts.
A contradiction is two claims that cannot both be true — especially numeric conflicts, direction conflicts
(grew vs declined), or timeline conflicts. For each contradiction:
- state claim_a and claim_b verbatim
- list source_refs for both
- rate severity: low (minor inconsistency), medium (notable conflict), high (direct factual conflict)
- write a one-sentence rationale
Only flag genuine conflicts, not different perspectives on the same fact."""


def evidence_contradiction_agent(state: AgentState) -> dict:
    llm = get_structured_llm(EvidenceContradictionOutput)
    evidence_text = format_evidence(state["evidence"])
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\n\nEvidence:\n{evidence_text}"},
    ])
    return {"evidence_contradictions": result.contradictions}
