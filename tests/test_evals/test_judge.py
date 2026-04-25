from unittest.mock import MagicMock, patch
import datetime as _dt
import pytest
from backend.evals import judge
from backend.evals.rubric import EvidenceEval, MemoEval


def test_score_evidence_returns_evidence_eval(
    sample_evidence_summary, fake_evidence_eval, monkeypatch
):
    fake_chain = MagicMock()
    fake_chain.invoke.return_value = fake_evidence_eval

    monkeypatch.setattr(judge, "_build_evidence_chain", lambda: fake_chain)
    out = judge.score_evidence(ticker="AAPL", evidence_summary=sample_evidence_summary)
    assert isinstance(out, EvidenceEval)
    assert out.evidence_coverage.score == 3


def test_score_memo_returns_memo_eval(
    sample_evidence_summary, sample_memo_dict, fake_memo_eval, monkeypatch
):
    fake_chain = MagicMock()
    fake_chain.invoke.return_value = fake_memo_eval

    monkeypatch.setattr(judge, "_build_memo_chain", lambda: fake_chain)
    out = judge.score_memo(memo=sample_memo_dict, evidence_summary=sample_evidence_summary)
    assert isinstance(out, MemoEval)
    assert out.average == pytest.approx(fake_memo_eval.average)


def test_score_evidence_retries_on_first_failure(
    sample_evidence_summary, fake_evidence_eval, monkeypatch
):
    fake_chain = MagicMock()
    fake_chain.invoke.side_effect = [RuntimeError("transient"), fake_evidence_eval]

    monkeypatch.setattr(judge, "_build_evidence_chain", lambda: fake_chain)
    out = judge.score_evidence(ticker="AAPL", evidence_summary=sample_evidence_summary)
    assert out.evidence_coverage.score == 3
    assert fake_chain.invoke.call_count == 2


def test_score_evidence_raises_after_two_failures(
    sample_evidence_summary, monkeypatch
):
    fake_chain = MagicMock()
    fake_chain.invoke.side_effect = [RuntimeError("x"), RuntimeError("y")]

    monkeypatch.setattr(judge, "_build_evidence_chain", lambda: fake_chain)
    with pytest.raises(RuntimeError):
        judge.score_evidence(ticker="AAPL", evidence_summary=sample_evidence_summary)


def test_summarize_evidence_truncates_long_input():
    spans = [{"text": "x" * 100, "source_ref": f"src:{i}"} for i in range(50)]
    summary = judge.summarize_evidence(spans, max_chars=500)
    assert len(summary) <= 600   # allow header overhead
    assert summary.startswith("Evidence (")


def test_score_memo_handles_datetime_in_memo(sample_evidence_summary, fake_memo_eval, monkeypatch):
    """Real ResearchMemo dicts contain datetime fields; json.dumps must not crash on them."""
    fake_chain = MagicMock()
    fake_chain.invoke.return_value = fake_memo_eval

    monkeypatch.setattr(judge, "_build_memo_chain", lambda: fake_chain)
    memo_with_dt = {
        "ticker": "AAPL",
        "timestamp": _dt.datetime(2026, 4, 25, 12, 0, 0),
        "synthesis": "x",
    }
    out = judge.score_memo(memo=memo_with_dt, evidence_summary=sample_evidence_summary)
    assert isinstance(out, MemoEval)
