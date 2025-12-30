"""
V3 Audit Data Models
Staged multi-scan architecture with dimension-based scoring

IMPORTANT: This is V3-specific. V2 models in scan.py remain unchanged.
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel


# Shared Finding model (can also import from audit_schema.py)
class Finding(BaseModel):
    """Issue discovered by deterministic rules"""
    
    id: str
    rule_id: str  # e.g. "SEC001", "PERF003", "QUAL001"
    severity: Literal["critical", "high", "medium", "low"]
    category: str  # e.g. "sql_injection", "n_plus_one", "large_file"
    
    # Location
    file_path: str
    line_number: Optional[int] = None
    
    # Description
    title: str
    description: str
    
    # Context
    code_snippet: Optional[str] = None
    metrics: Dict[str, Any] = {}  # Rule-specific metrics


class DimensionScanResult(Document):
    """Result of a single dimension scan (Security, Performance, etc.)"""
    
    # Identity
    id: Optional[PydanticObjectId] = None
    audit_run_id: PydanticObjectId
    repo_id: PydanticObjectId
    scan_type: Literal[
        "security",
        "performance", 
        "code_quality",
        "architecture",
        "maintainability",
        "testing_confidence"
    ]
    
    # Status
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    error_message: Optional[str] = None
    
    # Deterministic Results (AI does NOT compute these)
    score: int = 0  # 0-100, calculated by scanner
    findings: List[Finding] = []
    metrics: Dict[str, Any] = {}  # Dimension-specific metrics
    
    # AI-Generated (optional, only for explanation)
    ai_summary: Optional[str] = None
    recommendations: List[str] = []
    
    # Cache efficiency metrics
    files_analyzed: int = 0
    files_from_cache: int = 0
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    class Settings:
        name = "dimension_scans_v3"  # V3-specific collection


class AuditRun(Document):
    """Parent entity representing a complete audit run across all dimensions"""
    
    # Metadata
    id: Optional[PydanticObjectId] = None
    repo_id: PydanticObjectId
    commit_sha: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Results (references to dimension scans)
    security_scan_id: Optional[PydanticObjectId] = None
    performance_scan_id: Optional[PydanticObjectId] = None
    code_quality_scan_id: Optional[PydanticObjectId] = None
    architecture_scan_id: Optional[PydanticObjectId] = None
    maintainability_scan_id: Optional[PydanticObjectId] = None
    testing_scan_id: Optional[PydanticObjectId] = None
    
    # Aggregated metrics (computed from dimension scans)
    overall_score: Optional[int] = None  # Average of dimension scores
    total_issues: int = 0
    
    # V2 Compatibility (optional - for dual-mode)
    legacy_scan_id: Optional[PydanticObjectId] = None  # Points to old ScanResult if V2 also ran
    
    class Settings:
        name = "audit_runs_v3"  # V3-specific collection


class FileMetricCache(Document):
    """Cached file-level metrics to enable incremental scans"""
    
    # Cache key (composite)
    repo_id: PydanticObjectId
    commit_sha: str
    file_path: str
    
    # Shared metrics (used by multiple dimensions)
    loc: int = 0  # Lines of code
    complexity: int = 0  # Cyclomatic complexity
    indent_depth: int = 0  # Maximum indent level
    churn_90d: int = 0  # Commits in last 90 days
    has_test: bool = False  # Test coverage detected
    
    # Language info
    language: str = "unknown"  # "python", "javascript", "typescript", etc.
    
    # Metadata
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    ttl: int = 86400 * 30  # 30 days TTL
    
    class Settings:
        name = "file_metrics_cache"
        indexes = [
            # Composite index for fast lookup
            [("repo_id", 1), ("commit_sha", 1), ("file_path", 1)],
            # TTL index for cleanup
            [("computed_at", 1)]
        ]
