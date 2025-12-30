"""
Performance Dimension Scanner (V3)
Detects performance issues and inefficiencies

Rules:
- High complexity as performance proxy (Phase 3)
- Future: N+1 query detection, algorithm analysis
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


class PerformanceScanner(DimensionScanner):
    """
    Performance dimension scanner.
    
    Rules (Phase 3 - basic):
    1. High Complexity: complexity > 25 (performance risk proxy)
    """
    
    # Rule thresholds
    HIGH_COMPLEXITY_THRESHOLD = 25
    
    @property
    def dimension_name(self) -> str:
        return "performance"
    
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """Run performance scan."""
        logger.info(f"Starting Performance scan for {repo_context.repo_id}")
        
        scan_result = DimensionScanResult(
            audit_run_id=repo_context.repo_id,
            repo_id=repo_context.repo_id,
            scan_type="performance",
            status="running",
            started_at=datetime.utcnow()
        )
        
        findings: List[Finding] = []
        files_analyzed = 0
        files_from_cache = 0
        
        for file_path, metrics in metric_cache.items():
            files_analyzed += 1
            files_from_cache += 1
            
            # Rule 1: High Complexity (performance risk proxy)
            if metrics.complexity > self.HIGH_COMPLEXITY_THRESHOLD:
                findings.append(Finding(
                    id=f"PERF001-{file_path}",
                    rule_id="PERF001",
                    severity="medium",
                    category="high_complexity",
                    file_path=file_path,
                    title="Performance Risk",
                    description=f"Very high complexity ({metrics.complexity}) may indicate performance issues",
                    metrics={
                        "complexity": metrics.complexity,
                        "threshold": self.HIGH_COMPLEXITY_THRESHOLD
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
            "high_complexity_count": len(findings),
            "total_findings": len(findings)
        }
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        if scan_result.started_at and scan_result.completed_at:
            duration = scan_result.completed_at - scan_result.started_at
            scan_result.duration_ms = int(duration.total_seconds() * 1000)
        
        logger.info(
            f"Performance scan completed: score={score}, findings={len(findings)}"
        )
        
        return scan_result
    
    def calculate_score(self, findings: List[Finding]) -> int:
        """Calculate performance score."""
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
