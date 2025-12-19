import json
import logging
from typing import List, Dict, Any
from groq import AsyncGroq
from app.models.scan import RiskItem, AuditReport, AuditSummary, FragilityMap, Roadmap, SecurityReliabilityItem

logger = logging.getLogger(__name__)

class AuditAI:
    def __init__(self, client: AsyncGroq):
        self.client = client

    async def generate_insights(self, top_risks: List[RiskItem], repo_context: Dict[str, Any]) -> AuditReport:
        """
        Generate comprehensive audit report based on top risks and repo context.
        """
        if not top_risks:
            return self._fallback_report("No significant risks detected.")

        # Prepare context for LLM (Truncate to save tokens)
        risk_context = []
        for item in top_risks[:5]: # Analyze top 5 only
            risk_context.append({
                "module": item.affected_areas[0] if item.affected_areas else "Unknown",
                "score_components": {
                    "complexity": "High" if "Complexity" in item.why_it_matters else "Normal",
                    "churn": "High" if "Changes" in item.why_it_matters else "Normal"
                }
            })

        prompt = f"""
        You are a Principal Software Architect performing a "Codebase Health Audit".
        
        CONTEXT:
        We have analyzed a repository and identified the following HIGH RISK areas based on Churn and Complexity heuristics:
        {json.dumps(risk_context, indent=2)}

        Repo Stats: {json.dumps(repo_context, indent=2)}

        INSTRUCTIONS:
        Generate a high-signal engineering report.
        1. Synthesize a "Fragility Map": Which areas are likely to break?
        2. Propose a "Roadmap": What should we fix NOW vs LATER?
        3. Security & Reliability: Infer potential risks based on the high-churn/high-complexity modules (e.g., if auth module is high churn, flag security risk).
        
        OUTPUT CONTRACT (JSON ONLY):
        {{
            "summary": {{
                "maintainability": "low"|"medium"|"high",
                "security": "low"|"medium"|"high",
                "performance": "low"|"medium"|"high",
                "testing_confidence": "low"|"medium"|"high",
                "overview": "1-2 sentence executive summary."
            }},
            "fragility_map": {{
                "high_risk_modules": ["module1", "module2"],
                "change_sensitive_areas": ["area1", "area2"]
            }},
            "security_reliability": [
                {{
                    "finding": "Potential auth bypass regression",
                    "severity": "urgent",
                    "context": "High churn in auth_service.py suggests instability."
                }}
            ],
            "roadmap": {{
                "fix_now": ["Refactor Auth", "Add tests to Payment"],
                "fix_next": ["Decouple User Service"],
                "defer": ["UI cleanup"]
            }},
            "executive_takeaway": "One powerful sentence for the CTO."
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
