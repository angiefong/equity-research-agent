from pydantic import BaseModel
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.contradiction import Contradiction


class EvidenceContradictionOutput(BaseModel):
    contradictions: list[Contradiction]


_SYSTEM = """You are a contradiction detector. Identify factual conflicts in evidence spans — two claims
about the same metric that cannot both be true (numeric conflicts, direction conflicts, timeline conflicts).

Only flag genuine conflicts between the same metric. Do NOT flag:
- different metrics (e.g. price vs market cap, EPS vs revenue) that happen to be near each other
- the same value expressed with trivial rounding (e.g. 24.0% vs 24.0%)
- peer company values (e.g. MSFT P/E vs AAPL P/E)
- missing/blank values

Return JSON in exactly this shape (report at most 5 most significant):
{
  "contradictions": [
    {
      "claim_a": "<first claim verbatim>",
      "claim_b": "<second claim verbatim>",
      "source_refs": ["<ref_a>", "<ref_b>"],
      "severity": "low" | "medium" | "high",
      "rationale": "<one sentence>"
    }
  ]
}"""


def evidence_contradiction_agent(state: AgentState) -> dict:
    llm = get_structured_llm(EvidenceContradictionOutput, method="json_mode")
    evidence_text = format_evidence(state["evidence"])
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Ticker: {state['ticker']}\n\nEvidence:\n{evidence_text}"},
    ])
    return {"evidence_contradictions": result.contradictions}
