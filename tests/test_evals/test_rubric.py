import pytest
from pydantic import ValidationError
from backend.evals.rubric import (
    MetricScore,
    EvidenceEval,
    MemoEval,
    FullEval,
    EVIDENCE_RUBRIC_TEXT,
    MEMO_RUBRIC_TEXT,
)


def test_metric_score_valid():
    s = MetricScore(score=4, rationale="solid causal chain on margin expansion")
    assert s.score == 4
    assert "causal" in s.rationale


def test_metric_score_rejects_out_of_range():
    with pytest.raises(ValidationError):
        MetricScore(score=6, rationale="x")
    with pytest.raises(ValidationError):
        MetricScore(score=-1, rationale="x")


def test_evidence_eval_shape():
    e = EvidenceEval(
        evidence_coverage=MetricScore(score=3, rationale="missing segment data"),
        missing_items=["Services growth rate", "China revenue trend"],
    )
    assert e.evidence_coverage.score == 3
    assert len(e.missing_items) == 2


def test_memo_eval_average_computes_seven_metrics():
    m = MemoEval(
        insight=MetricScore(score=3, rationale="r"),
        factual_accuracy=MetricScore(score=4, rationale="r"),
        logical_consistency=MetricScore(score=4, rationale="r"),
        causal_reasoning=MetricScore(score=3, rationale="r"),
        synthesis_quality=MetricScore(score=3, rationale="r"),
        data_integrity=MetricScore(score=5, rationale="r"),
        agent_coordination=MetricScore(score=4, rationale="r"),
        overall_comment="solid",
    )
    assert m.average == pytest.approx((3 + 4 + 4 + 3 + 3 + 5 + 4) / 7)


def test_full_eval_holds_both():
    full = FullEval(
        evidence=EvidenceEval(
            evidence_coverage=MetricScore(score=3, rationale="r"),
            missing_items=[],
        ),
        memo=MemoEval(
            insight=MetricScore(score=3, rationale="r"),
            factual_accuracy=MetricScore(score=3, rationale="r"),
            logical_consistency=MetricScore(score=3, rationale="r"),
            causal_reasoning=MetricScore(score=3, rationale="r"),
            synthesis_quality=MetricScore(score=3, rationale="r"),
            data_integrity=MetricScore(score=3, rationale="r"),
            agent_coordination=MetricScore(score=3, rationale="r"),
            overall_comment="x",
        ),
    )
    assert full.evidence.evidence_coverage.score == 3
    assert full.memo.average == 3.0


def test_rubric_text_constants_present_and_nontrivial():
    assert "evidence" in EVIDENCE_RUBRIC_TEXT.lower()
    assert "0" in EVIDENCE_RUBRIC_TEXT and "5" in EVIDENCE_RUBRIC_TEXT
    for metric in [
        "insight",
        "factual",
        "logical",
        "causal",
        "synthesis",
        "data integrity",
        "agent coordination",
    ]:
        assert metric in MEMO_RUBRIC_TEXT.lower(), f"missing {metric} in rubric"
