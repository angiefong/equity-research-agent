import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ResearchMemo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    research_summary: str
    bull_case: str
    bear_case: str
    moderator_synthesis: str
    contradictions_detected: list[str]
    contradiction_resolutions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str]
    thesis_drift_summary: Optional[str] = None
    confidence_notes: str
    scenarios: list[str] = Field(default_factory=list)
    citations: list[str]
    bull_weight: Optional[float] = None
    bear_weight: Optional[float] = None
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
