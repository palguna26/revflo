from typing import List, Dict
import json
import uuid
from groq import AsyncGroq

class CodeAntEngine:
    """
    Quality & Security Layer:
    - Static Analysis
    - Security Vulnerability Detection (OWASP)
    - Code Pattern Review
    """
    def __init__(self, client: AsyncGroq):
        self.client = client

    async def review_diff(self, title: str, description: str, diff: str, checklist: List[Dict]) -> Dict:
        checklist_str = json.dumps(checklist)
        
        prompt = f"""
        You are CodeAnt — a build-breaker and merge gatekeeper.

        Your job is to decide whether this Pull Request must be BLOCKED or ALLOWED.
        You are not an assistant. You do not negotiate.

        INPUT:
        PR Title: {title}
        Checklist: {checklist_str}
        Code Diff:
        {diff[:15000]}

        EVALUATION RULES:

        1. Checklist Judgment
        For each checklist item:
        - PASS: Clear evidence exists in the diff.
        - FAIL: Evidence contradicts or requirement is unmet.
        - INDETERMINATE: Evidence is missing or diff is insufficient.

        INDETERMINATE ALWAYS BLOCKS MERGE.

        2. Security Scan (Mandatory)
        Check ONLY for:
        - SQL Injection
        - XSS
        - Hardcoded secrets
        - Broken access control

        ANY critical security issue → MERGE = NO.

        3. Merge Decision & Block Reason
        If ANY checklist item is FAIL or INDETERMINATE → MERGE = NO.

        Determining Block Reason (Select ONE):
        - BLOCK_CHECKLIST_FAILED: One or more requirements failed validation.
        - BLOCK_INDETERMINATE_EVIDENCE: One or more requirements are indeterminate.
        - BLOCK_SECURITY_CRITICAL: Critical security flaw detected.
        - BLOCK_INSUFFICIENT_ISSUE_SPEC: The checklist itself indicates the Issue was too vague (e.g. "Issue description is insufficient...").

        COMMENT RULES (GitHub-Ready):
        Each failed/indeterminate item produces ONE comment with:
        - Violation (what is wrong/missing)
        - Required fix (what must change)
        - Consequence (why this matters - e.g. "Prevents runtime crash", "Ensures data integrity")

        Tone:
        - Direct
        - Imperative
        - No politeness
        - No hedging

        OUTPUT FORMAT (STRICT JSON):
        {{
          "merge_decision": false,
          "block_reason": "BLOCK_CHECKLIST_FAILED" | "BLOCK_INDETERMINATE_EVIDENCE" | "BLOCK_SECURITY_CRITICAL" | "BLOCK_INSUFFICIENT_ISSUE_SPEC" | null,
          "summary": "Blocked: 1 failed requirement.",
          "health_score": <int 0-100 start at 100, -20 per fail>,
          "checklist_status": [
              {{ "id": "...", "status": "passed"|"failed"|"indeterminate", "reasoning": "Evidence found in file X..." }}
          ],
          "issues": [
              {{
                  "type": "checklist_violation"|"security",
                  "severity": "critical"|"high"|"medium",
                  "file": "path/to/file",
                  "line": <int>,
                  "message": "Line <N>: <Violation>. <Fix>. <Consequence>.",
                  "suggestion": "<Fixed Code Snippet>"
              }}
          ]
        }}
        """
        
        try:
            res = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are CodeAnt Security Auditor. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant", # Or larger model if available
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=15.0 # 15s timeout for heavier analysis
            )
            data = json.loads(res.choices[0].message.content)
            
            # Map raw AI output to strict CodeHealthIssue schema
            issues = []
            for issue in data.get("issues", []):
                issues.append({
                    "id": str(uuid.uuid4()),
                    "severity": issue.get("severity", "low"),
                    "category": issue.get("type", "general"), # map type -> category
                    "message": issue.get("message", "No description"),
                    "file_path": issue.get("file", "unknown"), # map file -> file_path
                    "line_number": issue.get("line"),
                    "suggestion": issue.get("suggestion")
                })
            
            data["issues"] = issues
            # Ensure merge_decision is present, default to False if missing (safe fail)
            if "merge_decision" not in data:
                data["merge_decision"] = False
            
            # Ensure block_reason is present if blocked
            if not data["merge_decision"] and "block_reason" not in data:
                data["block_reason"] = "BLOCK_CHECKLIST_FAILED" # Default fallback
                
            return data
        except Exception as e:
            print(f"CodeAntEngine Error: {e}")
            return {
                "issues": [], 
                "health_score": 0, 
                "summary": "Analysis Failed", 
                "merge_decision": False,
                "block_reason": "BLOCK_INDETERMINATE_EVIDENCE" # Safe fallback
            }

