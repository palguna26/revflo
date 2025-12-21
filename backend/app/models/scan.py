from datetime import datetime
from typing import Optional, List, Literal
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel
from app.models.audit_schema import Finding, AuditCategories

class RiskItem(BaseModel):
    title: str
    why_it_matters: str
    affected_areas: List[str]
    likelihood: Literal["high", "medium", "low"]
    recommended_action: str
    severity: Literal["critical", "high", "medium", "low"]

class AuditSummary(BaseModel):
    maintainability: str
    security: str
    performance: str
    testing_confidence: str
    overview: str

class FragilityMap(BaseModel):
    high_risk_modules: List[str] = []
    change_sensitive_areas: List[str] = []

class SecurityReliabilityItem(BaseModel):
    finding: str
    severity: str
    context: str

class Roadmap(BaseModel):
    fix_now: List[str] = []
    fix_next: List[str] = []
    defer: List[str] = []

class AuditReport(BaseModel):
    summary: AuditSummary
    top_risks: List[RiskItem]
    fragility_map: FragilityMap
    security_reliability: List[SecurityReliabilityItem] = []
    roadmap: Roadmap
    executive_takeaway: str

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
    
    # AI Report
    report: Optional[AuditReport] = None
    raw_metrics: Optional[dict] = None # For debug/legacy

    class Settings:
        name = "scans"
