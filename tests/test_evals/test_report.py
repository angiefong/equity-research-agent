from backend.evals import report
from backend.evals.rubric import (
    EvidenceEval,
    FullEval,
    MemoEval,
    MetricScore,
)


def _full(memo_score: int = 4, evidence_score: int = 3, missing: list[str] = None) -> FullEval:
    return FullEval(
        evidence=EvidenceEval(
            evidence_coverage=MetricScore(score=evidence_score, rationale="r"),
            missing_items=missing or [],
        ),
        memo=MemoEval(
            insight=MetricScore(score=memo_score, rationale="r"),
            factual_accuracy=MetricScore(score=memo_score, rationale="r"),
            logical_consistency=MetricScore(score=memo_score, rationale="r"),
            causal_reasoning=MetricScore(score=memo_score, rationale="r"),
            synthesis_quality=MetricScore(score=memo_score, rationale="r"),
            data_integrity=MetricScore(score=memo_score, rationale="r"),
            agent_coordination=MetricScore(score=memo_score, rationale="r"),
            overall_comment="x",
        ),
    )


def test_build_summary_renders_table_with_no_baseline():
    per_ticker = {
        "AAPL": _full(memo_score=4, evidence_score=3, missing=["China geo"]),
        "RIVN": _full(memo_score=2, evidence_score=2, missing=["delivery guidance"]),
    }
    md = report.build_summary(
        per_ticker=per_ticker,
        baseline_avgs=None,
        run_meta={"branch": "feature/x", "epoch": "2026-Q2",
                  "judge_model": "claude-sonnet-4-6",
                  "agent_model": "llama-3.1-8b-instant",
                  "ticker_set": "quick", "dagshub_url": "https://example/"},
    )
    assert "Eval Run" in md
    assert "Establishing baseline" in md
    assert "AAPL" in md and "RIVN" in md
    assert "China geo" in md
    assert "delivery guidance" in md


def test_build_summary_renders_deltas_with_baseline():
    per_ticker = {"AAPL": _full(memo_score=4, evidence_score=4)}
    md = report.build_summary(
        per_ticker=per_ticker,
        baseline_avgs={
            "avg_evidence_coverage": 3.0,
            "avg_insight": 3.0,
            "avg_factual_accuracy": 3.0,
            "avg_logical_consistency": 3.0,
            "avg_causal_reasoning": 3.0,
            "avg_synthesis_quality": 3.0,
            "avg_data_integrity": 3.0,
            "avg_agent_coordination": 3.0,
            "avg_overall_memo": 3.0,
        },
        run_meta={"branch": "feature/x", "epoch": "2026-Q2",
                  "judge_model": "claude-sonnet-4-6",
                  "agent_model": "llama-3.1-8b-instant",
                  "ticker_set": "quick", "dagshub_url": "https://example/"},
    )
    assert "+1.0" in md   # delta
    assert "✅" in md or "+" in md


def test_build_summary_includes_failed_tickers():
    per_ticker = {
        "AAPL": _full(memo_score=4),
        "RIVN": None,   # failed
    }
    md = report.build_summary(
        per_ticker=per_ticker,
        baseline_avgs=None,
        run_meta={"branch": "x", "epoch": "2026-Q2",
                  "judge_model": "x", "agent_model": "x",
                  "ticker_set": "quick", "dagshub_url": ""},
    )
    assert "❌" in md
    assert "RIVN" in md


def test_regression_check_flags_drop_above_threshold():
    over = report.exceeds_regression(
        avg_overall=2.5, baseline_overall=3.0, threshold=0.3
    )
    assert over is True


def test_regression_check_passes_within_threshold():
    over = report.exceeds_regression(
        avg_overall=2.85, baseline_overall=3.0, threshold=0.3
    )
    assert over is False


def test_regression_check_no_baseline_returns_false():
    assert report.exceeds_regression(
        avg_overall=2.0, baseline_overall=None, threshold=0.3
    ) is False
