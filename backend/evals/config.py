"""Eval harness configuration: ticker sets, defaults, env validation."""
from __future__ import annotations
import os

TICKER_SETS: dict[str, list[str]] = {
    "quick": ["AAPL", "RIVN"],
    "full":  ["AAPL", "MSFT", "F", "PLTR", "TSLA"],
}

DEFAULT_EPOCH = "2026-Q2"
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"
REGRESSION_THRESHOLD = 0.3

REQUIRED_ENV = ("ANTHROPIC_KEY", "GROQ_KEY")


def validate_env() -> None:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing required env vars for eval: {', '.join(missing)}"
        )


def resolve_judge_model() -> str:
    return os.environ.get("EVAL_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)


def resolve_epoch() -> str:
    return os.environ.get("EVAL_EPOCH", DEFAULT_EPOCH)


def resolve_regression_threshold() -> float:
    raw = os.environ.get("EVAL_REGRESSION_THRESHOLD")
    if raw is None:
        return REGRESSION_THRESHOLD
    return float(raw)
