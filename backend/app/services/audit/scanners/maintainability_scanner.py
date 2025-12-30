"""
Maintainability Dimension Scanner (V3)
Detects code that is hard to maintain

Rules:
- Hotspot: High complexity + high churn (from V2)
- Future: Coupling analysis, documentation coverage
"""
import logging
from typing import Set, Dict, List
from datetime import datetime
from app.models.audit_v3 import DimensionScanResult, Finding
from app.services.audit.dimension_scanner import (
    DimensionScanner,
    RepoContext,
    FileMetrics
)

logger = logging.getLogger(__name__)


class MaintainabilityScanner(DimensionScanner):
    """
    Maintainability dimension scanner.
    
    Rules (extracted from V2 risk_engine):
    1. Hotspot: complexity > 15 AND churn > 10 (high severity)
    """
    
    # Rule thresholds
    HOTSPOT_COMPLEXITY = 15
    HOTSPOT_CHURN = 10
    
    @property
    def dimension_name(self) -> str:
        return "maintainability"
    
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """Run maintainability scan."""
        logger.info(f"Starting Maintainability scan for {repo_context.repo_id}")
        
        scan_result = DimensionScanResult(
            audit_run_id=repo_context.repo_id,
            repo_id=repo_context.repo_id,
            scan_type="maintainability",
            status="running",
            started_at=datetime.utcnow()
        )
        
        findings: List[Finding] = []
        files_analyzed = 0
        files_from_cache = 0
        
        for file_path, metrics in metric_cache.items():
            files_analyzed += 1
            files_from_cache += 1
            
            # Rule 1: Hotspot (high complexity + high churn)
            if metrics.complexity > self.HOTSPOT_COMPLEXITY and metrics.churn_90d > self.HOTSPOT_CHURN:
                findings.append(Finding(
                    id=f"MAINT001-{file_path}",
                    rule_id="MAINT001",
                    severity="high",
                    category="hotspot",
                    file_path=file_path,
                    title="Hotspot",
                    description=f"High complexity ({metrics.complexity}) + frequent changes ({metrics.churn_90d} commits) = instability risk",
                    metrics={
                        "complexity": metrics.complexity,
                        "churn_90d": metrics.churn_90d,
                        "complexity_threshold": self.HOTSPOT_COMPLEXITY,
                        "churn_threshold": self.HOTSPOT_CHURN
                    }
                ))
        
        # Calculate score
        score = self.calculate_score(findings)
        
        # Update scan result
        scan_result.score = score
        scan_result.findings = findings
        scan_result.files_analyzed = files_analyzed
        scan_result.files_from_cache = files_from_cache
        scan_result.metrics = {
            "hotspot_count": len(findings),
            "total_findings": len(findings)
        }
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        if scan_result.started_at and scan_result.completed_at:
            duration = scan_result.completed_at - scan_result.started_at
            scan_result.duration_ms = int(duration.total_seconds() * 1000)
        
        logger.info(
            f"Maintainability scan completed: score={score}, findings={len(findings)}"
        )
        
        return scan_result
    
    def calculate_score(self, findings: List[Finding]) -> int:
        """Calculate maintainability score."""
        score = 100
        
        for finding in findings:
            if finding.severity == "critical":
                score -= 20
            elif finding.severity == "high":
                score -= 10
            elif finding.severity == "medium":
                score -= 5
            elif finding.severity == "low":
                score -= 2
        
        return max(0, score)
