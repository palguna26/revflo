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

        INSTRUCTIONS:
        1. "Executive Summary": Summarize the overall health based on the finding severity and count.
        2. "Explainer": For the top findings, explain WHY the metrics (Complexity, Churn, etc.) are problematic for that specific code. Use the snippets to give concrete examples.
        3. "Roadmap": Generate a remedial action for each finding. 
           CRITICAL: logic must be 1:1. Finding A -> Fix A. Do NOT invent new tasks.

        OUTPUT CONTRACT (JSON ONLY):
        {{
            "summary": {{
                "maintainability": "low"|"medium"|"high", # Infer from finding severity
                "security": "low"|"medium"|"high",
                "performance": "low"|"medium"|"high",
                "testing_confidence": "low"|"medium"|"high",
                "overview": "Short executive summary explaining the score."
            }},
            "fragility_map": {{
                "high_risk_modules": ["file1", "file2"], # Must match finding files
                "change_sensitive_areas": []
            }},
            "security_reliability": [], # Leave empty unless you see explicit security risks in findings
            "roadmap": {{
                "fix_now": ["Action for Critical Finding 1", "Action for Critical Finding 2"],
                "fix_next": ["Action for High Finding 1"],
                "defer": ["Action for Medium/Low Findings"]
            }},
            "executive_takeaway": "One powerful sentence summary."
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
                maintainability="medium", security="medium", 
                performance="medium", testing_confidence="medium", 
                overview=message
            ),
            top_risks=[],
            fragility_map=FragilityMap(),
            roadmap=Roadmap(),
            executive_takeaway=message
        )
