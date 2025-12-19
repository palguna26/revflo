from typing import Optional, List, Literal, Any
import uuid
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel

# Complex nested structures for PR analysis
class TestResult(BaseModel):
    test_id: str
    name: str
    status: Literal["passed", "failed", "skipped"]
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    checklist_ids: List[str] = []

class CodeHealthIssue(BaseModel):
    id: Optional[str] = None # Make optional for legacy
    severity: Literal["critical", "high", "medium", "low"]
    category: Optional[str] = "general" # Make optional
    message: str
    file_path: Optional[str] = "unknown" # Make optional
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    # Support legacy fields if needed via validator but for now just optional

class CoverageAdvice(BaseModel):
    file_path: str
    lines: List[int]
    suggestion: str

class SuggestedTest(BaseModel):
    test_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    framework: str = "pytest"
    target: Optional[str] = "unknown"
    checklist_ids: List[str] = []
    snippet: Optional[str] = None # Make optional
    reasoning: Optional[str] = None

class ChecklistItem(BaseModel):
    id: str
    text: str
    required: bool
    status: Literal["pending", "passed", "failed", "skipped", "indeterminate"]
    linked_tests: List[str] = []
    evidence: Optional[str] = None
    reasoning: Optional[str] = None

class PRManifest(BaseModel):
    checklist_items: List[ChecklistItem]

class PRDetailData(BaseModel):
    # This mirrors the 'detail' field from the original raw dict, 
    # but flattened into the document is better for Beanie.
    # However, existing code had `doc["detail"]`. I will flatten it for better schema.
    pr_number: int
    title: str
    author: str
    created_at: datetime
    health_score: int
    validation_status: Literal["pending", "validated", "needs_work"]
    manifest: Optional[PRManifest] = None
    test_results: List[TestResult] = []
    code_health: List[CodeHealthIssue] = []
    coverage_advice: List[CoverageAdvice] = []
    suggested_tests: List[SuggestedTest] = []
    github_url: str

class PullRequest(Document):
    repo_id: PydanticObjectId
    pr_number: int
    
    # Flattening the detail:
    title: str
    author: str
    created_at: datetime
    github_url: str
    
    # Analysis fields
    health_score: int = 0
    validation_status: Literal["pending", "validated", "needs_work"] = "pending"
    block_reason: Optional[Literal["BLOCK_CHECKLIST_FAILED", "BLOCK_INDETERMINATE_EVIDENCE", "BLOCK_SECURITY_CRITICAL", "BLOCK_INSUFFICIENT_ISSUE_SPEC"]] = None
    revalidate_requested_at: Optional[datetime] = None
    recommended_for_merge: bool = False
    recommended_at: Optional[datetime] = None
    summary: Optional[str] = None
    
    # Complex Data
    manifest: Optional[PRManifest] = None
    test_results: List[TestResult] = []
    code_health: List[CodeHealthIssue] = []
    coverage_advice: List[CoverageAdvice] = []
    suggested_tests: List[SuggestedTest] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "pull_requests"
