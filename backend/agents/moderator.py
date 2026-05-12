from typing import Any
from pydantic import BaseModel, field_validator, model_validator
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState, resolve_query
from backend.schemas.contradiction import Contradiction
from backend.schemas.debate import DebatePoint
from backend.schemas.memo import ResearchMemo


def _coerce_to_str(v: Any) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        lines = []
        for item in v:
            if isinstance(item, str):
                lines.append(f"- {item}")
            elif isinstance(item, dict):
                arg = item.get("argument") or item.get("claim") or item.get("text") or ""
                cite = item.get("citation") or item.get("source_ref") or ""
                line = f"- {arg}" + (f" [{cite}]" if cite else "")
                lines.append(line)
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    return str(v)


class _ResearchMemoRaw(BaseModel):
    research_summary: str
    bull_case: str
    bear_case: str
    moderator_synthesis: str
    contradictions_detected: list[str]
    contradiction_resolutions: list[str]
    unresolved_questions: list[str]
    thesis_drift_summary: str | None = None
    confidence_notes: str
    scenarios: list[str]
    citations: list[str]

    @model_validator(mode="before")
    @classmethod
    def _fill_missing(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        str_defaults = {
            "research_summary": "",
            "bull_case": "",
            "bear_case": "",
            "moderator_synthesis": "",
            "confidence_notes": "",
        }
        list_defaults = {
            "contradictions_detected": [],
            "contradiction_resolutions": [],
            "unresolved_questions": [],
            "scenarios": [],
            "citations": [],
        }
        for k, v in str_defaults.items():
            data.setdefault(k, v)
        for k, v in list_defaults.items():
            data.setdefault(k, v)
        return data

    @field_validator("bull_case", "bear_case", "moderator_synthesis", "research_summary", "confidence_notes", mode="before")
    @classmethod
    def _strify(cls, v: Any) -> str:
        return _coerce_to_str(v)

    @field_validator(
        "contradictions_detected",
        "contradiction_resolutions",
        "unresolved_questions",
        "scenarios",
        "citations",
        mode="before",
    )
    @classmethod
    def _list_strify(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [item if isinstance(item, str) else _coerce_to_str(item) for item in v]
        return [_coerce_to_str(v)]


class ModeratorOutput(BaseModel):
    memo: _ResearchMemoRaw


_SYSTEM = """You are a financial research moderator producing balanced, source-backed research memos.
You MUST NOT issue investment advice, buy/sell/hold recommendations, suitability assessments, or
price targets. Scenarios below are an ANALYTICAL FRAMEWORK, not a recommendation.
Every factual claim must be tied to a source_ref from the evidence.

Return JSON with ALL 11 of the following keys inside "memo" — do not omit any. Strings must be
strings (not arrays of objects). Arrays must be arrays of strings. Shape:
{
  "memo": {
    "research_summary": "<2-3 sentence overview, STRING>",
    "bull_case": "<synthesis of strongest upside arguments with [N] citations, STRING>",
    "bear_case": "<synthesis of strongest downside arguments with [N] citations, STRING>",
    "moderator_synthesis": "<Reconcile bull and bear using CAUSAL reasoning, not restatement. Identify: (a) facts both sides agree on, (b) key disputed points, (c) which side's evidence is stronger on each dispute and WHY. Do not use the same metric to support opposing conclusions without resolving the tension. Conclude with a named falsifiable condition that would change the call (e.g. 'Services growth dropping below 8% for two consecutive quarters' or 'gross margin compressing >150bps YoY'). STRING>",
    "contradictions_detected": ["<factual conflict stated as a string, e.g. 'Source X says revenue +15%, Source Y says +8%'>", ...],
    "contradiction_resolutions": ["<For each contradiction above, name the better-supported claim and the SPECIFIC reason (source authority, recency, methodology, sample), OR explicitly say 'irreconcilable from current evidence — would need: <named missing data>'. BANNED phrasings: 'depends on various factors', 'influenced by multiple things', 'each interpretation has merit'. One resolution per contradiction, in the same order.>", ...],
    "unresolved_questions": ["<question the evidence cannot answer>", ...],
    "thesis_drift_summary": "<how thesis changed vs prior run, or null if no prior run>",
    "confidence_notes": "<quality and completeness of evidence — name missing data (segments, geographies, guidance), stale dates, single-source claims, STRING>",
    "scenarios": ["Base (<weight>%): <what the evidence suggests is most likely, with key assumptions>", "Bull (<weight>%): <conditions under which upside plays out>", "Bear (<weight>%): <conditions under which downside plays out>"],
    "citations": ["<source_ref string>", ...]
  }
}
All 11 keys are REQUIRED. Scenario weights should sum to ~100 and reflect evidence strength,
not a personal view. Use the TREND of metrics, not just levels. If a section has nothing to
report, use "" for strings or [] for arrays.

DATA RECENCY (CRITICAL — applies to bull_case, bear_case, and contradiction_resolutions):
When the evidence contains multiple values for the same metric (e.g., revenue growth -25.8%
in one span and +11.4% in another, or two different gross margin figures), ALWAYS use the
MOST RECENT span and explicitly note the staleness of the older one in the resolution. Newer
data supersedes older data unless the older span is explicitly more authoritative (e.g., a
filed 10-Q vs. a third-party news estimate). Do not silently quote stale figures in bull_case
or bear_case while the same metric has a newer evidence span available — the judge will catch
this and it is the most common data-integrity failure.

NUMERIC FORMAT CONSISTENCY:
Pick ONE format per metric across the whole memo. Either ratios as decimals (gross margin
0.0267) OR as percentages (gross margin 2.67%) — never mix. Decimals are more error-prone
in prose; prefer percentages with the % sign for any margin / growth / yield figure.

AVOID:
- Restating bull and bear cases side-by-side and calling it synthesis.
- Vague hedges like "depends on market conditions" — name the drivers.
- Labelling growth "slowing" or margins "pressured" without a trend comparison."""


def compute_weights(bull_points: list[dict], bear_points: list[dict]) -> tuple[float, float]:
    """Return (bull_weight, bear_weight) — average confidence per side, 0.0 if empty."""
    def _avg(points: list[dict]) -> float:
        if not points:
            return 0.0
        confs = [p.get("confidence", 0.0) for p in points]
        return sum(confs) / len(confs)
    return _avg(bull_points), _avg(bear_points)


def _format_contradictions(items: list[Contradiction]) -> str:
    if not items:
        return "None detected."
    return "\n".join(f"- [{c.severity.value.upper()}] {c.claim_a} vs {c.claim_b}" for c in items)


def _format_debate(points: list[DebatePoint], label: str) -> str:
    return "\n".join(f"[{label.upper()}-{i+1}] {p.claim} (conf: {p.confidence:.2f})\n  {p.rationale}" for i, p in enumerate(points))


def moderator_agent(state: AgentState) -> dict:
    llm = get_structured_llm(ModeratorOutput, method="json_mode")

    evidence_text = format_evidence(state["evidence"])
    bull_text = _format_debate(state["bull_points"], "bull")
    bear_text = _format_debate(state["bear_points"], "bear")
    contradictions_text = _format_contradictions(
        state["evidence_contradictions"] + state["debate_contradictions"]
    )
    drift_context = ""
    if state.get("thesis_delta"):
        delta = state["thesis_delta"]
        drift_context = (
            f"\nThesis drift since last run:\n"
            f"- Strengthened: {delta.strengthened}\n"
            f"- Weakened: {delta.weakened}\n"
            f"- New: {delta.new}\n"
            f"- Disappeared: {delta.disappeared}"
        )

    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": (
            f"Ticker: {state['ticker']}\nQuery: {resolve_query(state)}\n\n"
            f"Evidence:\n{evidence_text}\n\n"
            f"Bull case:\n{bull_text}\n\n"
            f"Bear case:\n{bear_text}\n\n"
            f"Contradictions:\n{contradictions_text}"
            f"{drift_context}"
        )},
    ])

    bull_weight, bear_weight = compute_weights(
        [p.model_dump() for p in state.get("bull_points", [])],
        [p.model_dump() for p in state.get("bear_points", [])],
    )
    memo = ResearchMemo(**{
        **result.memo.model_dump(),
        "ticker": state["ticker"],
        "bull_weight": bull_weight,
        "bear_weight": bear_weight,
        "company_name": state.get("company_name"),
        "exchange": state.get("exchange"),
        "sector": state.get("sector"),
    })

    return {"final_memo": memo}
