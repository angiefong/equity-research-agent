import os
import pytest
from backend.evals import config


def test_ticker_sets_defined():
    assert config.TICKER_SETS["quick"] == ["AAPL", "RIVN"]
    assert config.TICKER_SETS["full"] == ["AAPL", "MSFT", "F", "PLTR", "TSLA"]


def test_defaults_present():
    assert config.DEFAULT_EPOCH == "2026-Q2"
    assert config.DEFAULT_JUDGE_MODEL == "claude-sonnet-4-6"
    assert config.REGRESSION_THRESHOLD == 0.3


def test_validate_env_missing_anthropic_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_KEY", "x")
    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        config.validate_env()


def test_validate_env_missing_groq_raises(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.delenv("GROQ_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="GROQ_KEY"):
        config.validate_env()


def test_validate_env_passes_with_required_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("GROQ_KEY", "x")
    config.validate_env()  # no exception


def test_resolve_judge_model_uses_default(monkeypatch):
    monkeypatch.delenv("EVAL_JUDGE_MODEL", raising=False)
    assert config.resolve_judge_model() == "claude-sonnet-4-6"


def test_resolve_judge_model_uses_override(monkeypatch):
    monkeypatch.setenv("EVAL_JUDGE_MODEL", "claude-haiku-4-5-20251001")
    assert config.resolve_judge_model() == "claude-haiku-4-5-20251001"
