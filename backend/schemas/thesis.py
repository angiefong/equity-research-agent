import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from backend.schemas.debate import DebatePoint


class ConfidenceDrift(BaseModel):
    topic: str
    previous: float
    current: float
    delta: float


class ThesisSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bull_points: list[DebatePoint]
    bear_points: list[DebatePoint]
    confidence_by_topic: dict[str, float]


class ThesisDelta(BaseModel):
    ticker: str
    previous_run_id: str
    current_run_id: str
    strengthened: list[str]
    weakened: list[str]
    new: list[str]
    disappeared: list[str]
    confidence_drift: list[ConfidenceDrift]
