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
        You are CodeAnt, an expert Security & Code Quality Auditor.
        
        Context:
        PR Title: {title}
        Checklist: {checklist_str}
        
        Diff:
        {diff[:15000]}
        
        Analyze for:
        1. Security Vulnerabilities (SQLi, XSS, Secrets, Auth logic).
        2. Code Quality (Anti-patterns, Performance).
        3. Checklist Satisfaction (Pass/Fail/Unknown).
        
        Output JSON (Strict):
        {{
            "summary": "High level summary",
            "health_score": 0-100,
            "checklist_status": [
                {{"id": "...", "status": "passed"|"failed"|"unknown", "reasoning": "..."}}
            ],
            "issues": [
                {{
                    "type": "security"|"quality",
                    "severity": "critical"|"high"|"medium"|"low",
                    "file": "path",
                    "line": 123,
                    "message": "Description",
                    "suggestion": "Fix details"
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
            return data
        except Exception as e:
            print(f"CodeAntEngine Error: {e}")
            return {"issues": [], "health_score": 0, "summary": "Analysis Failed"}

