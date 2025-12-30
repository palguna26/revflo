"""
Testing Confidence Dimension Scanner (V3)
Detects files lacking test coverage

Rules:
- No Tests: Substantial files without tests (from V2)
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


class TestingConfidenceScanner(DimensionScanner):
    """
    Testing Confidence dimension scanner.
    
    Rules (extracted from V2 risk_engine):
    1. No Tests: loc > 100 AND has_test = false (medium severity)
    """
    
    # Rule thresholds
    NO_TESTS_MIN_LOC = 100
    
    @property
    def dimension_name(self) -> str:
        return "testing_confidence"
    
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """Run testing confidence scan."""
        logger.info(f"Starting Testing Confidence scan for {repo_context.repo_id}")
        
        scan_result = DimensionScanResult(
            audit_run_id=repo_context.repo_id,
            repo_id=repo_context.repo_id,
            scan_type="testing_confidence",
            status="running",
            started_at=datetime.utcnow()
        )
        
        findings: List[Finding] = []
        files_analyzed = 0
        files_from_cache = 0
        files_with_tests = 0
        
        for file_path, metrics in metric_cache.items():
            files_analyzed += 1
            files_from_cache += 1
            
            if metrics.has_test:
                files_with_tests += 1
            
            # Rule 1: No Tests
            if metrics.loc > self.NO_TESTS_MIN_LOC and not metrics.has_test:
                findings.append(Finding(
                    id=f"TEST001-{file_path}",
                    rule_id="TEST001",
                    severity="medium",
                    category="no_tests",
                    file_path=file_path,
                    title="No Tests",
                    description=f"Substantial file ({metrics.loc} lines) without test coverage",
                    metrics={
                        "loc": metrics.loc,
                        "has_test": False,
                        "threshold": self.NO_TESTS_MIN_LOC
                    }
                ))
        
        # Calculate score
        score = self.calculate_score(findings)
        
        # Test coverage percentage
        coverage_pct = 0
        if files_analyzed > 0:
            coverage_pct = int((files_with_tests / files_analyzed) * 100)
        
        # Update scan result
        scan_result.score = score
        scan_result.findings = findings
        scan_result.files_analyzed = files_analyzed
        scan_result.files_from_cache = files_from_cache
        scan_result.metrics = {
            "no_tests_count": len(findings),
            "files_with_tests": files_with_tests,
            "test_coverage_pct": coverage_pct,
            "total_findings": len(findings)
        }
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        if scan_result.started_at and scan_result.completed_at:
            duration = scan_result.completed_at - scan_result.started_at
            scan_result.duration_ms = int(duration.total_seconds() * 1000)
        
        logger.info(
            f"Testing Confidence scan completed: score={score}, "
            f"coverage={coverage_pct}%, findings={len(findings)}"
        )
        
        return scan_result
    
    def calculate_score(self, findings: List[Finding]) -> int:
        """Calculate testing confidence score."""
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
