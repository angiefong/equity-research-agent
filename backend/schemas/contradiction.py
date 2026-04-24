import uuid
from enum import Enum
from pydantic import BaseModel, Field


class ContradictionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContradictionStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    UNRESOLVABLE = "unresolvable"


class Contradiction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim_a: str
    claim_b: str
    source_refs: list[str]
    severity: ContradictionSeverity
    rationale: str
    status: ContradictionStatus = ContradictionStatus.OPEN
