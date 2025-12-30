"""
Code Quality Dimension Scanner (V3)
First dimension scanner implementation

Detects:
- Large files (monoliths)
- Complex modules
- Code quality issues

Phase 2: Initial implementation with V2 rule extraction
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


class CodeQualityScanner(DimensionScanner):
    """
    Code Quality dimension scanner.
    
    Rules (extracted from V2 risk_engine):
    1. Large File: loc > 300 (medium severity)
    2. Complex Module: complexity > 20 (medium severity)
    """
    
    # Rule thresholds (configurable via .revflo.yml in future)
    LARGE_FILE_LOC = 300
    COMPLEX_MODULE_COMPLEXITY = 20
    
    @property
    def dimension_name(self) -> str:
        return "code_quality"
    
    async def scan(
        self,
        repo_context: RepoContext,
        changed_files: Set[str],
        metric_cache: Dict[str, FileMetrics]
    ) -> DimensionScanResult:
        """
        Run code quality scan.
        
        Phase 2: Analyzes all files (incremental support in Phase 4)
        """
        logger.info(f"Starting Code Quality scan for {repo_context.repo_id}")
        
        # Create scan result
        scan_result = DimensionScanResult(
            audit_run_id=repo_context.repo_id,  # Will be set by orchestrator
            repo_id=repo_context.repo_id,
            scan_type="code_quality",
            status="running",
            started_at=datetime.utcnow()
        )
        
        findings: List[Finding] = []
        files_analyzed = 0
        files_from_cache = 0
        
        # Analyze all files in cache
        for file_path, metrics in metric_cache.items():
            files_analyzed += 1
            files_from_cache += 1  # Phase 2: all from cache (orchestrator provides)
            
            # Rule 1: Large File
            if metrics.loc > self.LARGE_FILE_LOC:
                findings.append(Finding(
                    id=f"QUAL001-{file_path}",
                    rule_id="QUAL001",
                    severity="medium",
                    category="large_file",
                    file_path=file_path,
                    title="Large File",
                    description=f"File has {metrics.loc} lines, suggesting too many responsibilities (threshold: {self.LARGE_FILE_LOC})",
                    metrics={
                        "loc": metrics.loc,
                        "threshold": self.LARGE_FILE_LOC
                    }
                ))
            
            # Rule 2: Complex Module
            if metrics.complexity > self.COMPLEX_MODULE_COMPLEXITY:
                findings.append(Finding(
                    id=f"QUAL002-{file_path}",
                    rule_id="QUAL002",
                    severity="medium",
                    category="complex_module",
                    file_path=file_path,
                    title="Complex Module",
                    description=f"High cyclomatic complexity ({metrics.complexity}) makes this module hard to maintain (threshold: {self.COMPLEX_MODULE_COMPLEXITY})",
                    metrics={
                        "complexity": metrics.complexity,
                        "threshold": self.COMPLEX_MODULE_COMPLEXITY
                    }
                ))
        
        # Calculate score (deterministic)
        score = self.calculate_score(findings)
        
        # Update scan result
        scan_result.score = score
        scan_result.findings = findings
        scan_result.files_analyzed = files_analyzed
        scan_result.files_from_cache = files_from_cache
        scan_result.metrics = {
            "large_file_count": len([f for f in findings if f.rule_id == "QUAL001"]),
            "complex_module_count": len([f for f in findings if f.rule_id == "QUAL002"]),
            "total_findings": len(findings)
        }
        scan_result.status = "completed"
        scan_result.completed_at = datetime.utcnow()
        
        # Calculate duration
        if scan_result.started_at and scan_result.completed_at:
            duration = scan_result.completed_at - scan_result.started_at
            scan_result.duration_ms = int(duration.total_seconds() * 1000)
        
        logger.info(
            f"Code Quality scan completed: score={score}, "
            f"findings={len(findings)}, files={files_analyzed}"
        )
        
        # Phase 5: AI explanation (if score < 90 and findings exist)
        if score < 90 and len(findings) > 0:
            try:
                from app.services.audit.dimension_ai import DimensionAI
                ai_service = DimensionAI()
                ai_result = await ai_service.explain_findings("code_quality", scan_result)
                
                if ai_result:
                    scan_result.ai_summary = ai_result.get("summary", "")
                    if "top_recommendation" in ai_result:
                        scan_result.recommendations = [ai_result["top_recommendation"]]
                    
                    logger.info(f"AI explanation generated for Code Quality")
            except Exception as e:
                logger.warning(f"AI explanation failed: {e}")
        
        return scan_result
    
    def calculate_score(self, findings: List[Finding]) -> int:
        """
        Calculate code quality score from findings.
        
        Deterministic algorithm:
        - Start at 100
        - Deduct 5 points per medium severity finding
        - Floor at 0
        """
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
