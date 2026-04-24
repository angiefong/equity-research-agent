from unittest.mock import patch, MagicMock
from backend.agents.supervisor import supervisor_agent

def _base_state():
    return {
        "query": "Build a bull and bear case for AAPL",
        "ticker": "AAPL",
        "evidence": [],
        "bull_points": [],
        "bear_points": [],
        "evidence_contradictions": [],
        "debate_contradictions": [],
        "verification_issues": [],
        "thesis_snapshot_prior": None,
        "thesis_snapshot_current": None,
        "thesis_delta": None,
        "final_memo": None,
        "reroute_count_total": 0,
        "reroute_targets": [],
        "verification_status": "pending",
    }

def test_supervisor_classifies_bull_bear():
    mock_output = MagicMock()
    mock_output.query_type = "bull_bear"
    with patch("backend.agents.supervisor.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_output
        result = supervisor_agent(_base_state())
    assert result["query_type"] == "bull_bear"

def test_supervisor_classifies_thesis_drift():
    mock_output = MagicMock()
    mock_output.query_type = "thesis_drift"
    with patch("backend.agents.supervisor.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_output
        state = _base_state()
        state["query"] = "How has the AAPL thesis changed since last run?"
        result = supervisor_agent(state)
    assert result["query_type"] == "thesis_drift"

from backend.schemas.evidence import EvidenceSpan

def _mock_spans(n=2, agent="market_data"):
    return [
        EvidenceSpan(text=f"span {i}", source_ref=f"market:AAPL:field-{i}", agent_origin=agent)
        for i in range(n)
    ]

def test_market_data_agent_returns_evidence():
    from backend.agents.market_data import market_data_agent
    with patch("backend.agents.market_data.get_market_data_evidence", return_value=_mock_spans(3)):
        result = market_data_agent(_base_state())
    assert "evidence" in result
    assert len(result["evidence"]) == 3

def test_filings_agent_returns_evidence():
    from backend.agents.filings import filings_agent
    with patch("backend.agents.filings.fetch_recent_filings", return_value=_mock_spans(2, "filings")):
        result = filings_agent(_base_state())
    assert len(result["evidence"]) == 2

def test_news_agent_returns_evidence():
    from backend.agents.news import news_agent
    with patch("backend.agents.news.get_news_evidence", return_value=_mock_spans(3, "news")):
        result = news_agent(_base_state())
    assert len(result["evidence"]) == 3

def test_quant_data_agent_returns_evidence():
    from backend.agents.quant_data import quant_data_agent
    with patch("backend.agents.quant_data.compute_returns", return_value=_mock_spans(1, "quant_data")[0]), \
         patch("backend.agents.quant_data.compute_volatility", return_value=_mock_spans(1, "quant_data")[0]), \
         patch("backend.agents.quant_data.fetch_peer_comps", return_value=_mock_spans(3, "quant_data")):
        result = quant_data_agent(_base_state())
    assert len(result["evidence"]) >= 2
