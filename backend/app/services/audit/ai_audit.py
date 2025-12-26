import json
import logging
from typing import List, Dict, Any
from groq import AsyncGroq
from app.models.scan import RiskItem, AuditReport, AuditSummary, FragilityMap, Roadmap, SecurityReliabilityItem

logger = logging.getLogger(__name__)

class AuditAI:
    def __init__(self, client: AsyncGroq):
        self.client = client

    async def generate_insights(self, top_risks: List[RiskItem], repo_context: Dict[str, Any], snippets: Dict[str, str]) -> AuditReport:
        """
        Generate comprehensive audit report based on top risks and repo context.
        """
        if not top_risks:
             return self._fallback_report("No significant risks detected based on metrics.")

        # Prepare Findings Context for LLM
        findings_context = []
        for item in top_risks:
            findings_context.append({
                "file": item.affected_areas[0] if item.affected_areas else "Unknown",
                "type": item.title,
                "severity": item.severity,
                "metrics": item.why_it_matters # We are passing the metric reasoning here
            })

        prompt = f"""
        You are a Principal Software Architect explaining the results of a deterministic "Codebase Health Audit".

        CONTEXT:
        We have computationally identified the following RISK FINDINGS based on strict metric thresholds:
        {json.dumps(findings_context, indent=2)}

        SOURCE CODE SNIPPETS (For context only):
        {json.dumps(snippets, indent=2)}

        REPOSITORY CONTEXT:
        {json.dumps(repo_context, indent=2)}

        INSTRUCTIONS:
        1. "Executive Summary": Analyze the findings and generate health scores (0-100) for each dimension:
           - maintainability: Based on complexity, code organization, readability (higher is better)
           - security: Based on security-related findings (higher is better)  
           - performance: Inferred from complexity and architectural issues (higher is better)
           - testing_confidence: Based on test coverage findings (higher is better)
           - code_quality: Based on code quality issues, patterns, and maintainability (higher is better)
           - architecture: Based on structural issues, coupling, module organization (higher is better)
        
        2. "Explainer": For the top findings, explain WHY the metrics (Complexity, Churn, etc.) are problematic.
        
        3. "Roadmap": Generate remedial actions categorized by urgency.

        SCORING GUIDANCE:
        - 90-100: Excellent, minimal issues
        - 70-89: Good, minor improvements needed
        - 50-69: Moderate, noticeable issues to address
        - 30-49: Poor, significant problems
        - 0-29: Critical, major refactoring required
        
        Consider the severity and count of findings:
        - Each Critical finding: -15 points from baseline
        - Each High finding: -10 points
        - Each Medium finding: -5 points
        - Each Low finding: -2 points

        OUTPUT CONTRACT (JSON ONLY):
        {{
            "summary": {{
                "maintainability": 75,  # INTEGER 0-100
                "security": 85,         # INTEGER 0-100
                "performance": 70,      # INTEGER 0-100
                "testing_confidence": 60, # INTEGER 0-100
                "code_quality": 75,     # INTEGER 0-100
                "architecture": 80,     # INTEGER 0-100
                "overview": "Short executive summary explaining the overall health."
            }},
            "fragility_map": {{
                "high_risk_modules": ["file1", "file2"], # Must match finding files
                "change_sensitive_areas": []
            }},
            "security_reliability": [], # Add items ONLY if you see explicit security risks
            "roadmap": {{
                "fix_now": ["Action for Critical/High Findings"],
                "fix_next": ["Action for Medium Findings"],
                "defer": ["Action for Low Findings or improvements"]
            }},
            "executive_takeaway": "One powerful sentence summarizing the audit results."
        }} 
        """

        try:
            res = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a Principal Architect. strictly output JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            
            # Construct Report
            return AuditReport(
                summary=AuditSummary(**data.get("summary", {})),
                top_risks=top_risks, # Pass through the computed risks
                fragility_map=FragilityMap(**data.get("fragility_map", {})),
                security_reliability=[SecurityReliabilityItem(**item) for item in data.get("security_reliability", [])],
                roadmap=Roadmap(**data.get("roadmap", {})),
                executive_takeaway=data.get("executive_takeaway", "Audit completed.")
            )

        except Exception as e:
            logger.error(f"AuditAI Error: {e}")
            return self._fallback_report(f"AI Analysis Failed: {str(e)}")

    def _fallback_report(self, message: str) -> AuditReport:
        return AuditReport(
            summary=AuditSummary(
                maintainability=50, 
                security=50, 
                performance=50, 
                testing_confidence=50,
                code_quality=50,
                architecture=50,
                overview=message
            ),
            top_risks=[],
            fragility_map=FragilityMap(),
            roadmap=Roadmap(),
            executive_takeaway=message
        )
