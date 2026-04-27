import uuid
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from backend.schemas.contradiction import ContradictionSeverity


class VerificationIssueType(str, Enum):
    UNSUPPORTED_CLAIM = "unsupported_claim"
    NUMERIC_MISMATCH = "numeric_mismatch"
    SOURCE_NOT_FOUND = "source_not_found"
    STALE_DATA = "stale_data"


class VerificationIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    claim: str
    issue_type: VerificationIssueType
    severity: ContradictionSeverity
    suggested_action: str
    target_agent: Optional[str] = None
