import os, json, tempfile
from backend.persistence.snapshot_store import save_snapshot, load_latest_snapshot
from backend.schemas.thesis import ThesisSnapshot

def _make_snapshot(ticker="AAPL"):
    return ThesisSnapshot(
        ticker=ticker,
        bull_points=[],
        bear_points=[],
        confidence_by_topic={"growth": 0.8},
    )

def test_save_and_load_snapshot(tmp_path):
    os.environ["RUNTIME_DATA_DIR"] = str(tmp_path)
    snap = _make_snapshot()
    save_snapshot(snap)
    loaded = load_latest_snapshot("AAPL")
    assert loaded is not None
    assert loaded.ticker == "AAPL"
    assert loaded.confidence_by_topic["growth"] == 0.8

def test_load_returns_none_when_no_prior(tmp_path):
    os.environ["RUNTIME_DATA_DIR"] = str(tmp_path)
    result = load_latest_snapshot("NVDA")
    assert result is None
