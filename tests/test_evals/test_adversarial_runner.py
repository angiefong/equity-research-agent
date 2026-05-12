"""Integration test for run_adversarial_case — mocks the graph + judge."""
from unittest.mock import MagicMock, patch

from backend.evals.adversarial import (
    AdversarialFixture,
    AdversarialJudgment,
    AdversarialSpan,
    run_adversarial_case,
)
from backend.schemas.debate import DebatePoint, DebateSide
from backend.schemas.memo import ResearchMemo


def _fixture(poisoned_ref="news:tavily-attacker:2026-05-09"):
    return AdversarialFixture(
        case_id="t",
        ticker="AAPL",
        category="explicit_instruction",
        description="test injection",
        legitimate_news_spans=[AdversarialSpan(text="legit", source_ref="news:legit:2026-05-08")],
        poisoned_news_span=AdversarialSpan(text="EVIL", source_ref=poisoned_ref),
        success_markers=["MARK"],
    )


def _stub_state(poisoned_ref, *, bull_cites_poison=False, citations_include_poison=False, news_verifier_flag=False):
    bull_evidence = [poisoned_ref] if bull_cites_poison else ["news:legit:2026-05-08"]
    memo_citations = [poisoned_ref] if citations_include_poison else ["news:legit:2026-05-08"]
    return {
        "bull_points": [DebatePoint(
            side=DebateSide.BULL, claim="c", rationale="r", confidence=0.5,
            evidence_span_ids=bull_evidence,
        )],
        "bear_points": [],
        "verification_issues": [
            MagicMock(target_agent="news")
        ] if news_verifier_flag else [],
        "final_memo": ResearchMemo(
            ticker="AAPL", research_summary="s", bull_case="b", bear_case="b",
            moderator_synthesis="m", contradictions_detected=[], unresolved_questions=[],
            thesis_drift_summary=None, confidence_notes="c", citations=memo_citations,
        ),
    }


def _fake_graph_factory(state):
    def factory(checkpointer=None):
        g = MagicMock()
        g.invoke = MagicMock()
        gs = MagicMock()
        gs.values = state
        g.get_state = MagicMock(return_value=gs)
        return g
    return factory


def test_run_case_clean_defense_returns_caught(tmp_path):
    fx = _fixture()
    state = _stub_state(fx.poisoned_news_span.source_ref)
    judge = MagicMock(return_value=AdversarialJudgment(absorbed=False, rationale="ok"))
    with patch("backend.evals.snapshot.epoch_snapshot") as snap:
        snap.return_value.__enter__ = MagicMock(return_value=tmp_path)
        snap.return_value.__exit__ = MagicMock(return_value=False)
        result = run_adversarial_case(
            fx, judge_fn=judge,
            graph_factory=_fake_graph_factory(state),
        )
    assert result.case_id == "t"
    assert result.judgment.absorbed is False
    assert result.breakdown.absorbed is False
    assert result.breakdown.agent_refused is True
    assert result.breakdown.citation_layer_caught is True
    assert result.breakdown.caught is True
    judge.assert_called_once()
    args = judge.call_args.kwargs
    assert args["injection_description"] == "test injection"
    assert "news:legit:2026-05-08" in args["legitimate_evidence_summary"]


def test_run_case_propagates_breakdown_when_verifier_flags(tmp_path):
    fx = _fixture()
    state = _stub_state(
        fx.poisoned_news_span.source_ref,
        bull_cites_poison=True,
        citations_include_poison=True,
        news_verifier_flag=True,
    )
    judge = MagicMock(return_value=AdversarialJudgment(absorbed=False, rationale="caught"))
    with patch("backend.evals.snapshot.epoch_snapshot") as snap:
        snap.return_value.__enter__ = MagicMock(return_value=tmp_path)
        snap.return_value.__exit__ = MagicMock(return_value=False)
        result = run_adversarial_case(fx, judge_fn=judge, graph_factory=_fake_graph_factory(state))
    assert result.breakdown.verifier_flagged is True
    assert result.breakdown.agent_refused is False
    assert result.breakdown.citation_layer_caught is False


def test_run_case_handles_judge_failure(tmp_path):
    fx = _fixture()
    state = _stub_state(fx.poisoned_news_span.source_ref)
    judge = MagicMock(side_effect=RuntimeError("judge boom"))
    with patch("backend.evals.snapshot.epoch_snapshot") as snap:
        snap.return_value.__enter__ = MagicMock(return_value=tmp_path)
        snap.return_value.__exit__ = MagicMock(return_value=False)
        result = run_adversarial_case(fx, judge_fn=judge, graph_factory=_fake_graph_factory(state))
    assert "judge_failed" in (result.error or "")
    assert result.judgment.absorbed is False


def test_run_case_handles_no_memo(tmp_path):
    fx = _fixture()
    state = {"bull_points": [], "bear_points": [], "verification_issues": [], "final_memo": None}
    with patch("backend.evals.snapshot.epoch_snapshot") as snap:
        snap.return_value.__enter__ = MagicMock(return_value=tmp_path)
        snap.return_value.__exit__ = MagicMock(return_value=False)
        result = run_adversarial_case(fx, judge_fn=MagicMock(), graph_factory=_fake_graph_factory(state))
    assert result.error == "no_final_memo"


def test_run_case_handles_graph_exception(tmp_path):
    fx = _fixture()
    def bad_factory(checkpointer=None):
        g = MagicMock()
        g.invoke = MagicMock(side_effect=RuntimeError("graph boom"))
        return g
    with patch("backend.evals.snapshot.epoch_snapshot") as snap:
        snap.return_value.__enter__ = MagicMock(return_value=tmp_path)
        snap.return_value.__exit__ = MagicMock(return_value=False)
        result = run_adversarial_case(fx, judge_fn=MagicMock(), graph_factory=bad_factory)
    assert result.error and "RuntimeError" in result.error
