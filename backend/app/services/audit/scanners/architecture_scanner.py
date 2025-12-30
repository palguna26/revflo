"""
Architecture Dimension Scanner (V3)
Detects architectural issues and code structure problems

Rules:
- Deep Nesting: Excessive indentation (from V2)
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


class ArchitectureScanner(DimensionScanner):
    """
    Architecture dimension scanner.
    
    Rules (extracted from V2 risk_engine):
    1. Deep Nesting: indent_depth > 5 (medium severity)
    """
    
    # Rule thresholds
    DEEP_NESTING_THRESHOLD = 5
    
    @property
    def dimension_name(self) -> str:
        return "architecture"
    
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """Run architecture scan."""
        logger.info(f"Starting Architecture scan for {repo_context.repo_id}")
        
        scan_result = DimensionScanResult(
            audit_run_id=repo_context.repo_id,
            repo_id=repo_context.repo_id,
            scan_type="architecture",
            status="running",
            started_at=datetime.utcnow()
        )
        
        findings: List[Finding] = []
        files_analyzed = 0
        files_from_cache = 0
        
        for file_path, metrics in metric_cache.items():
            files_analyzed += 1
            files_from_cache += 1
            
            # Rule 1: Deep Nesting
            if metrics.indent_depth > self.DEEP_NESTING_THRESHOLD:
                findings.append(Finding(
                    id=f"ARCH001-{file_path}",
                    rule_id="ARCH001",
                    severity="medium",
                    category="deep_nesting",
                    file_path=file_path,
                    title="Deep Nesting",
                    description=f"Deep nesting (indent depth: {metrics.indent_depth}) reduces readability and testability",
                    metrics={
                        "indent_depth": metrics.indent_depth,
                        "threshold": self.DEEP_NESTING_THRESHOLD
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
            "deep_nesting_count": len(findings),
            "total_findings": len(findings)
        }
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        if scan_result.started_at and scan_result.completed_at:
            duration = scan_result.completed_at - scan_result.started_at
            scan_result.duration_ms = int(duration.total_seconds() * 1000)
        
        logger.info(
            f"Architecture scan completed: score={score}, findings={len(findings)}"
        )
        
        return scan_result
    
    def calculate_score(self, findings: List[Finding]) -> int:
        """Calculate architecture score."""
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
