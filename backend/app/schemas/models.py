from datetime import datetime
from typing import Annotated, Any, List, Optional, Literal
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator


# Shared ID type
def str_objectid(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    return str(v)

PyObjectId = Annotated[str, BeforeValidator(str_objectid)]


class User(BaseModel):
    id: PyObjectId
    login: str
    avatar_url: str
    name: Optional[str] = None
    email: Optional[str] = None
    managed_repos: List[str] = []


class RepoSummary(BaseModel):
    repo_full_name: str
    owner: str
    name: str
    health_score: int
    is_installed: bool
    pr_count: int = 0
    issue_count: int = 0
    last_activity: Optional[str] = None


class PRSummary(BaseModel):
    """Lightweight PR card model used on repo page and dashboards."""

    pr_number: int
    title: str
    author: str
    created_at: datetime
    health_score: int = 90  # placeholder until we compute real health
    validation_status: Literal["pending", "validated", "needs_work"] = "pending"
    github_url: str


class ChecklistItem(BaseModel):
    id: str
    text: str
    required: bool
    status: Literal["pending", "passed", "failed", "skipped"]
    linked_tests: List[str] = []


class IssueChecklistSummary(BaseModel):
    total: int
    passed: int
    failed: int
    pending: int


class Issue(BaseModel):
    issue_number: int
    title: str
    status: Literal["open", "processing", "completed"]
    created_at: datetime
    updated_at: datetime
    checklist_summary: IssueChecklistSummary
    checklist: Optional[List[ChecklistItem]] = None
    github_url: str


class TestResult(BaseModel):
    test_id: str
    name: str
    status: Literal["passed", "failed", "skipped"]
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    checklist_ids: List[str] = []


class CodeHealthIssue(BaseModel):
    id: str
    severity: Literal["critical", "high", "medium", "low"]
    category: str
    message: str
    file_path: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


class CoverageAdvice(BaseModel):
    file_path: str
    lines: List[int]
    suggestion: str


class SuggestedTest(BaseModel):
    test_id: str
    name: str
    framework: str
    target: str
    checklist_ids: List[str]
    snippet: str
    reasoning: Optional[str] = None


class PRManifest(BaseModel):
    checklist_items: List[ChecklistItem]


class PRDetail(BaseModel):
    pr_number: int
    title: str
    author: str
    created_at: datetime
    health_score: int
    validation_status: Literal["pending", "validated", "needs_work"]
    manifest: Optional[PRManifest] = None
    test_results: List[TestResult]
    code_health: List[CodeHealthIssue]
    coverage_advice: List[CoverageAdvice]
    suggested_tests: List[SuggestedTest]
    github_url: str


class Notification(BaseModel):
    id: PyObjectId
    type: Literal["info", "warning", "error", "success"]
    message: str
    repo_full_name: Optional[str] = None
    created_at: datetime
    read: bool = False
