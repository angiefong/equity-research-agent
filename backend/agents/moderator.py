from typing import Any
from pydantic import BaseModel, field_validator, model_validator
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState
from backend.persistence.snapshot_store import save_snapshot
from backend.schemas.contradiction import Contradiction
from backend.schemas.debate import DebatePoint
from backend.schemas.memo import ResearchMemo
from backend.schemas.thesis import ThesisSnapshot


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
    unresolved_questions: list[str]
    thesis_drift_summary: str | None = None
    confidence_notes: str
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
            "unresolved_questions": [],
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

    @field_validator("contradictions_detected", "unresolved_questions", "citations", mode="before")
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
You MUST NOT issue investment advice, buy/sell/hold recommendations, or suitability assessments.
Every factual claim must be tied to a source_ref from the evidence.

Return JSON with ALL of the following 9 keys inside "memo" — do not omit any. Strings must be strings
(not arrays of objects). Arrays must be arrays of strings. Shape:
{
  "memo": {
    "research_summary": "<2-3 sentence overview, STRING>",
    "bull_case": "<strongest upside arguments with citations, STRING>",
    "bear_case": "<strongest downside arguments with citations, STRING>",
    "moderator_synthesis": "<reconcile bull and bear — agreed facts, key disputed points, STRING>",
    "contradictions_detected": ["<factual conflict as a string>", ...],
    "unresolved_questions": ["<question the evidence cannot answer>", ...],
    "thesis_drift_summary": "<how thesis changed vs prior run, or null if no prior run>",
    "confidence_notes": "<quality and completeness of evidence, STRING>",
    "citations": ["<source_ref string>", ...]
  }
}
All 9 keys are REQUIRED. If a section has nothing to report, use "" for strings or [] for arrays."""


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
            f"Ticker: {state['ticker']}\nQuery: {state['query']}\n\n"
            f"Evidence:\n{evidence_text}\n\n"
            f"Bull case:\n{bull_text}\n\n"
            f"Bear case:\n{bear_text}\n\n"
            f"Contradictions:\n{contradictions_text}"
            f"{drift_context}"
        )},
    ])

    memo = ResearchMemo(**{**result.memo.model_dump(), "ticker": state["ticker"]})

    snapshot = ThesisSnapshot(
        ticker=state["ticker"],
        bull_points=state["bull_points"],
        bear_points=state["bear_points"],
        confidence_by_topic={
            p.claim[:40]: p.confidence
            for p in state["bull_points"] + state["bear_points"]
        },
    )
    save_snapshot(snapshot)

    return {
        "final_memo": memo,
        "thesis_snapshot_current": snapshot,
    }
