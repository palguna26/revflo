from datetime import datetime
from typing import Optional, List, Literal, Dict
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

# --- Sub-Models for Structured Output ---

class RiskItem(BaseModel):
    title: str
    why_it_matters: str
    affected_areas: List[str]
    likelihood: Literal["low", "medium", "high"]
    recommended_action: str
    severity: Literal["critical", "high", "medium", "low"] = "medium"

class FragilityMap(BaseModel):
    high_risk_modules: List[str] = []
    change_sensitive_areas: List[str] = []

class SecurityReliabilityItem(BaseModel):
    finding: str
    severity: Literal["critical", "high", "medium", "low"]
    context: str

class Roadmap(BaseModel):
    fix_now: List[str] = []
    fix_next: List[str] = []
    defer: List[str] = []

class AuditSummary(BaseModel):
    maintainability: Literal["low", "medium", "high"]
    security: Literal["low", "medium", "high"]
    performance: Literal["low", "medium", "high"]
    testing_confidence: Literal["low", "medium", "high"]
    overview: str = ""

class AuditReport(BaseModel):
    """
    The strict output contract for the audit report.
    """
    summary: AuditSummary
    top_risks: List[RiskItem] = []
    fragility_map: FragilityMap
    security_reliability: List[SecurityReliabilityItem] = []
    roadmap: Roadmap
    executive_takeaway: str

# --- DB Document ---

class ScanResult(Document):
    repo_id: PydanticObjectId
    status: Literal["pending", "processing", "completed", "failed"]
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Store the full structured report
    report: Optional[AuditReport] = None
    
    # Raw metrics for internal use / debugging
    raw_metrics: Optional[Dict] = None
    
    error_message: Optional[str] = None

    class Settings:
        name = "scans"
        indexes = [
            "repo_id",
            "started_at",
        ]
