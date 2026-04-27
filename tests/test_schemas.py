from backend.schemas.evidence import EvidenceSpan, Claim
from backend.schemas.debate import DebatePoint, DebateSide

def test_evidence_span_defaults():
    span = EvidenceSpan(
        text="AAPL revenue grew 10% YoY",
        source_ref="market:AAPL-financials:revenue-growth",
        agent_origin="market_data",
    )
    assert span.id is not None
    assert span.confidence == 1.0
    assert span.chart_data is None

def test_evidence_span_requires_text():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        EvidenceSpan(source_ref="market:AAPL:revenue", agent_origin="market_data")

def test_claim_defaults():
    claim = Claim(
        assertion="AAPL revenue grew 10%",
        source_ref="market:AAPL-financials:revenue-growth",
        confidence=0.9,
    )
    assert claim.id is not None

def test_debate_point_bull():
    dp = DebatePoint(
        side=DebateSide.BULL,
        claim="Strong revenue growth driven by services",
        evidence_span_ids=["abc-123"],
        confidence=0.85,
        rationale="Services segment grew 14% YoY",
    )
    assert dp.id is not None
    assert dp.side == DebateSide.BULL

def test_debate_point_requires_rationale():
    from pydantic import ValidationError
    import pytest
    with pytest.raises(ValidationError):
        DebatePoint(side=DebateSide.BEAR, claim="x", evidence_span_ids=[], confidence=0.5)

from backend.schemas.contradiction import Contradiction, ContradictionSeverity, ContradictionStatus

def test_contradiction_defaults_to_open():
    c = Contradiction(
        claim_a="Revenue grew 10%",
        claim_b="Revenue declined 2%",
        source_refs=["sec:AAPL-10K-2024:financials", "news:tavily-article:2024-01-15"],
        severity=ContradictionSeverity.HIGH,
        rationale="Direct numeric conflict on revenue direction",
    )
    assert c.status == ContradictionStatus.OPEN
    assert c.id is not None

from backend.schemas.verification import VerificationIssue, VerificationIssueType
from backend.schemas.contradiction import ContradictionSeverity

def test_verification_issue():
    vi = VerificationIssue(
        claim="EPS grew 15% YoY",
        issue_type=VerificationIssueType.NUMERIC_MISMATCH,
        severity=ContradictionSeverity.HIGH,
        suggested_action="Re-fetch earnings data from EDGAR",
        target_agent="filings",
    )
    assert vi.id is not None
    assert vi.target_agent == "filings"

def test_verification_issue_target_agent_optional():
    vi = VerificationIssue(
        claim="Strong brand loyalty",
        issue_type=VerificationIssueType.UNSUPPORTED_CLAIM,
        severity=ContradictionSeverity.MEDIUM,
        suggested_action="Add source citation",
    )
    assert vi.target_agent is None

from backend.schemas.thesis import ThesisSnapshot, ThesisDelta, ConfidenceDrift
from backend.schemas.debate import DebatePoint, DebateSide

def test_thesis_snapshot():
    snap = ThesisSnapshot(
        ticker="AAPL",
        bull_points=[],
        bear_points=[],
        confidence_by_topic={"growth": 0.8, "risk": 0.4},
    )
    assert snap.id is not None
    assert snap.ticker == "AAPL"
    assert snap.timestamp is not None

def test_thesis_delta():
    delta = ThesisDelta(
        ticker="AAPL",
        previous_run_id="abc",
        current_run_id="xyz",
        strengthened=["Services revenue growth thesis"],
        weakened=[],
        new=["AI hardware supercycle argument"],
        disappeared=["China market expansion thesis"],
        confidence_drift=[
            ConfidenceDrift(topic="growth", previous=0.7, current=0.85, delta=0.15)
        ],
    )
    assert len(delta.strengthened) == 1
    assert delta.confidence_drift[0].delta == 0.15

from backend.schemas.memo import ResearchMemo

def test_research_memo_first_run():
    memo = ResearchMemo(
        ticker="AAPL",
        research_summary="AAPL shows strong services growth",
        bull_case="Services segment expanding margins",
        bear_case="Hardware saturation risk",
        moderator_synthesis="Balanced outlook with services as swing factor",
        contradictions_detected=["Revenue direction conflict between 10-K and news"],
        unresolved_questions=["Will China sales recover in H2?"],
        thesis_drift_summary=None,
        confidence_notes="High confidence on financials, medium on macro",
        citations=["sec:AAPL-10K-2024:financials", "market:AAPL-price:90d-history"],
    )
    assert memo.id is not None
    assert memo.thesis_drift_summary is None

def test_research_memo_second_run_has_drift():
    memo = ResearchMemo(
        ticker="AAPL",
        research_summary="Updated thesis",
        bull_case="x",
        bear_case="y",
        moderator_synthesis="z",
        contradictions_detected=[],
        unresolved_questions=[],
        thesis_drift_summary="Services thesis strengthened; China risk newly emerged",
        confidence_notes="High",
        citations=[],
    )
    assert memo.thesis_drift_summary is not None
