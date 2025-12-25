"""
Repo Audit Pipeline - Data Models

Issue-agnostic risk assessment models.
Completely separate from PR Validation to prevent coupling.
"""
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel


# Audit Finding

class AuditFinding(Document):
    """
    Issue-agnostic observation from code audit.
    
    Contract:
    - No checklists
    - No issue references
    - Pure risk assessment
    - Immutable
    """
    audit_run_id: PydanticObjectId
    
    # Classification
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal["security", "performance", "code_quality", "architecture", "dependencies", "tests"]
    rule: str  # e.g., "unsafe_pickle", "exposed_secret", "high_complexity"
    
    # Location
    file_path: str
    line_number: Optional[int] = None
    
    # Details
    description: str
    recommendation: Optional[str] = None
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    immutable: bool = True
    
    class Settings:
        name = "audit_findings"
        indexes = ["audit_run_id", "severity", "category"]


# Audit Run

class AuditRun(Document):
    """
    Immutable audit snapshot tied to specific commit.
    
    Contract:
    - Tied to commit SHA (point-in-time)
    - Stores findings separately
    - Never references issues or PRs
    """
    repo_id: PydanticObjectId
    
    # Snapshot info
    commit_sha: str
    branch: str = "main"
    
    # Status
    status: Literal["pending", "running", "completed", "failed"]
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Summary metrics (computed from findings)
    metrics: Dict[str, Any] = {}  # e.g., {"critical_count": 3, "high_count": 12}
    
    # Error info if failed
    error: Optional[str] = None
    
    class Settings:
        name = "audit_runs"
        indexes = ["repo_id", "commit_sha", "started_at"]


# Audit Trend (for time-series analysis)

class AuditTrend(BaseModel):
    """
    Aggregated audit data for trends.
    
    Used for time-series visualization, not core storage.
    """
    date: datetime
    commit_sha: str
    
    # Metric snapshots
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Category breakdown
    security_issues: int = 0
    performance_issues: int = 0
    quality_issues: int = 0
