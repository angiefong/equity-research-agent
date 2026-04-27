from typing import Annotated, Literal, Optional
from typing_extensions import NotRequired, TypedDict

from backend.schemas.contradiction import Contradiction
from backend.schemas.debate import DebatePoint
from backend.schemas.evidence import EvidenceSpan
from backend.schemas.memo import ResearchMemo
from backend.schemas.thesis import ThesisSnapshot, ThesisDelta
from backend.schemas.verification import VerificationIssue
from backend.graph.reducers import dedupe_by_id


class InputState(TypedDict):
    ticker: str
    query: NotRequired[str]


class AgentState(TypedDict):
    query: str
    ticker: str
    query_type: Literal["earnings", "bull_bear", "thesis_drift", "unknown"]
    evidence: Annotated[list[EvidenceSpan], dedupe_by_id]
    bull_points: Annotated[list[DebatePoint], dedupe_by_id]
    bear_points: Annotated[list[DebatePoint], dedupe_by_id]
    evidence_contradictions: Annotated[list[Contradiction], dedupe_by_id]
    debate_contradictions: Annotated[list[Contradiction], dedupe_by_id]
    verification_issues: Annotated[list[VerificationIssue], dedupe_by_id]
    thesis_snapshot_prior: Optional[ThesisSnapshot]
    thesis_snapshot_current: Optional[ThesisSnapshot]
    thesis_delta: Optional[ThesisDelta]
    final_memo: Optional[ResearchMemo]
    reroute_count_total: int
    reroute_targets: list[str]
    verification_status: Literal["pending", "pass", "fail", "needs_reroute"]


class OutputState(TypedDict):
    final_memo: ResearchMemo
    thesis_delta: Optional[ThesisDelta]
    evidence_contradictions: list[Contradiction]
    debate_contradictions: list[Contradiction]


DEFAULT_QUERY_TEMPLATE = "Build a bull and bear case for {ticker}"


def resolve_query(state: "AgentState | InputState") -> str:
    """Return the user's query, or a default keyed off the ticker if absent."""
    q = state.get("query")
    if q:
        return q
    return DEFAULT_QUERY_TEMPLATE.format(ticker=state["ticker"])
