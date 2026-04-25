import json
from pathlib import Path
import pytest
from backend.evals import snapshot


def test_arg_hash_stable_across_calls():
    h1 = snapshot._arg_hash(("AAPL",), {"max_results": 5})
    h2 = snapshot._arg_hash(("AAPL",), {"max_results": 5})
    assert h1 == h2


def test_arg_hash_different_for_different_args():
    h1 = snapshot._arg_hash(("AAPL",), {})
    h2 = snapshot._arg_hash(("MSFT",), {})
    assert h1 != h2


def test_arg_hash_ignores_time_varying_keys():
    h1 = snapshot._arg_hash(("AAPL",), {"as_of": "2026-01-01"})
    h2 = snapshot._arg_hash(("AAPL",), {"as_of": "2026-04-25"})
    assert h1 == h2  # `as_of` is in the ignore list


def test_serialize_roundtrip_pydantic(tmp_path):
    from backend.schemas.evidence import EvidenceSpan

    span = EvidenceSpan(
        source_ref="news:tavily:test_section",
        text="hello",
        agent_origin="test",
    )
    payload = snapshot._serialize(span)
    rehydrated = snapshot._deserialize(payload, EvidenceSpan)
    assert rehydrated.text == "hello"


def test_serialize_roundtrip_list_of_pydantic():
    from backend.schemas.evidence import EvidenceSpan

    spans = [
        EvidenceSpan(source_ref="news:tavily:a", text="a", agent_origin="test"),
        EvidenceSpan(source_ref="news:tavily:b", text="b", agent_origin="test"),
    ]
    payload = snapshot._serialize(spans)
    rehydrated = snapshot._deserialize(payload, list[EvidenceSpan])
    assert [s.text for s in rehydrated] == ["a", "b"]


def test_cold_cache_writes_fixture_then_warm_cache_reads_it(tmp_path, monkeypatch):
    """First call hits real fn, writes fixture. Second call reads from fixture."""
    call_count = {"n": 0}

    def fake_real_fn(ticker):
        call_count["n"] += 1
        return [{"sentinel": ticker, "call": call_count["n"]}]

    # Stand up a fake module attribute we can monkeypatch
    import types
    fake_mod = types.ModuleType("fake_tools_mod")
    fake_mod.fake_fetch = fake_real_fn
    monkeypatch.setitem(__import__("sys").modules, "fake_tools_mod", fake_mod)

    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()

    # Run cold
    with snapshot._patch("fake_tools_mod", "fake_fetch", fixture_dir, return_type=list):
        out1 = fake_mod.fake_fetch("AAPL")
    assert out1 == [{"sentinel": "AAPL", "call": 1}]
    # at least one fixture file written
    assert any(fixture_dir.iterdir())

    # Run warm — should NOT call real fn again
    with snapshot._patch("fake_tools_mod", "fake_fetch", fixture_dir, return_type=list):
        out2 = fake_mod.fake_fetch("AAPL")
    assert out2 == [{"sentinel": "AAPL", "call": 1}]  # same as cold; no new call
    assert call_count["n"] == 1


def test_epoch_snapshot_context_manager_patches_real_targets(tmp_path):
    """Smoke: epoch_snapshot context patches the documented backend.tools.* targets without raising."""
    with snapshot.epoch_snapshot(epoch="test-epoch", ticker="AAPL", root=tmp_path):
        from backend.tools.news import get_news_evidence
        assert callable(get_news_evidence)  # still callable, but patched
