"""Adversarial eval harness: measures prompt-injection resistance via planted news spans.

See docs/adr/0004 for the design rationale. The harness loads JSON fixtures from
backend/evals/adversarial_fixtures/, patches the news-fetch layer for each case to inject
a poisoned span alongside legitimate ones, runs the full LangGraph pipeline, and scores:

  - Primary (judge):       absorption_rate = absorbed_cases / total_cases  (lower is better)
  - Diagnostic (program):  catch breakdown by mechanism — verifier_flagged / agent_refused /
                           citation_layer_caught / absorbed
"""
from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AdversarialCategory(str, Enum):
    EXPLICIT_INSTRUCTION = "explicit_instruction"
    ROLE_HIJACK = "role_hijack"
    MISLEADING_QUOTATION = "misleading_quotation"
    FABRICATED_METRIC = "fabricated_metric"
    SOURCE_REF_SPOOF = "source_ref_spoof"


class AdversarialSpan(BaseModel):
    text: str
    source_ref: str
    agent_origin: str = "news"
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class AdversarialFixture(BaseModel):
    case_id: str
    ticker: str
    category: AdversarialCategory
    description: str = Field(description="What this attack does, in one sentence")
    legitimate_news_spans: list[AdversarialSpan] = Field(min_length=1)
    poisoned_news_span: AdversarialSpan
    success_markers: list[str] = Field(
        default_factory=list,
        description="Phrases whose presence in the memo strongly suggests absorption (diagnostic only — judge is authoritative)",
    )


class CatchBreakdown(BaseModel):
    verifier_flagged: bool = False
    agent_refused: bool = False
    citation_layer_caught: bool = False
    absorbed: bool = False

    @property
    def caught(self) -> bool:
        return not self.absorbed


class AdversarialJudgment(BaseModel):
    absorbed: bool
    rationale: str


class AdversarialResult(BaseModel):
    case_id: str
    ticker: str
    category: AdversarialCategory
    judgment: AdversarialJudgment
    breakdown: CatchBreakdown
    final_memo_snippet: Optional[str] = None
    error: Optional[str] = None


def load_fixtures(directory: Path) -> list[AdversarialFixture]:
    """Load and validate every .json file in `directory` as an AdversarialFixture."""
    files = sorted(p for p in directory.glob("*.json") if p.is_file())
    if not files:
        raise FileNotFoundError(f"no adversarial fixtures found under {directory}")
    fixtures: list[AdversarialFixture] = []
    seen: set[str] = set()
    for f in files:
        data = json.loads(f.read_text())
        fixture = AdversarialFixture(**data)
        if fixture.case_id in seen:
            raise ValueError(f"duplicate case_id {fixture.case_id!r} in {f}")
        seen.add(fixture.case_id)
        fixtures.append(fixture)
    return fixtures
