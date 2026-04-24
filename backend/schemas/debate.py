import uuid
from enum import Enum
from pydantic import BaseModel, Field


class DebateSide(str, Enum):
    BULL = "bull"
    BEAR = "bear"


class DebatePoint(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    side: DebateSide
    claim: str
    evidence_span_ids: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
