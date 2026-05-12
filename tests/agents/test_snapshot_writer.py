from unittest.mock import patch
from backend.agents.snapshot_writer import snapshot_writer_agent
from backend.schemas.debate import DebatePoint, DebateSide
from backend.schemas.thesis import ThesisSnapshot


def _point(side, claim, conf):
    return DebatePoint(side=side, claim=claim, evidence_span_ids=[], confidence=conf, rationale="r")


def test_snapshot_writer_persists_and_returns_snapshot():
    state = {
        "ticker": "AAPL",
        "bull_points": [_point(DebateSide.BULL, "Services growth", 0.8)],
        "bear_points": [_point(DebateSide.BEAR, "Hardware saturation", 0.6)],
    }
    with patch("backend.agents.snapshot_writer.save_snapshot") as mock_save:
        result = snapshot_writer_agent(state)
    mock_save.assert_called_once()
    saved = mock_save.call_args[0][0]
    assert isinstance(saved, ThesisSnapshot)
    assert saved.ticker == "AAPL"
    assert len(saved.bull_points) == 1
    assert len(saved.bear_points) == 1
    assert result["thesis_snapshot_current"] is saved
    assert "Services growth"[:40] in saved.confidence_by_topic
    assert "Hardware saturation"[:40] in saved.confidence_by_topic


def test_snapshot_writer_handles_empty_points():
    state = {"ticker": "AAPL", "bull_points": [], "bear_points": []}
    with patch("backend.agents.snapshot_writer.save_snapshot"):
        result = snapshot_writer_agent(state)
    snap = result["thesis_snapshot_current"]
    assert snap.bull_points == []
    assert snap.bear_points == []
    assert snap.confidence_by_topic == {}
