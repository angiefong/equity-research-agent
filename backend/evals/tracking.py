"""MLflow + DagsHub tracking wrapper for the eval harness.

One parent MLflow run per CLI invocation, one nested run per ticker.
Logs metrics, params, tags, and artifacts.
"""
from __future__ import annotations
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import mlflow
from mlflow.entities import Run

from backend.evals.rubric import FullEval

EXPERIMENT_NAME = "equity-research-agent"


def _mlflow_client():
    return mlflow.tracking.MlflowClient()


def setup_tracking() -> None:
    """Set tracking URI from DagsHub env vars, falling back to local mlruns/."""
    owner = os.environ.get("DAGSHUB_REPO_OWNER")
    repo = os.environ.get("DAGSHUB_REPO_NAME")
    token = os.environ.get("DAGSHUB_TOKEN")
    explicit_uri = os.environ.get("MLFLOW_TRACKING_URI")

    if explicit_uri:
        mlflow.set_tracking_uri(explicit_uri)
    elif owner and repo and token:
        mlflow.set_tracking_uri(f"https://dagshub.com/{owner}/{repo}.mlflow")
        # mlflow client reads these env vars for HTTP basic auth:
        os.environ.setdefault("MLFLOW_TRACKING_USERNAME", owner)
        os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", token)
    # else: mlflow falls back to local ./mlruns

    mlflow.set_experiment(EXPERIMENT_NAME)


@contextmanager
def parent_run(tags: dict[str, str], params: dict[str, Any]):
    setup_tracking()
    with mlflow.start_run(tags=tags) as run:
        mlflow.log_params(params)
        yield run


@contextmanager
def ticker_run(ticker: str):
    with mlflow.start_run(nested=True, run_name=ticker, tags={"ticker": ticker}) as run:
        yield run


def metric_dict_for_ticker(full: FullEval) -> dict[str, float]:
    return {
        "evidence_coverage":   full.evidence.evidence_coverage.score,
        "insight":             full.memo.insight.score,
        "factual_accuracy":    full.memo.factual_accuracy.score,
        "logical_consistency": full.memo.logical_consistency.score,
        "causal_reasoning":    full.memo.causal_reasoning.score,
        "synthesis_quality":   full.memo.synthesis_quality.score,
        "data_integrity":      full.memo.data_integrity.score,
        "agent_coordination":  full.memo.agent_coordination.score,
        "overall_memo":        full.memo.average,
    }


def aggregate_averages(per_ticker_metrics: list[dict[str, float] | None]) -> dict[str, float]:
    """Average per-metric across successful tickers; record success/fail counts."""
    succeeded = [m for m in per_ticker_metrics if m is not None]
    n_succ = len(succeeded)
    n_fail = len(per_ticker_metrics) - n_succ
    if n_succ == 0:
        return {"n_tickers_succeeded": 0, "n_tickers_failed": n_fail}
    keys = succeeded[0].keys()
    averages = {f"avg_{k}": sum(m[k] for m in succeeded) / n_succ for k in keys}
    averages["n_tickers_succeeded"] = n_succ
    averages["n_tickers_failed"] = n_fail
    return averages


def log_eval_artifacts(local_dir: Path) -> None:
    """Upload all artifacts under local_dir to the active run."""
    if local_dir.exists():
        mlflow.log_artifacts(str(local_dir))


def find_baseline_run(
    experiment_name: str,
    branch: str,
    epoch: str,
    ticker_set: str,
) -> Run | None:
    """Most recent successful parent run on `branch` matching epoch+ticker_set."""
    client = _mlflow_client()
    exp = client.get_experiment_by_name(experiment_name)
    if exp is None:
        return None
    filter_str = (
        f"tags.branch = '{branch}' "
        f"AND tags.epoch = '{epoch}' "
        f"AND params.ticker_set = '{ticker_set}' "
        f"AND attributes.status = 'FINISHED'"
    )
    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        filter_string=filter_str,
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    return runs[0] if runs else None
