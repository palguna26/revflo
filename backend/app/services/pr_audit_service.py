from typing import List, Dict
from app.models.user import User
from app.models.scan import RiskItem
from app.services.github import github_service
import logging

logger = logging.getLogger(__name__)

class PRAuditService:
    """
    Service for posting audit findings to GitHub PRs as comments.
    V2 Feature: PR Comment Integration
    """
    
    # Rate limiting constants
    MAX_INLINE_COMMENTS = 20  # Warn if more than this many inline comments
    
    async def post_audit_to_pr(
        self, 
        owner: str, 
        repo_name: str, 
        pr_number: int, 
        findings: List[RiskItem],
        commit_sha: str,
        user: User,
        severity_filter: str = "critical_high"
    ) -> Dict:
        """
        Post audit findings as comments on a GitHub PR.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            pr_number: Pull request number
            findings: List of audit findings (RiskItem)
            commit_sha: Commit SHA to attach comments to
            user: User making the request
            severity_filter: "all", "critical_high", or "critical"
        
        Returns:
            Dict with posted_count, error_count, warnings, and details
        """
        # Filter findings based on severity
        filtered_findings = self._filter_findings(findings, severity_filter)
        
        posted_comments = []
        errors = []
        warnings = []
        
        # Rate limit warning
        inline_count = sum(1 for f in filtered_findings if f.file_path and f.line_number)
        if inline_count > self.MAX_INLINE_COMMENTS:
            warnings.append(
                f"High number of inline comments ({inline_count}). "
                f"This may consume significant API rate limit quota."
            )
            logger.warning(f"Posting {inline_count} inline comments to PR #{pr_number}")
        
        # Post a summary comment first
        summary = self._generate_summary_comment(filtered_findings, len(findings), severity_filter)
        try:
            result = await github_service.post_pr_comment(
                owner, repo_name, pr_number, summary, user
            )
            posted_comments.append({"type": "summary", "comment_id": result.get("id")})
            logger.info(f"Posted summary comment to PR #{pr_number}")
        except Exception as e:
            logger.error(f"Failed to post summary comment to PR #{pr_number}: {e}")
            errors.append({"type": "summary", "error": str(e)})
            # If summary fails, still try to post inline comments
        
        # Post inline comments for findings with file/line info
        for finding in filtered_findings:
            if finding.file_path and finding.line_number:
                comment_body = self._format_finding_comment(finding)
                try:
                    result = await github_service.post_pr_review_comment(
                        owner, repo_name, pr_number,
                        commit_sha, finding.file_path, comment_body, finding.line_number,
                        user
                    )
                    posted_comments.append({
                        "type": "inline",
                        "finding_id": finding.id,
                        "file": finding.file_path,
                        "line": finding.line_number,
                        "comment_id": result.get("id")
                    })
                except Exception as e:
                    # Graceful degradation: log error but continue
                    error_msg = str(e)
                    logger.warning(f"Failed to post inline comment for {finding.file_path}:{finding.line_number}: {error_msg}")
                    
                    # Check for rate limiting
                    if "rate limit" in error_msg.lower() or "403" in error_msg:
                        warnings.append("GitHub API rate limit may have been reached")
                    
                    errors.append({
                        "finding_id": finding.id,
                        "file": finding.file_path,
                        "line": finding.line_number,
                        "error": error_msg
                    })
        
        result = {
            "status": "completed",
            "posted_count": len(posted_comments),
            "error_count": len(errors),
            "warnings": warnings,
            "filtered_findings_count": len(filtered_findings),
            "total_findings_count": len(findings),
            "posted_comments": posted_comments,
            "errors": errors
        }
        
        logger.info(
            f"PR #{pr_number} audit posted: {len(posted_comments)} comments, "
            f"{len(errors)} errors, {len(warnings)} warnings"
        )
        
        return result
    
    def _filter_findings(self, findings: List[RiskItem], severity_filter: str) -> List[RiskItem]:
        """Filter findings based on severity."""
        if severity_filter == "all":
            return findings
        elif severity_filter == "critical_high":
            return [f for f in findings if f.severity in ["critical", "high"]]
        elif severity_filter == "critical":
            return [f for f in findings if f.severity == "critical"]
        return findings
    
    def _generate_summary_comment(
        self, 
        filtered_findings: List[RiskItem], 
        total_findings: int,
        severity_filter: str
    ) -> str:
        """Generate a markdown summary comment for the PR."""
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in filtered_findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
        
        # Build markdown
        comment = "## 🔍 RevFlo Code Audit\n\n"
        comment += "RevFlo has analyzed this repository using **deterministic, metric-driven rules**.\n\n"
        
        # Overall summary
        if not filtered_findings:
            comment += "✅ **No critical or high severity issues found!**\n\n"
            if total_findings > 0:
                comment += f"*Note: {total_findings} lower-severity findings were detected but not shown here.*\n\n"
        else:
            comment += "### 📊 Findings Summary\n\n"
            comment += "| Severity | Count |\n"
            comment += "|----------|-------|\n"
            
            if severity_counts["critical"] > 0:
                comment += f"| 🔴 **Critical** | **{severity_counts['critical']}** |\n"
            if severity_counts["high"] > 0:
                comment += f"| 🟠 **High** | **{severity_counts['high']}** |\n"
            if severity_counts["medium"] > 0:
                comment += f"| 🟡 Medium | {severity_counts['medium']} |\n"
            if severity_counts["low"] > 0:
                comment += f"| 🟢 Low | {severity_counts['low']} |\n"
            
            comment += "\n"
            
            if total_findings > len(filtered_findings):
                comment += f"*Showing **{len(filtered_findings)}** of **{total_findings}** total findings (filter: `{severity_filter}`)*\n\n"
        
        # Explanation of methodology
        comment += "---\n\n"
        comment += "### 📝 About These Findings\n\n"
        comment += "RevFlo uses **static metrics** and **hard-coded rules** to identify risk:\n\n"
        comment += "- **Hotspots**: High complexity + frequent changes\n"
        comment += "- **Large Files**: Files exceeding recommended size limits\n"
        comment += "- **Deep Nesting**: Excessive indentation complexity\n"
        comment += "- **No Tests**: Source files without corresponding test coverage\n\n"
        comment += "*No AI inference is used for decision-making. All findings are deterministic and reproducible.*\n\n"
        comment += "---\n"
        comment += "*Powered by [RevFlo](https://revflo.dev) | Metric-Driven Code Intelligence*"
        
        return comment
    
    def _format_finding_comment(self, finding: RiskItem) -> str:
        """Format a single finding as a markdown comment."""
        emoji_map = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢"
        }
        emoji = emoji_map.get(finding.severity, "⚪")
        
        comment = f"{emoji} **{finding.severity.upper()}**: {finding.rule_type}\n\n"
        comment += f"**Issue**: {finding.description}\n\n"
        
        if finding.explanation:
            comment += f"**Why this matters**: {finding.explanation}\n\n"
        
        # Show metrics that triggered the rule
        if finding.metrics:
            comment += "**Metrics**:\n"
            for key, value in finding.metrics.items():
                comment += f"- `{key}`: **{value}**\n"
            comment += "\n"
        
        # Actionable advice
        if finding.rule_type == "Hotspot":
            comment += "💡 **Recommendation**: Consider refactoring to reduce complexity or splitting into smaller modules.\n"
        elif finding.rule_type == "Large File":
            comment += "💡 **Recommendation**: Break this file into smaller, focused modules.\n"
        elif finding.rule_type == "Deep Nesting":
            comment += "💡 **Recommendation**: Reduce nesting depth using early returns or extracting methods.\n"
        elif finding.rule_type == "No Tests":
            comment += "💡 **Recommendation**: Add unit tests to improve code reliability and maintainability.\n"
        
        comment += "\n---\n*RevFlo | Deterministic Code Analysis*"
        
        return comment

pr_audit_service = PRAuditService()
