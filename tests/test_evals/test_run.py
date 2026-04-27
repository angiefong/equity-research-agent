from unittest.mock import MagicMock, patch
import pytest
from backend.evals import run as run_module
from backend.evals.rubric import (
    EvidenceEval,
    FullEval,
    MemoEval,
    MetricScore,
)


def _stub_full_eval() -> FullEval:
    return FullEval(
        evidence=EvidenceEval(
            evidence_coverage=MetricScore(score=4, rationale="r"),
            missing_items=[],
        ),
        memo=MemoEval(
            insight=MetricScore(score=4, rationale="r"),
            factual_accuracy=MetricScore(score=4, rationale="r"),
            logical_consistency=MetricScore(score=4, rationale="r"),
            causal_reasoning=MetricScore(score=4, rationale="r"),
            synthesis_quality=MetricScore(score=4, rationale="r"),
            data_integrity=MetricScore(score=4, rationale="r"),
            agent_coordination=MetricScore(score=4, rationale="r"),
            overall_comment="x",
        ),
    )


@pytest.fixture(autouse=True)
def stub_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_KEY", "stub")
    monkeypatch.setenv("GROQ_KEY", "stub")


class _StubTickerCtx:
    def __enter__(self):
        return MagicMock()

    def __exit__(self, *a):
        return False


@pytest.fixture(autouse=True)
def stub_mlflow(monkeypatch, tmp_path):
    """Prevent all real MLflow I/O in every test in this module."""
    monkeypatch.setattr(run_module.mlflow, "log_metrics", lambda *a, **k: None)
    monkeypatch.setattr(run_module.mlflow, "log_artifacts", lambda *a, **k: None)
    monkeypatch.setattr(run_module.mlflow, "log_artifact", lambda *a, **k: None)
    monkeypatch.setattr(run_module.mlflow, "set_tag", lambda *a, **k: None)
    monkeypatch.setattr(run_module.tracking, "ticker_run",
                        lambda ticker: _StubTickerCtx())
    monkeypatch.setattr(run_module.tracking, "find_baseline_run",
                        lambda *a, **k: None)
    monkeypatch.setattr(run_module, "RUNTIME_ROOT", tmp_path)


def test_run_quick_invokes_pipeline_per_ticker(monkeypatch, tmp_path):
    pipeline_calls = []

    def fake_run_pipeline(ticker, epoch):
        pipeline_calls.append(ticker)
        from backend.schemas.memo import ResearchMemo
        from backend.schemas.evidence import EvidenceSpan
        fake_memo = ResearchMemo(
            ticker=ticker,
            research_summary=f"test summary for {ticker}",
            bull_case="bull",
            bear_case="bear",
            moderator_synthesis="synthesis",
            contradictions_detected=[],
            unresolved_questions=[],
            confidence_notes="notes",
            citations=[],
        )
        fake_evidence = [EvidenceSpan(source_ref="news:tavily:test", text="x", agent_origin="news")]
        return {"final_memo": fake_memo, "evidence": fake_evidence}

    def fake_score_evidence(ticker, evidence_summary):
        return _stub_full_eval().evidence

    def fake_score_memo(memo, evidence_summary):
        return _stub_full_eval().memo

    monkeypatch.setattr(run_module, "_run_pipeline_for_ticker", fake_run_pipeline)
    monkeypatch.setattr(run_module.judge, "score_evidence", fake_score_evidence)
    monkeypatch.setattr(run_module.judge, "score_memo", fake_score_memo)
    monkeypatch.setattr(run_module, "_setup_mlflow_and_run",
                        lambda *a, **k: _StubMlflowCtx(tmp_path))

    exit_code = run_module.main(["--quick"])
    assert pipeline_calls == ["AAPL", "RIVN"]
    assert exit_code == 0

    # Verify per-ticker artifacts were written under tmp_path
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1, "exactly one run dir per CLI invocation"
    run_dir = run_dirs[0]
    for ticker in ["AAPL", "RIVN"]:
        tdir = run_dir / ticker
        assert tdir.exists(), f"missing artifact dir for {ticker}"
        assert (tdir / "memo.json").exists()
        assert (tdir / "evidence_summary.txt").exists()
        assert (tdir / "judge_memo_rationale.json").exists()
        assert (tdir / "judge_evidence_rationale.json").exists()
        assert (tdir / "missing_items.json").exists()
    assert (run_dir / "summary.md").exists()


def test_run_partial_failure_exits_nonzero(monkeypatch, tmp_path):
    def fake_run_pipeline(ticker, epoch):
        if ticker == "RIVN":
            raise RuntimeError("pipeline boom")
        from backend.schemas.memo import ResearchMemo
        fake_memo = ResearchMemo(
            ticker=ticker,
            research_summary=f"test summary for {ticker}",
            bull_case="bull",
            bear_case="bear",
            moderator_synthesis="synthesis",
            contradictions_detected=[],
            unresolved_questions=[],
            confidence_notes="notes",
            citations=[],
        )
        return {"final_memo": fake_memo, "evidence": []}

    def fake_score_evidence(ticker, es):
        return _stub_full_eval().evidence

    def fake_score_memo(memo, es):
        return _stub_full_eval().memo

    monkeypatch.setattr(run_module, "_run_pipeline_for_ticker", fake_run_pipeline)
    monkeypatch.setattr(run_module.judge, "score_evidence", fake_score_evidence)
    monkeypatch.setattr(run_module.judge, "score_memo", fake_score_memo)
    monkeypatch.setattr(run_module, "_setup_mlflow_and_run",
                        lambda *a, **k: _StubMlflowCtx(tmp_path))

    exit_code = run_module.main(["--quick"])
    assert exit_code == 1

    # Verify the failure path wrote error.txt for RIVN, NOT memo.json
    run_dir = next(tmp_path.iterdir())
    rivn_dir = run_dir / "RIVN"
    assert rivn_dir.exists(), "RIVN dir should exist for failure tracking"
    assert (rivn_dir / "error.txt").exists()
    assert "RuntimeError" in (rivn_dir / "error.txt").read_text()
    assert not (rivn_dir / "memo.json").exists(), "memo.json should not exist on failure"

    # AAPL succeeded normally
    aapl_dir = run_dir / "AAPL"
    assert (aapl_dir / "memo.json").exists()


class _StubMlflowCtx:
    """Stand-in for tracking.parent_run / ticker_run that records calls."""
    def __init__(self, root):
        self.root = root
        self.run = MagicMock()
        self.run.info.run_id = "stub-run-id"

    def __enter__(self):
        return self.run

    def __exit__(self, *a):
        return False
