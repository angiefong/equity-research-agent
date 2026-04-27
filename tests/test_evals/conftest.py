import pytest
from backend.evals.rubric import (
    EvidenceEval,
    MemoEval,
    MetricScore,
)


@pytest.fixture
def sample_evidence_summary() -> str:
    return (
        "AAPL evidence (compact summary):\n"
        "- Q1 2026 revenue: $124.3B (+2% YoY)\n"
        "- iPhone revenue: $69.7B\n"
        "- Services revenue: $26.3B (+14% YoY)\n"
        "- Gross margin: 46.6%\n"
        "- 3 news items: Vision Pro launch, China demand softness, App Store ruling"
    )


@pytest.fixture
def sample_memo_dict() -> dict:
    return {
        "ticker": "AAPL",
        "bull_points": [
            {"claim": "Services growing 14% YoY", "rationale": "high-margin recurring", "source_refs": ["filings:10-Q:p3"]},
        ],
        "bear_points": [
            {"claim": "iPhone revenue decelerating", "rationale": "China softness", "source_refs": ["news:reuters:2026-04-20"]},
        ],
        "synthesis": "Services growth offsets iPhone deceleration in the near term.",
        "scenarios": [],
        "contradiction_resolutions": [],
        "unresolved_questions": ["FY26 guidance pending"],
    }


@pytest.fixture
def fake_evidence_eval() -> EvidenceEval:
    return EvidenceEval(
        evidence_coverage=MetricScore(score=3, rationale="segment present, geo missing"),
        missing_items=["China revenue trend", "FY26 guidance"],
    )


@pytest.fixture
def fake_memo_eval() -> MemoEval:
    return MemoEval(
        insight=MetricScore(score=3, rationale="r"),
        factual_accuracy=MetricScore(score=4, rationale="r"),
        logical_consistency=MetricScore(score=4, rationale="r"),
        causal_reasoning=MetricScore(score=3, rationale="r"),
        synthesis_quality=MetricScore(score=3, rationale="r"),
        data_integrity=MetricScore(score=4, rationale="r"),
        agent_coordination=MetricScore(score=4, rationale="r"),
        overall_comment="Solid bull/bear, weak on geo specificity.",
    )
