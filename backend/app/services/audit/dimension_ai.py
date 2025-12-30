"""
Dimension AI Service (V3)
Provides AI explanations for dimension scan results

Phase 5: Small, focused AI calls per dimension with token limits
"""
import logging
import json
from typing import List, Optional
from groq import AsyncGroq
from app.models.audit_v3 import DimensionScanResult, Finding
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DimensionAI:
    """
    AI service for dimension-specific explanations.
    
    Token budgets per dimension:
    - Security: 600 tokens
    - Performance: 500 tokens
    - Code Quality: 400 tokens
    - Architecture: 700 tokens
    - Maintainability: 300 tokens
    - Testing Confidence: 200 tokens
    """
    
    # Token budgets
    MAX_TOKENS = {
        "security": 600,
        "performance": 500,
        "code_quality": 400,
        "architecture": 700,
        "maintainability": 300,
        "testing_confidence": 200
    }
    
    # Prompt templates
    PROMPTS = {
        "security": """You are a security engineer. Explain these security findings briefly:
{findings}

Output JSON with:
- summary (1 sentence)
- top_recommendation (1 action item)""",
        
        "performance": """You are a performance engineer. Explain these performance findings briefly:
{findings}

Output JSON with:
- summary (1 sentence)
- top_recommendation (1 action item)""",
        
        "code_quality": """You are a code quality expert. Explain these code quality findings briefly:
{findings}

Output JSON with:
- summary (1 sentence)
- top_recommendation (1 action item)""",
        
        "architecture": """You are a software architect. Explain these architectural findings briefly:
{findings}

Output JSON with:
- summary (1 sentence)
- top_recommendation (1 action item)""",
        
        "maintainability": """You are a maintenance engineer. Explain these maintainability findings briefly:
{findings}

Output JSON with:
- summary (1 sentence)
- top_recommendation (1 action item)""",
        
        "testing_confidence": """You are a test engineer. Explain these testing findings briefly:
{findings}

Output JSON with:
- summary (1 sentence)
- top_recommendation (1 action item)"""
    }
    
    def __init__(self):
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.groq_api_key)
    
    async def explain_findings(
        self,
        dimension: str,
        scan_result: DimensionScanResult
    ) -> Optional[dict]:
        """
        Generate AI explanation for dimension findings.
        
        Conditions:
        - Skip if no findings
        - Skip if score >= 90 (healthy)
        - Skip if no budget for this dimension
        """
        # Check if AI should run
        if not self._should_run_ai(scan_result):
            return None
        
        # Get token budget
        max_tokens = self.MAX_TOKENS.get(dimension, 400)
        
        try:
            # Build prompt
            prompt = self._build_prompt(dimension, scan_result.findings)
            
            # Truncate if too long
            if len(prompt) > max_tokens * 4:  # Rough token estimate
                prompt = prompt[:max_tokens * 4]
            
            # Call LLM
            response = await self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"AI explanation generated for {dimension}")
            return result
            
        except Exception as e:
            logger.error(f"AI explanation failed for {dimension}: {e}")
            return None
    
    def _should_run_ai(self, scan_result: DimensionScanResult) -> bool:
        """Determine if AI should run"""
        # Skip if no findings
        if len(scan_result.findings) == 0:
            return False
        
        # Skip if score is healthy
        if scan_result.score >= 90:
            return False
        
        return True
    
    def _build_prompt(self, dimension: str, findings: List[Finding]) -> str:
        """Build prompt with findings"""
        # Limit to top 5 findings by severity
        top_findings = sorted(
            findings,
            key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(f.severity, 4)
        )[:5]
        
        # Format findings
        findings_text = "\n".join([
            f"- {f.severity.upper()}: {f.title} in {f.file_path} - {f.description}"
            for f in top_findings
        ])
        
        # Get template
        template = self.PROMPTS.get(dimension, self.PROMPTS["code_quality"])
        
        return template.format(findings=findings_text)
