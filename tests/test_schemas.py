from backend.schemas.evidence import EvidenceSpan, Claim

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
