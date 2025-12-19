from datetime import datetime
from typing import Optional, List, Literal
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field

class Vulnerability(BaseModel):
    id: str
    severity: Literal["critical", "high", "medium", "low"]
    package_name: str
    description: str
    fixed_version: Optional[str] = None

class ScanResult(Document):
    repo_id: PydanticObjectId
    status: Literal["pending", "processing", "completed", "failed"]
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    vulnerabilities: List[Vulnerability] = []
    summary: str = ""

    class Settings:
        name = "scans"
