from typing import Optional, List, Literal
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel

# We can reuse the schema definitions or redefine embedded documents here.
# To keep it self-contained and clean, I'll redefine embedded models or import if I can.
# For now, let's redefine simplified embedded classes or use Dict if complex.
# Better: Import the sub-models (ChecklistItem, IssueChecklistSummary) from schemas if they are purely data structures.
# But schemas are in `app.schemas.models`.

class ValidationResult(BaseModel):
    pr_number: int
    status: Literal["passed", "failed", "pending", "skipped"]
    evidence: Optional[str] = None
    reasoning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChecklistItem(BaseModel):
    id: str
    text: str
    required: bool
    status: Literal["pending", "passed", "failed", "skipped"]
    linked_tests: List[str] = []
    latest_validation: Optional[ValidationResult] = None
    validations: List[ValidationResult] = []

class IssueChecklistSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pending: int

class Issue(Document):
    repo_id: PydanticObjectId
    issue_number: int
    title: str
    status: Literal["open", "processing", "completed"] = "open"
    created_at: datetime
    updated_at: datetime
    checklist_summary: IssueChecklistSummary
    checklist: List[ChecklistItem] = []
    github_url: str
    description: Optional[str] = None

    class Settings:
        name = "issues"
