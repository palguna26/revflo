from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Finding(BaseModel):
    id: str
    severity: Literal["critical", "high", "medium", "low"]
    file_path: str
    line: int
    description: str
    explanation: Optional[str] = None # Short AI explanation if available

class AuditCategories(BaseModel):
    security: int = 0
    performance: int = 0
    code_quality: int = 0
    architecture: int = 0
    maintainability: int = 0
    dependencies: int = 0

class AuditResult(BaseModel):
    audit_id: str
    repo_id: str
    commit_sha: str
    overall_score: int
    risk_level: Literal["low", "medium", "high", "critical"]
    engine_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    categories: AuditCategories
    findings: List[Finding] = []
    
    # Metadata
    loc: int = 0
    language: str = "Unknown"
