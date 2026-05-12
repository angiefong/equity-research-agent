from unittest.mock import MagicMock, patch
import pytest
from backend.evals import tracking
from backend.evals.rubric import (
    EvidenceEval,
    FullEval,
    MemoEval,
    MetricScore,
)


def _make_full_eval(memo_avg: float = 3.5) -> FullEval:
    return FullEval(
        evidence=EvidenceEval(
            evidence_coverage=MetricScore(score=3, rationale="r"),
            missing_items=["x"],
        ),
        memo=MemoEval(
            insight=MetricScore(score=int(memo_avg), rationale="r"),
            factual_accuracy=MetricScore(score=int(memo_avg), rationale="r"),
            logical_consistency=MetricScore(score=int(memo_avg), rationale="r"),
            causal_reasoning=MetricScore(score=int(memo_avg), rationale="r"),
            synthesis_quality=MetricScore(score=int(memo_avg), rationale="r"),
            data_integrity=MetricScore(score=int(memo_avg), rationale="r"),
            agent_coordination=MetricScore(score=int(memo_avg), rationale="r"),
            overall_comment="x",
        ),
    )


def test_metric_dict_for_ticker_has_eight_keys():
    full = _make_full_eval()
    metrics = tracking.metric_dict_for_ticker(full)
    expected = {
        "evidence_coverage", "insight", "factual_accuracy",
        "logical_consistency", "causal_reasoning", "synthesis_quality",
        "data_integrity", "agent_coordination", "overall_memo",
    }
    assert set(metrics.keys()) == expected


def test_aggregate_averages_skip_failed_tickers():
    full_a = _make_full_eval(memo_avg=4)
    metrics_a = tracking.metric_dict_for_ticker(full_a)
    full_b = _make_full_eval(memo_avg=2)
    metrics_b = tracking.metric_dict_for_ticker(full_b)

    avg = tracking.aggregate_averages([metrics_a, metrics_b, None])
    assert avg["avg_overall_memo"] == pytest.approx(3.0)
    assert avg["n_tickers_succeeded"] == 2
    assert avg["n_tickers_failed"] == 1


def test_setup_tracking_sets_auth_when_uri_is_explicit_dagshub(monkeypatch):
    """Regression: prior code only set HTTP basic auth on the fallback path.
    When MLFLOW_TRACKING_URI was explicitly set in .env (to the same DagsHub URL),
    requests went out unauthenticated and got 403."""
    monkeypatch.delenv("MLFLOW_TRACKING_USERNAME", raising=False)
    monkeypatch.delenv("MLFLOW_TRACKING_PASSWORD", raising=False)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://dagshub.com/me/repo.mlflow")
    monkeypatch.setenv("DAGSHUB_REPO_OWNER", "me")
    monkeypatch.setenv("DAGSHUB_REPO_NAME", "repo")
    monkeypatch.setenv("DAGSHUB_TOKEN", "tok")
    with patch.object(tracking.mlflow, "set_tracking_uri"), \
         patch.object(tracking.mlflow, "set_experiment"):
        tracking.setup_tracking()
    import os
    assert os.environ["MLFLOW_TRACKING_USERNAME"] == "me"
    assert os.environ["MLFLOW_TRACKING_PASSWORD"] == "tok"


def test_setup_tracking_does_not_set_auth_for_non_dagshub_uri(monkeypatch):
    monkeypatch.delenv("MLFLOW_TRACKING_USERNAME", raising=False)
    monkeypatch.delenv("MLFLOW_TRACKING_PASSWORD", raising=False)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    monkeypatch.setenv("DAGSHUB_REPO_OWNER", "me")
    monkeypatch.setenv("DAGSHUB_TOKEN", "tok")
    with patch.object(tracking.mlflow, "set_tracking_uri"), \
         patch.object(tracking.mlflow, "set_experiment"):
        tracking.setup_tracking()
    import os
    assert "MLFLOW_TRACKING_USERNAME" not in os.environ
    assert "MLFLOW_TRACKING_PASSWORD" not in os.environ


def test_find_baseline_run_returns_none_when_no_runs(monkeypatch):
    fake_client = MagicMock()
    fake_client.search_runs.return_value = []
    monkeypatch.setattr(tracking, "_mlflow_client", lambda: fake_client)
    out = tracking.find_baseline_run(
        experiment_name="test", branch="main", epoch="2026-Q2", ticker_set="quick"
    )
    assert out is None


def test_find_baseline_run_returns_most_recent(monkeypatch):
    fake_run = MagicMock()
    fake_run.data.metrics = {"avg_overall_memo": 3.2}
    fake_run.info.run_id = "abc123"

    fake_client = MagicMock()
    fake_client.search_runs.return_value = [fake_run]
    monkeypatch.setattr(tracking, "_mlflow_client", lambda: fake_client)

    out = tracking.find_baseline_run(
        experiment_name="test", branch="main", epoch="2026-Q2", ticker_set="quick"
    )
    assert out is fake_run
