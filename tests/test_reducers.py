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


from backend.graph.state import AgentState, InputState, OutputState

def test_input_state_shape():
    state: InputState = {"query": "Build a bull case for AAPL", "ticker": "AAPL"}
    assert state["ticker"] == "AAPL"

def test_agent_state_has_required_keys():
    import typing
    hints = typing.get_type_hints(AgentState)
    for key in [
        "query", "ticker", "evidence", "bull_points", "bear_points",
        "evidence_contradictions", "debate_contradictions", "verification_issues",
        "thesis_snapshot_prior", "thesis_snapshot_current", "thesis_delta",
        "final_memo", "reroute_count_total", "reroute_targets", "verification_status",
    ]:
        assert key in hints, f"Missing key: {key}"

def test_output_state_shape():
    import typing
    hints = typing.get_type_hints(OutputState)
    assert "final_memo" in hints
    assert "thesis_delta" in hints
