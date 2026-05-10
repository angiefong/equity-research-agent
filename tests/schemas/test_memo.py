from datetime import datetime
from backend.schemas.memo import ResearchMemo


def test_memo_has_weight_fields():
    m = ResearchMemo(
        ticker="AAPL",
        research_summary="...",
        bull_case="...",
        bear_case="...",
        moderator_synthesis="...",
        contradictions_detected=[],
        unresolved_questions=[],
        confidence_notes="...",
        citations=[],
        bull_weight=0.78,
        bear_weight=0.64,
        company_name="Apple Inc.",
        exchange="NASDAQ",
        sector="Consumer Electronics",
    )
    assert m.bull_weight == 0.78
    assert m.bear_weight == 0.64
    assert m.company_name == "Apple Inc."
    assert m.exchange == "NASDAQ"
    assert m.sector == "Consumer Electronics"


def test_memo_metadata_optional():
    m = ResearchMemo(
        ticker="AAPL",
        research_summary="x", bull_case="x", bear_case="x",
        moderator_synthesis="x", contradictions_detected=[],
        unresolved_questions=[], confidence_notes="x", citations=[],
    )
    assert m.bull_weight is None
    assert m.company_name is None
