"""
Security Dimension Scanner (V3)
Detects security vulnerabilities and risks

Rules:
- Placeholder for Phase 3
- Future: Hardcoded secrets, SQL injection, dependency vulnerabilities
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


class SecurityScanner(DimensionScanner):
    """
    Security dimension scanner.
    
    Phase 3: Placeholder (no rules yet)
    Future phases: Dependency vulnerabilities, secret detection, etc.
    """
    
    @property
    def dimension_name(self) -> str:
        return "security"
    
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """Run security scan."""
        logger.info(f"Starting Security scan for {repo_context.repo_id}")
        
        scan_result = DimensionScanResult(
            audit_run_id=repo_context.repo_id,
            repo_id=repo_context.repo_id,
            scan_type="security",
            status="running",
            started_at=datetime.utcnow()
        )
        
        findings: List[Finding] = []
        files_analyzed = len(metric_cache)
        
        # Phase 3: No security rules yet - placeholder
        # Future: Add detection for:
        # - Hardcoded secrets/API keys
        # - SQL injection patterns
        # - XSS vulnerabilities
        # - Dependency vulnerabilities (npm audit, pip-audit)
        
        # Calculate score (100 if no issues)
        score = self.calculate_score(findings)
        
        # Update scan result
        scan_result.score = score
        scan_result.findings = findings
        scan_result.files_analyzed = files_analyzed
        scan_result.files_from_cache = files_analyzed
        scan_result.metrics = {
            "total_findings": len(findings)
        }
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        if scan_result.started_at and scan_result.completed_at:
            duration = scan_result.completed_at - scan_result.started_at
            scan_result.duration_ms = int(duration.total_seconds() * 1000)
        
        logger.info(
            f"Security scan completed: score={score} (placeholder - no rules yet)"
        )
        
        return scan_result
    
    def calculate_score(self, findings: List[Finding]) -> int:
        """Calculate security score."""
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
