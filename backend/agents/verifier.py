from pydantic import BaseModel
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.schemas.contradiction import ContradictionSeverity
from backend.schemas.verification import VerificationIssue


class VerifierOutput(BaseModel):
    issues: list[VerificationIssue]


_SYSTEM = """You verify claims in a financial research memo against the evidence provided.
For each issue found:
- quote the exact claim
- classify the issue_type: unsupported_claim, numeric_mismatch, source_not_found, stale_data
- rate severity: low, medium, high
- suggest a corrective action
- name the target_agent to reroute (market_data, filings, news, or quant_data) if needed
Only flag genuine issues. Omit low-confidence guesses. If claims are well-supported, return an empty list."""


def verifier_agent(state: AgentState) -> dict:
    llm = get_structured_llm(VerifierOutput)
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

    high_severity = [
        i for i in result.issues
        if i.severity == ContradictionSeverity.HIGH
    ]
    if high_severity:
        targets = list({i.target_agent for i in high_severity if i.target_agent})
        status = "needs_reroute" if targets else "fail"
    elif result.issues:
        status = "fail"
        targets = []
    else:
        status = "pass"
        targets = []

    return {
        "verification_issues": result.issues,
        "verification_status": status,
        "reroute_targets": targets,
    }
