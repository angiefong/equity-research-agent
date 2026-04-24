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

def test_quant_interpretation_agent_returns_evidence():
    from backend.agents.quant_interpretation import quant_interpretation_agent
    from backend.schemas.evidence import EvidenceSpan
    mock_span = EvidenceSpan(text="P/E 28.5", source_ref="quant:AAPL-ratios:pe-ratio", agent_origin="quant_interpretation")
    with patch("backend.agents.quant_interpretation.compute_pe_ratio", return_value=mock_span), \
         patch("backend.agents.quant_interpretation.compute_ev_ebitda", return_value=mock_span), \
         patch("backend.agents.quant_interpretation.generate_price_chart", return_value=mock_span):
        result = quant_interpretation_agent(_base_state())
    assert len(result["evidence"]) == 3
    assert all(s.agent_origin == "quant_interpretation" for s in result["evidence"])

from backend.schemas.contradiction import Contradiction, ContradictionSeverity

def test_evidence_contradiction_agent_returns_contradictions():
    from backend.agents.evidence_contradiction import evidence_contradiction_agent
    from pydantic import BaseModel

    class MockOutput(BaseModel):
        contradictions: list[Contradiction]

    mock_output = MockOutput(contradictions=[
        Contradiction(
            claim_a="Revenue grew 10%",
            claim_b="Revenue declined 2%",
            source_refs=["sec:AAPL-10K-2024:revenue", "news:tavily-article:2024-01"],
            severity=ContradictionSeverity.HIGH,
            rationale="Direct numeric conflict",
        )
    ])
    state = _base_state()
    state["evidence"] = [
        EvidenceSpan(text="Revenue grew 10%", source_ref="sec:AAPL-10K-2024:revenue", agent_origin="filings"),
        EvidenceSpan(text="Revenue declined 2%", source_ref="news:tavily-article:2024-01", agent_origin="news"),
    ]
    with patch("backend.agents.evidence_contradiction.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_output
        result = evidence_contradiction_agent(state)
    assert "evidence_contradictions" in result
    assert len(result["evidence_contradictions"]) == 1
    assert result["evidence_contradictions"][0].severity == ContradictionSeverity.HIGH

from backend.schemas.debate import DebatePoint, DebateSide

def _mock_debate_output(side: str):
    from pydantic import BaseModel
    class MockOut(BaseModel):
        debate_points: list[DebatePoint]
    return MockOut(debate_points=[
        DebatePoint(
            side=DebateSide.BULL if side == "bull" else DebateSide.BEAR,
            claim="Services revenue accelerating",
            evidence_span_ids=["e1"],
            confidence=0.85,
            rationale="Services grew 14% YoY driven by App Store",
        )
    ])

def test_bull_agent_returns_bull_points():
    from backend.agents.bull import bull_agent
    with patch("backend.agents.bull.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = _mock_debate_output("bull")
        result = bull_agent(_base_state())
    assert "bull_points" in result
    assert result["bull_points"][0].side == DebateSide.BULL

def test_bear_agent_returns_bear_points():
    from backend.agents.bear import bear_agent
    with patch("backend.agents.bear.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = _mock_debate_output("bear")
        result = bear_agent(_base_state())
    assert "bear_points" in result
    assert result["bear_points"][0].side == DebateSide.BEAR

def test_debate_contradiction_agent_detects_conflict():
    from backend.agents.debate_contradiction import debate_contradiction_agent
    from pydantic import BaseModel

    class MockOut(BaseModel):
        contradictions: list[Contradiction]

    mock_out = MockOut(contradictions=[
        Contradiction(
            claim_a="Bull: Services revenue will double",
            claim_b="Bear: Services growth already plateauing",
            source_refs=["quant:AAPL-ratios:pe-ratio"],
            severity=ContradictionSeverity.MEDIUM,
            rationale="Conflicting views on services trajectory",
        )
    ])
    state = _base_state()
    state["bull_points"] = [DebatePoint(side=DebateSide.BULL, claim="Services will double", evidence_span_ids=[], confidence=0.8, rationale="growth")]
    state["bear_points"] = [DebatePoint(side=DebateSide.BEAR, claim="Services plateauing", evidence_span_ids=[], confidence=0.7, rationale="slowdown")]
    with patch("backend.agents.debate_contradiction.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = mock_out
        result = debate_contradiction_agent(state)
    assert len(result["debate_contradictions"]) == 1

from backend.schemas.verification import VerificationIssue, VerificationIssueType

def test_verifier_sets_pass_when_no_issues():
    from backend.agents.verifier import verifier_agent
    from pydantic import BaseModel

    class MockOut(BaseModel):
        issues: list[VerificationIssue]

    with patch("backend.agents.verifier.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = MockOut(issues=[])
        result = verifier_agent(_base_state())
    assert result["verification_status"] == "pass"
    assert result["reroute_targets"] == []

def test_verifier_sets_needs_reroute_on_high_severity():
    from backend.agents.verifier import verifier_agent
    from pydantic import BaseModel

    class MockOut(BaseModel):
        issues: list[VerificationIssue]

    high_issue = VerificationIssue(
        claim="EPS grew 50%",
        issue_type=VerificationIssueType.NUMERIC_MISMATCH,
        severity=ContradictionSeverity.HIGH,
        suggested_action="Re-fetch earnings from EDGAR",
        target_agent="filings",
    )
    with patch("backend.agents.verifier.get_structured_llm") as mock_llm:
        mock_llm.return_value.invoke.return_value = MockOut(issues=[high_issue])
        result = verifier_agent(_base_state())
    assert result["verification_status"] == "needs_reroute"
    assert "filings" in result["reroute_targets"]

def test_thesis_replay_returns_none_on_first_run():
    from backend.agents.thesis_replay import thesis_replay_agent
    from backend.schemas.debate import DebatePoint, DebateSide
    state = _base_state()
    state["bull_points"] = []
    state["bear_points"] = []
    with patch("backend.agents.thesis_replay.load_latest_snapshot", return_value=None):
        result = thesis_replay_agent(state)
    assert result["thesis_snapshot_prior"] is None
    assert result["thesis_delta"] is None

def test_thesis_replay_computes_delta_on_second_run():
    from backend.agents.thesis_replay import thesis_replay_agent
    from backend.schemas.thesis import ThesisSnapshot
    from backend.schemas.debate import DebatePoint, DebateSide
    prior = ThesisSnapshot(
        ticker="AAPL",
        bull_points=[DebatePoint(side=DebateSide.BULL, claim="Old bull claim", evidence_span_ids=[], confidence=0.7, rationale="old")],
        bear_points=[],
        confidence_by_topic={"growth": 0.6},
    )
    state = _base_state()
    state["bull_points"] = [DebatePoint(side=DebateSide.BULL, claim="New bull claim", evidence_span_ids=[], confidence=0.9, rationale="new")]
    state["bear_points"] = []
    with patch("backend.agents.thesis_replay.load_latest_snapshot", return_value=prior):
        result = thesis_replay_agent(state)
    assert result["thesis_snapshot_prior"] is not None
    assert result["thesis_delta"] is not None
    assert "New bull claim" in result["thesis_delta"].new
    assert "Old bull claim" in result["thesis_delta"].disappeared

from backend.schemas.memo import ResearchMemo

def test_moderator_produces_memo_first_run():
    from backend.agents.moderator import moderator_agent
    mock_memo = ResearchMemo(
        ticker="AAPL",
        research_summary="Strong services growth",
        bull_case="Services margin expansion",
        bear_case="Hardware saturation",
        moderator_synthesis="Balanced outlook",
        contradictions_detected=[],
        unresolved_questions=["Will China recover?"],
        thesis_drift_summary=None,
        confidence_notes="High confidence",
        citations=["sec:AAPL-10K-2024:revenue"],
    )
    from pydantic import BaseModel
    class MockOut(BaseModel):
        memo: ResearchMemo
    with patch("backend.agents.moderator.get_structured_llm") as mock_llm, \
         patch("backend.agents.moderator.save_snapshot"):
        mock_llm.return_value.invoke.return_value = MockOut(memo=mock_memo)
        result = moderator_agent(_base_state())
    assert "final_memo" in result
    assert result["final_memo"].thesis_drift_summary is None
    assert "thesis_snapshot_current" in result

def test_moderator_includes_drift_on_second_run():
    from backend.agents.moderator import moderator_agent
    from backend.schemas.thesis import ThesisDelta
    state = _base_state()
    state["thesis_delta"] = ThesisDelta(
        ticker="AAPL", previous_run_id="p", current_run_id="c",
        strengthened=["Services"], weakened=[], new=[], disappeared=[], confidence_drift=[],
    )
    mock_memo = ResearchMemo(
        ticker="AAPL", research_summary="x", bull_case="x", bear_case="x",
        moderator_synthesis="x", contradictions_detected=[], unresolved_questions=[],
        thesis_drift_summary="Services thesis strengthened",
        confidence_notes="High", citations=[],
    )
    from pydantic import BaseModel
    class MockOut(BaseModel):
        memo: ResearchMemo
    with patch("backend.agents.moderator.get_structured_llm") as mock_llm, \
         patch("backend.agents.moderator.save_snapshot"):
        mock_llm.return_value.invoke.return_value = MockOut(memo=mock_memo)
        result = moderator_agent(state)
    assert result["final_memo"].thesis_drift_summary is not None

def test_reroute_agent_fetches_targeted_agent():
    from backend.agents.reroute import reroute_agent
    from backend.schemas.evidence import EvidenceSpan
    state = _base_state()
    state["reroute_targets"] = ["filings"]
    state["reroute_count_total"] = 0
    mock_span = EvidenceSpan(text="New filing data", source_ref="sec:AAPL-10Q-2024:revenue", agent_origin="filings")
    with patch("backend.agents.reroute.fetch_recent_filings", return_value=[mock_span]):
        result = reroute_agent(state)
    assert result["reroute_count_total"] == 1
    assert result["verification_status"] == "pending"
    assert len(result["evidence"]) == 1
