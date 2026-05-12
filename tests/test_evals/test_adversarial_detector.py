from backend.evals.adversarial import CatchBreakdown, compute_catch_breakdown
from backend.schemas.contradiction import ContradictionSeverity
from backend.schemas.debate import DebatePoint, DebateSide
from backend.schemas.memo import ResearchMemo
from backend.schemas.verification import VerificationIssue, VerificationIssueType


POISONED = "news:tavily-attacker:2026-05-09"


def _point(side, source_refs, claim="c"):
    return DebatePoint(
        side=side, claim=claim, rationale="r", confidence=0.5,
        evidence_span_ids=source_refs,
    )


def _vi(target_agent, claim="c"):
    return VerificationIssue(
        claim=claim,
        issue_type=VerificationIssueType.UNSUPPORTED_CLAIM,
        severity=ContradictionSeverity.HIGH,
        suggested_action="re-fetch",
        target_agent=target_agent,
    )


def _memo(citations):
    return ResearchMemo(
        ticker="AAPL", research_summary="s", bull_case="b", bear_case="b",
        moderator_synthesis="m", contradictions_detected=[], unresolved_questions=[],
        thesis_drift_summary=None, confidence_notes="c", citations=citations,
    )


def test_full_defense_when_nothing_references_poisoned_span():
    state = {
        "bull_points": [_point(DebateSide.BULL, ["news:tavily-legit:2026-05-08"])],
        "bear_points": [_point(DebateSide.BEAR, ["news:tavily-legit:2026-05-08"])],
        "verification_issues": [],
        "final_memo": _memo(["news:tavily-legit:2026-05-08"]),
    }
    cb = compute_catch_breakdown(state, POISONED, judge_absorbed=False)
    assert cb.agent_refused is True
    assert cb.citation_layer_caught is True
    assert cb.verifier_flagged is False
    assert cb.absorbed is False
    assert cb.caught is True


def test_verifier_flagged_when_news_target_issue_exists():
    state = {
        "bull_points": [_point(DebateSide.BULL, [POISONED])],
        "bear_points": [],
        "verification_issues": [_vi(target_agent="news")],
        "final_memo": _memo([POISONED]),
    }
    cb = compute_catch_breakdown(state, POISONED, judge_absorbed=False)
    assert cb.verifier_flagged is True
    assert cb.agent_refused is False
    assert cb.citation_layer_caught is False


def test_verifier_not_flagged_for_unrelated_target():
    state = {
        "bull_points": [],
        "bear_points": [],
        "verification_issues": [_vi(target_agent="market_data")],
        "final_memo": _memo([]),
    }
    cb = compute_catch_breakdown(state, POISONED, judge_absorbed=False)
    assert cb.verifier_flagged is False


def test_absorbed_is_set_from_judge_verdict():
    state = {
        "bull_points": [],
        "bear_points": [],
        "verification_issues": [],
        "final_memo": _memo([]),
    }
    cb = compute_catch_breakdown(state, POISONED, judge_absorbed=True)
    assert cb.absorbed is True
    assert cb.caught is False


def test_handles_missing_state_keys():
    cb = compute_catch_breakdown({}, POISONED, judge_absorbed=False)
    assert cb.agent_refused is True  # nothing cited it
    assert cb.citation_layer_caught is True  # no memo, no citations
    assert cb.verifier_flagged is False
    assert cb.absorbed is False


def test_accepts_dict_state_shape():
    """LangGraph may hand us state as a dict-of-dicts after model_dump()."""
    state = {
        "bull_points": [{"side": "bull", "claim": "c", "rationale": "r",
                         "confidence": 0.5, "evidence_span_ids": [POISONED]}],
        "bear_points": [],
        "verification_issues": [{"claim": "c", "issue_type": "unsupported_claim",
                                  "severity": "high", "suggested_action": "x",
                                  "target_agent": "news"}],
        "final_memo": {"citations": [POISONED]},
    }
    cb = compute_catch_breakdown(state, POISONED, judge_absorbed=False)
    assert cb.verifier_flagged is True
    assert cb.agent_refused is False
    assert cb.citation_layer_caught is False
