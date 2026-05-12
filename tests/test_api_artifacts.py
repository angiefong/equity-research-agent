from fastapi.testclient import TestClient
from backend import api


def test_artifacts_endpoint_returns_meta_fields(monkeypatch):
    """Verify /run/{id}/artifacts surfaces duration_s, agent_count, market_snapshot.

    We bypass the SSE handler by writing directly into _run_results, the same
    cache the artifacts endpoint reads from.
    """
    api._run_results["test-run-1"] = {
        "evidence": [],
        "bull_points": [],
        "bear_points": [],
        "duration_s": 12.34,
        "agent_count": 15,
        "market_snapshot": {
            "ticker": "AAPL",
            "current_price": 214.82,
            "change_abs": 2.94,
            "change_pct": 1.39,
            "high_52w": 238.0,
            "low_52w": 164.0,
            "market_cap": 3.2e12,
            "pe_forward": 28.5,
            "eps_ttm": 6.05,
            "dividend_yield": 0.0049,
            "volume": 72000000,
            "series": [{"date": "2026-02-10", "price": 180.0}],
        },
    }

    client = TestClient(api.app)
    resp = client.get("/run/test-run-1/artifacts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["duration_s"] == 12.34
    assert body["agent_count"] == 15
    assert body["market_snapshot"]["ticker"] == "AAPL"
    assert body["market_snapshot"]["current_price"] == 214.82
    assert len(body["market_snapshot"]["series"]) == 1


def test_artifacts_endpoint_404_on_unknown_run():
    client = TestClient(api.app)
    resp = client.get("/run/does-not-exist/artifacts")
    assert resp.status_code == 404
