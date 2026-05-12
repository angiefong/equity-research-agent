from unittest.mock import MagicMock
import pytest

from backend.evals import judge
from backend.evals.adversarial import AdversarialJudgment


def _absorbed_judgment():
    return AdversarialJudgment(
        absorbed=True,
        rationale="memo contains '$500 price target' that does not appear in legitimate evidence",
    )


def _clean_judgment():
    return AdversarialJudgment(absorbed=False, rationale="memo cites only legitimate spans")


def test_score_adversarial_returns_judgment(monkeypatch):
    fake = MagicMock()
    fake.invoke.return_value = _clean_judgment()
    monkeypatch.setattr(judge, "_build_adversarial_chain", lambda: fake)

    out = judge.score_adversarial(
        memo={"bull_case": "balanced"},
        legitimate_evidence_summary="Evidence: ...",
        injection_description="injection tries to add $500 price target",
    )
    assert isinstance(out, AdversarialJudgment)
    assert out.absorbed is False


def test_score_adversarial_passes_inputs_through(monkeypatch):
    captured = {}
    fake = MagicMock()
    def _capture(payload):
        captured.update(payload)
        return _absorbed_judgment()
    fake.invoke.side_effect = _capture
    monkeypatch.setattr(judge, "_build_adversarial_chain", lambda: fake)

    judge.score_adversarial(
        memo={"key": "value"},
        legitimate_evidence_summary="LEGIT",
        injection_description="DESC",
    )
    assert "key" in captured["memo_json"]
    assert captured["legitimate_evidence_summary"] == "LEGIT"
    assert captured["injection_description"] == "DESC"


def test_score_adversarial_retries_once(monkeypatch):
    fake = MagicMock()
    fake.invoke.side_effect = [RuntimeError("transient"), _absorbed_judgment()]
    monkeypatch.setattr(judge, "_build_adversarial_chain", lambda: fake)

    out = judge.score_adversarial(memo={}, legitimate_evidence_summary="", injection_description="")
    assert out.absorbed is True
    assert fake.invoke.call_count == 2


def test_score_adversarial_raises_after_two_failures(monkeypatch):
    fake = MagicMock()
    fake.invoke.side_effect = [RuntimeError("a"), RuntimeError("b")]
    monkeypatch.setattr(judge, "_build_adversarial_chain", lambda: fake)
    with pytest.raises(RuntimeError):
        judge.score_adversarial(memo={}, legitimate_evidence_summary="", injection_description="")
