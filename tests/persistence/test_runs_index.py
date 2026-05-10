import json
import os
from pathlib import Path

import pytest

from backend.persistence.runs_index import append_run, list_runs


@pytest.fixture
def tmp_index(tmp_path, monkeypatch):
    path = tmp_path / "runs.jsonl"
    monkeypatch.setattr("backend.persistence.runs_index.RUNS_FILE", str(path))
    return path


def test_append_and_list_runs(tmp_index):
    append_run({
        "run_id": "abc",
        "ticker": "AAPL",
        "verdict": "Cautious Bull",
        "bull_weight": 0.78,
        "bear_weight": 0.64,
        "lede": "Apple presents a cautious bull setup.",
        "duration_s": 134.2,
        "agent_count": 14,
    })
    append_run({
        "run_id": "def",
        "ticker": "NVDA",
        "verdict": "Strong Bull",
        "bull_weight": 0.85,
        "bear_weight": 0.30,
        "lede": "NVDA continues to compound.",
        "duration_s": 111.8,
        "agent_count": 14,
    })
    runs = list_runs(limit=10)
    assert len(runs) == 2
    # newest first
    assert runs[0]["run_id"] == "def"
    assert runs[1]["run_id"] == "abc"


def test_list_runs_respects_limit(tmp_index):
    for i in range(5):
        append_run({"run_id": f"r{i}", "ticker": "X", "verdict": "Bull",
                    "bull_weight": 0.5, "bear_weight": 0.5, "lede": "x",
                    "duration_s": 1.0, "agent_count": 1})
    assert len(list_runs(limit=3)) == 3
