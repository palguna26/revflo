from datetime import datetime
from typing import Optional, List, Literal
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel
from app.models.audit_schema import Finding, AuditCategories

class RiskItem(BaseModel):
    """V2: Backward compatible with V1 and V2 scan data"""
    # V2 fields (from risk_engine.py)
    id: Optional[str] = None
    rule_type: Optional[str] = None  # "Hotspot", "Deep Nesting", "Large File", etc.
    file_path: Optional[str] = None
    description: Optional[str] = None
    explanation: Optional[str] = None
    metrics: Optional[dict] = {}
    line_number: Optional[int] = None
    
    # V1 fields (for backward compatibility with existing scans)
    title: Optional[str] = None
    why_it_matters: Optional[str] = None
    affected_areas: Optional[List[str]] = []
    likelihood: Optional[Literal["high", "medium", "low"]] = None
    recommended_action: Optional[str] = None
    
    # Common field (both versions)
    severity: Literal["critical", "high", "medium", "low"] = "medium"

class AuditSummary(BaseModel):
    maintainability: int = 50  # 0-100 score
    security: int = 50
    performance: int = 50
    testing_confidence: int = 50
    code_quality: int = 50  # Added
    architecture: int = 50  # Added
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
    engine_version: str = "2.0.0"  # V2: Real cyclomatic complexity
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    overall_score: int = 0
    error_message: Optional[str] = None
    
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
