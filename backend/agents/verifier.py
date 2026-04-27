from pydantic import BaseModel
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.contradiction import ContradictionSeverity
from backend.schemas.verification import VerificationIssue, VerificationIssueType


class _VerificationIssueRaw(BaseModel):
    claim: str
    issue_type: VerificationIssueType
    severity: ContradictionSeverity
    suggested_action: str
    target_agent: str | None = None


class VerifierOutput(BaseModel):
    issues: list[_VerificationIssueRaw]


_SYSTEM = """You verify claims in a financial research memo against the evidence provided.
Only flag genuine issues. Omit low-confidence guesses. If claims are well-supported, return an empty list.

Return JSON in exactly this shape (report at most 5 most significant issues):
{
  "issues": [
    {
      "claim": "<exact claim verbatim>",
      "issue_type": "unsupported_claim" | "numeric_mismatch" | "source_not_found" | "stale_data",
      "severity": "low" | "medium" | "high",
      "suggested_action": "<one sentence corrective action>",
      "target_agent": "market_data" | "filings" | "news" | "quant_data" | null
    }
  ]
}

target_agent must be one of market_data, filings, news, quant_data, or null."""


def verifier_agent(state: AgentState) -> dict:
    llm = get_structured_llm(VerifierOutput, method="json_mode")
    evidence_text = format_evidence(state["evidence"])

    all_claims = (
        [p.claim for p in state["bull_points"]]
        + [p.claim for p in state["bear_points"]]
    )
    claims_text = "\n".join(f"- {c}" for c in all_claims)

    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Ticker: {state['ticker']}\n\n"
            f"Claims to verify:\n{claims_text}\n\n"
            f"Available evidence:\n{evidence_text}"
        )},
    ])

    issues = [VerificationIssue(**i.model_dump()) for i in result.issues]

    high_severity = [i for i in issues if i.severity == ContradictionSeverity.HIGH]
    if high_severity:
        targets = list({i.target_agent for i in high_severity if i.target_agent})
        status = "needs_reroute" if targets else "fail"
    elif issues:
        status = "fail"
        targets = []
    else:
        status = "pass"
        targets = []

    return {
        "verification_issues": issues,
        "verification_status": status,
        "reroute_targets": targets,
    }
