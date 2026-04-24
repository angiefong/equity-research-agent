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
    unresolved_questions: list[str]
    thesis_drift_summary: Optional[str] = None
    confidence_notes: str
    citations: list[str]
