"""Rubric schemas + anchor text for the LLM-as-judge eval harness."""
from __future__ import annotations
from pydantic import BaseModel, Field


class MetricScore(BaseModel):
    score: int = Field(ge=0, le=5, description="0=hallucinated, 3=intern, 5=publication-grade")
    rationale: str = Field(description="1-3 sentences citing specific content")


class EvidenceEval(BaseModel):
    evidence_coverage: MetricScore
    missing_items: list[str] = Field(
        default_factory=list,
        description="Specific evidence items the pipeline failed to gather",
    )


class MemoEval(BaseModel):
    insight: MetricScore
    factual_accuracy: MetricScore
    logical_consistency: MetricScore
    causal_reasoning: MetricScore
    synthesis_quality: MetricScore
    data_integrity: MetricScore
    agent_coordination: MetricScore
    overall_comment: str

    @property
    def average(self) -> float:
        scores = [
            self.insight.score,
            self.factual_accuracy.score,
            self.logical_consistency.score,
            self.causal_reasoning.score,
            self.synthesis_quality.score,
            self.data_integrity.score,
            self.agent_coordination.score,
        ]
        return sum(scores) / len(scores)


class FullEval(BaseModel):
    evidence: EvidenceEval
    memo: MemoEval


EVIDENCE_RUBRIC_TEXT = """\
Evidence quality rubric (0-5):
- 0: Evidence is missing or completely irrelevant to writing a senior-analyst memo on this ticker.
- 1: Major categories absent (no fundamentals, no news, no filings).
- 2: One critical category present but shallow (e.g., prices only, no segment data).
- 3: Competent intern-level coverage — fundamentals + news + filings present, but segment / geo / forward-guidance breakdowns missing.
- 4: Senior-analyst breadth — segment revenue, geo mix, margin trends present, with timestamps.
- 5: Publication-grade evidence: forward guidance, peer comps, multiple-year trends, every span timestamped, every claim sourceable.

In `missing_items`, list specific items by name (e.g., "Services revenue growth rate", "F-Series segment margins", "China geo exposure", "FY26 guidance"). Use ticker-specific knowledge — AAPL needs Services + iPhone segments; TSLA needs delivery numbers + energy segment; F needs F-Series and credit segment.
"""

MEMO_RUBRIC_TEXT = """\
Memo quality rubric (7 metrics, each scored 0-5 with a 1-3 sentence rationale citing specific memo content):

1. Insight — does the memo make non-obvious, ticker-specific claims?
   - 0: Generic peer-applicable platitudes.
   - 3: Competent intern observations (correct but obvious).
   - 5: Non-obvious thesis with specific named drivers grounded in the evidence.

2. Factual accuracy — are numbers correctly read and interpreted?
   - 0: Invented or misread metrics; level/growth confused.
   - 3: Mostly correct with a one-off slip.
   - 5: Every number traceable to evidence and correctly interpreted (delta vs level, YoY vs QoQ).

3. Logical consistency — internal contradictions handled?
   - 0: Contradictions present and unresolved.
   - 3: Minor inconsistencies between sections.
   - 5: Contradictions detected and adjudicated explicitly.

4. Causal reasoning — driver → mechanism → financial → valuation chains?
   - 0: "X is good because revenue grew."
   - 3: Partial driver → impact chain.
   - 5: Full driver → mechanism → financial impact → valuation impact chain on key claims.

5. Synthesis quality — bull and bear synthesized vs restated?
   - 0: Both sides restated, no synthesis.
   - 3: Partial reconciliation.
   - 5: Disputes resolved with reasoning that picks a side or names what would change the call.

6. Data integrity — every claim cited, no inventions?
   - 0: Numbers from nowhere.
   - 3: Most claims cited.
   - 5: Every claim has a span cite to evidence.

7. Agent coordination — bull and bear engage each other?
   - 0: Independent monologues.
   - 3: Partial cross-reference.
   - 5: Bull and bear directly engage each other's specific claims.

Score in this fixed order: insight → factual_accuracy → logical_consistency → causal_reasoning → synthesis_quality → data_integrity → agent_coordination.
"""
