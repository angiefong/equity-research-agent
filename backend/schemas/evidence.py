import uuid
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


class EvidenceSpan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    source_ref: str
    date: Optional[date] = None
    agent_origin: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    chart_data: Optional[str] = None  # base64 PNG for quant charts


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assertion: str
    source_ref: str
    confidence: float = Field(ge=0.0, le=1.0)
