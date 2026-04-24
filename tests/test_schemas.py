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
