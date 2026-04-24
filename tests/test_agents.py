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
