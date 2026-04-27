"""CLI entry-point for the eval harness.

Usage:
    python -m backend.evals.run --quick [--publish]
    python -m backend.evals.run --full  [--publish]
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import mlflow

from backend.evals import config, judge, report, snapshot, tracking
from backend.evals.rubric import FullEval

EXPERIMENT_NAME = "equity-research-agent"
RUNTIME_ROOT = Path("runtime_data/eval_runs")


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def _git_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def _agent_model_in_use() -> str:
    """Read the actual model from backend.agents.llm at runtime."""
    try:
        import backend.agents.llm as llm_mod
        import inspect
        src = inspect.getsource(llm_mod)
        for line in src.splitlines():
            line = line.strip()
            if line.startswith("model="):
                return line.split("=", 1)[1].strip().strip('",')
    except Exception:
        pass
    return "unknown"


def _run_pipeline_for_ticker(ticker: str, epoch: str) -> dict:
    """Invoke the LangGraph pipeline for one ticker, with snapshot replay active."""
    from backend.graph.builder import build_graph
    graph = build_graph()
    with snapshot.epoch_snapshot(epoch=epoch, ticker=ticker):
        result = graph.invoke({"ticker": ticker})
    return result


@contextmanager
def _setup_mlflow_and_run(tags: dict, params: dict):
    """Wrapper so tests can stub the entire MLflow ctx."""
    with tracking.parent_run(tags=tags, params=params) as run:
        yield run


def _publish_to_github(summary_path: Path) -> None:
    pr_number = os.environ.get("GITHUB_PR_NUMBER")
    if not pr_number:
        print("[publish] no GITHUB_PR_NUMBER set; skipping PR comment.")
        return
    cmd = ["gh", "pr", "comment", str(pr_number), "--body-file", str(summary_path)]
    subprocess.run(cmd, check=True)
    print(f"[publish] posted summary to PR #{pr_number}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="backend.evals.run")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--quick", action="store_true")
    grp.add_argument("--full", action="store_true")
    parser.add_argument("--publish", action="store_true",
                        help="post markdown summary to GitHub PR if $GITHUB_PR_NUMBER is set")
    args = parser.parse_args(argv)

    config.validate_env()
    ticker_set = "quick" if args.quick else "full"
    tickers = config.TICKER_SETS[ticker_set]
    epoch = config.resolve_epoch()
    judge_model = config.resolve_judge_model()
    agent_model = _agent_model_in_use()

    run_id = f"{int(time.time())}-{uuid.uuid4().hex[:6]}"
    local_dir = RUNTIME_ROOT / run_id
    local_dir.mkdir(parents=True, exist_ok=True)

    tags = {
        "git_sha": _git_sha(),
        "branch": _git_branch(),
        "agent_model": agent_model,
        "judge_model": judge_model,
        "epoch": epoch,
    }
    params = {
        "ticker_set": ticker_set,
        "n_tickers": len(tickers),
        "regression_threshold": config.resolve_regression_threshold(),
    }

    per_ticker: dict[str, FullEval | None] = {}
    n_failed = 0

    with _setup_mlflow_and_run(tags, params):
        for ticker in tickers:
            try:
                state = _run_pipeline_for_ticker(ticker, epoch)
                memo = state.get("memo") or state.get("research_memo") or state
                evidence_spans = state.get("evidence", [])
                if hasattr(memo, "model_dump"):
                    memo = memo.model_dump()
                evidence_dicts = [
                    e.model_dump() if hasattr(e, "model_dump") else e
                    for e in evidence_spans
                ]
                evidence_summary = judge.summarize_evidence(evidence_dicts)
                evidence_eval = judge.score_evidence(ticker, evidence_summary)
                memo_eval = judge.score_memo(memo, evidence_summary)
                full = FullEval(evidence=evidence_eval, memo=memo_eval)
                per_ticker[ticker] = full

                # Per-ticker artifacts
                tdir = local_dir / ticker
                tdir.mkdir(parents=True, exist_ok=True)
                (tdir / "memo.json").write_text(json.dumps(memo, indent=2, default=str))
                (tdir / "evidence_summary.txt").write_text(evidence_summary)
                (tdir / "judge_evidence_rationale.json").write_text(
                    evidence_eval.model_dump_json(indent=2)
                )
                (tdir / "judge_memo_rationale.json").write_text(
                    memo_eval.model_dump_json(indent=2)
                )
                (tdir / "missing_items.json").write_text(
                    json.dumps(evidence_eval.missing_items, indent=2)
                )

                with tracking.ticker_run(ticker):
                    mlflow.log_metrics(tracking.metric_dict_for_ticker(full))
                    mlflow.log_artifacts(str(tdir))

            except Exception as e:
                per_ticker[ticker] = None
                n_failed += 1
                tdir = local_dir / ticker
                tdir.mkdir(parents=True, exist_ok=True)
                (tdir / "error.txt").write_text(f"{type(e).__name__}: {e}\n")
                with tracking.ticker_run(ticker):
                    mlflow.set_tag("eval_status", "failed")
                    mlflow.log_artifacts(str(tdir))

        # Aggregate + log parent metrics
        per_ticker_metrics = [
            tracking.metric_dict_for_ticker(v) if v is not None else None
            for v in per_ticker.values()
        ]
        agg = tracking.aggregate_averages(per_ticker_metrics)
        mlflow.log_metrics(agg)

        # Look up baseline + render summary
        baseline = tracking.find_baseline_run(
            EXPERIMENT_NAME, branch="main", epoch=epoch, ticker_set=ticker_set
        )
        baseline_avgs = baseline.data.metrics if baseline else None

        dagshub_url = os.environ.get("MLFLOW_TRACKING_URI", "")
        run_meta = {
            "branch": tags["branch"],
            "epoch": epoch,
            "judge_model": judge_model,
            "agent_model": agent_model,
            "ticker_set": ticker_set,
            "dagshub_url": dagshub_url,
        }
        summary_md = report.build_summary(per_ticker, baseline_avgs, run_meta)
        summary_path = local_dir / "summary.md"
        summary_path.write_text(summary_md)
        mlflow.log_artifact(str(summary_path))

    print(summary_md)

    if args.publish:
        try:
            _publish_to_github(summary_path)
        except Exception as e:
            print(f"[publish] failed: {e}", file=sys.stderr)

    avg_overall = agg.get("avg_overall_memo")
    baseline_overall = baseline_avgs.get("avg_overall_memo") if baseline_avgs else None
    regressed = report.exceeds_regression(
        avg_overall, baseline_overall, config.resolve_regression_threshold()
    )
    if n_failed > 0 or regressed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
