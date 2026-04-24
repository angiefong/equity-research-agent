import os
from pydantic import BaseModel
from backend.agents._prompts import format_evidence
from backend.agents.llm import get_llm, get_structured_llm
from backend.graph.state import AgentState
from backend.persistence.snapshot_store import save_snapshot
from backend.schemas.contradiction import Contradiction
from backend.schemas.debate import DebatePoint
from backend.schemas.memo import ResearchMemo
from backend.schemas.thesis import ThesisSnapshot
from datetime import datetime


class ModeratorOutput(BaseModel):
    memo: ResearchMemo


_SYSTEM = """You are a financial research moderator producing balanced, source-backed research memos.
You MUST NOT issue investment advice, buy/sell/hold recommendations, or suitability assessments.

Produce a structured memo with all required sections:
- research_summary: 2-3 sentence overview
- bull_case: strongest upside arguments with citations
- bear_case: strongest downside arguments with citations
- moderator_synthesis: reconcile bull and bear — agreed facts, key disputed points
- contradictions_detected: list any factual conflicts found
- unresolved_questions: questions the evidence cannot answer
- thesis_drift_summary: how thesis changed vs prior run (omit if no prior run — set to null)
- confidence_notes: quality and completeness of evidence
- citations: list all source_refs used

Every factual claim must be tied to a source_ref from the evidence."""


def _format_contradictions(items: list[Contradiction]) -> str:
    if not items:
        return "None detected."
    return "\n".join(f"- [{c.severity.value.upper()}] {c.claim_a} vs {c.claim_b}" for c in items)


def _format_debate(points: list[DebatePoint], label: str) -> str:
    return "\n".join(f"[{label.upper()}-{i+1}] {p.claim} (conf: {p.confidence:.2f})\n  {p.rationale}" for i, p in enumerate(points))


def moderator_agent(state: AgentState) -> dict:
    llm = get_structured_llm(ModeratorOutput)

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
        "final_memo": result.memo,
        "thesis_snapshot_current": snapshot,
    }
