from datetime import datetime
from typing import Optional, List, Literal
from beanie import Document, PydanticObjectId
from pydantic import Field
from app.models.audit_schema import Finding, AuditCategories

class Vulnerability(Finding):
    # Backwards compatibility if needed, or just alias it. 
    # The prompt asked for "findings", let's use Finding for general issues
    # and keep a specific list for vulnerabilities if we want, or merge them.
    # The prompt explicitly asked for "Critical Findings" section.
    package_name: Optional[str] = None
    fixed_version: Optional[str] = None

class ScanResult(Document):
    repo_id: PydanticObjectId
    status: Literal["pending", "processing", "completed", "failed"]
    
    # Audit Metadata
    commit_sha: Optional[str] = None
    engine_version: str = "1.0.0"
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    overall_score: int = 0
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Detailed Results
    categories: AuditCategories = Field(default_factory=AuditCategories)
    findings: List[Finding] = []
    
    # Legacy/Simple Summary
    summary: str = ""

    class Settings:
        name = "scans"
