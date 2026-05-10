from fastapi.testclient import TestClient

from backend import api


def test_runs_endpoint_returns_recent(monkeypatch, tmp_path):
    runs_file = tmp_path / "runs.jsonl"
    monkeypatch.setattr("backend.persistence.runs_index.RUNS_FILE", str(runs_file))
    from backend.persistence.runs_index import append_run
    append_run({"run_id": "a", "ticker": "AAPL", "verdict": "Bull",
                "bull_weight": 0.7, "bear_weight": 0.5, "lede": "x",
                "duration_s": 1.0, "agent_count": 14})

    client = TestClient(api.app)
    resp = client.get("/runs?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body[0]["ticker"] == "AAPL"
