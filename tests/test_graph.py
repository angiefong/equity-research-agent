from unittest.mock import patch, MagicMock
from backend.schemas.memo import ResearchMemo

def _mock_agent(return_value: dict):
    def agent(state):
        return return_value
    return agent

def _make_memo():
    return ResearchMemo(
        ticker="AAPL", research_summary="s", bull_case="b", bear_case="b",
        moderator_synthesis="m", contradictions_detected=[], unresolved_questions=[],
        thesis_drift_summary=None, confidence_notes="c", citations=[],
    )

def test_graph_runs_to_completion():
    from backend.graph.builder import build_graph
    from backend.schemas.evidence import EvidenceSpan
    from backend.schemas.thesis import ThesisSnapshot

    mock_span = EvidenceSpan(text="x", source_ref="market:AAPL:price", agent_origin="market_data")
    mock_memo = _make_memo()
    mock_snapshot = ThesisSnapshot(ticker="AAPL", bull_points=[], bear_points=[], confidence_by_topic={})

    from contextlib import ExitStack
    patches = {
        "backend.agents.supervisor.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(query_type="bull_bear")))),
        "backend.agents.market_data.get_market_data_evidence": MagicMock(return_value=[mock_span]),
        "backend.agents.filings.fetch_recent_filings": MagicMock(return_value=[mock_span]),
        "backend.agents.news.get_news_evidence": MagicMock(return_value=[mock_span]),
        "backend.agents.quant_data.compute_returns": MagicMock(return_value=mock_span),
        "backend.agents.quant_data.compute_volatility": MagicMock(return_value=mock_span),
        "backend.agents.quant_data.fetch_peer_comps": MagicMock(return_value=[]),
        "backend.agents.quant_interpretation.compute_pe_ratio": MagicMock(return_value=mock_span),
        "backend.agents.quant_interpretation.compute_ev_ebitda": MagicMock(return_value=mock_span),
        "backend.agents.quant_interpretation.generate_price_chart": MagicMock(return_value=mock_span),
        "backend.agents.evidence_contradiction.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(contradictions=[])))),
        "backend.agents.bull.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(debate_points=[])))),
        "backend.agents.bear.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(debate_points=[])))),
        "backend.agents.debate_contradiction.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(contradictions=[])))),
        "backend.agents.verifier.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(issues=[])))),
        "backend.agents.thesis_replay.load_latest_snapshot": MagicMock(return_value=None),
        "backend.agents.moderator.get_structured_llm": MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=MagicMock(memo=mock_memo)))),
        "backend.agents.moderator.save_snapshot": MagicMock(),
    }

    with ExitStack() as stack:
        for target, mock_val in patches.items():
            stack.enter_context(patch(target, mock_val))
        graph = build_graph()
        result = graph.invoke({"query": "Bull case for AAPL", "ticker": "AAPL"})

    assert result["final_memo"] is not None
    assert result["final_memo"].ticker == "AAPL"
