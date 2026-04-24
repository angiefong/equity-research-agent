from backend.graph.reducers import dedupe_by_id
from backend.schemas.evidence import EvidenceSpan

def _span(id: str, text: str) -> EvidenceSpan:
    s = EvidenceSpan(text=text, source_ref="market:AAPL:price", agent_origin="test")
    s.id = id
    return s

def test_dedupe_no_overlap():
    a = [_span("1", "first")]
    b = [_span("2", "second")]
    result = dedupe_by_id(a, b)
    assert len(result) == 2

def test_dedupe_removes_duplicate_id():
    a = [_span("1", "first")]
    b = [_span("1", "first-duplicate")]
    result = dedupe_by_id(a, b)
    assert len(result) == 1
    assert result[0].text == "first"

def test_dedupe_empty_existing():
    b = [_span("1", "only")]
    result = dedupe_by_id([], b)
    assert len(result) == 1

def test_dedupe_empty_new():
    a = [_span("1", "only")]
    result = dedupe_by_id(a, [])
    assert len(result) == 1

def test_dedupe_parallel_writes():
    market = [_span("m1", "price"), _span("m2", "financials")]
    filings = [_span("f1", "10-K"), _span("m1", "duplicate")]
    merged = dedupe_by_id(market, filings)
    assert len(merged) == 3
    ids = {s.id for s in merged}
    assert ids == {"m1", "m2", "f1"}
