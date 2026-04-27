from backend.tools.source_ref import format_source_ref, parse_source_ref, render_source_ref, validate_source_ref

def test_format_round_trip():
    ref = format_source_ref("sec", "AAPL-10K-2024", "risk_factors")
    parsed = parse_source_ref(ref)
    assert parsed.source_type == "sec"
    assert parsed.identifier == "AAPL-10K-2024"
    assert parsed.section == "risk_factors"

def test_format_rejects_colon_in_parts():
    import pytest
    with pytest.raises(ValueError):
        format_source_ref("sec", "AAPL:10K", "section")

def test_parse_rejects_wrong_segment_count():
    import pytest
    with pytest.raises(ValueError):
        parse_source_ref("sec:AAPL")

def test_validate_known_source_types():
    assert validate_source_ref("sec:AAPL-10K-2024:risk_factors") is True
    assert validate_source_ref("market:AAPL-price:90d-history") is True
    assert validate_source_ref("news:tavily-article:2024-01-15") is True
    assert validate_source_ref("quant:AAPL-ratios:pe-ratio") is True

def test_validate_unknown_source_type():
    assert validate_source_ref("unknown:foo:bar") is False

def test_render_sec():
    label = render_source_ref("sec:AAPL-10K-2024:risk_factors")
    assert "SEC Filing" in label
    assert "risk_factors" in label

def test_render_market():
    label = render_source_ref("market:AAPL-price:90d-history")
    assert "Market Data" in label
