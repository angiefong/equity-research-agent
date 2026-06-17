from fastapi.testclient import TestClient

from backend.api import app


def test_demo_gate_allows_open_dev_when_unset(monkeypatch):
    monkeypatch.delenv("DEMO_ACCESS_CODE", raising=False)
    client = TestClient(app)

    resp = client.get("/runs?limit=1")

    assert resp.status_code == 200


def test_demo_gate_requires_access_code_when_set(monkeypatch):
    monkeypatch.setenv("DEMO_ACCESS_CODE", "let-me-in")
    client = TestClient(app)

    missing = client.get("/runs?limit=1")
    wrong = client.get("/runs?limit=1&access_code=nope")
    ok = client.get("/runs?limit=1&access_code=let-me-in")

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert ok.status_code == 200
