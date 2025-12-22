from typing import List, Dict, Any
from groq import AsyncGroq
from app.core.config import get_settings
from app.services.ai.quantum import QuantumEngine
from app.services.ai.codeant import CodeAntEngine
from app.services.ai.qodo import QodoEngine
from app.services.audit.scanner import audit_scanner 

class RevFloAssistant:
    """
    Unified AI Assistant Service for RevFlo.
    Exposes Intent, Change, and Risk intelligence layers.
    """
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncGroq(api_key=self.settings.groq_api_key)
        
        # Internal Engines (Hidden from consumers)
        self._quantum = QuantumEngine(self.client)   # Intent
        self._codeant = CodeAntEngine(self.client)   # Change Review
        self._qodo = QodoEngine(self.client)         # Change Tests
        self._scanner = audit_scanner                # System Risk

    async def understand_intent(self, title: str, body: str) -> List[Dict]:
        """
        Layer 1: Intent Intelligence.
        Converts vague issue descriptions into actional execution contracts (checklists).
        """
        return await self._quantum.generate_checklist(title, body)

    async def verify_change(self, title: str, description: str, diff: str, checklist_items: List[dict]) -> dict:
        """
        Layer 2: Change Intelligence.
        Validates correctness (CodeAnt) and ensures safety (Qodo).
        """
        # 1. Review Logic (Correctness & Risk)
        review_data = await self._codeant.review_diff(title, description, diff, checklist_items)
        
        # 2. Test Generation (Safety)
        tests = await self._qodo.generate_tests(diff)
        
        # 3. Unified Result
        return {
            "summary": review_data.get("summary"),
            "health_score": review_data.get("health_score"),
            "code_health": review_data.get("issues", []),
            "checklist_items": review_data.get("checklist_status", []),
            "suggested_tests": tests
        }

    async def assess_risk(self, scan_record, repo_url: str, token: str):
        """
        Layer 3: System Intelligence.
        Performs a deep snapshot audit of the repository to identify architectural and security risks.
        """
        await self._scanner._process_scan(scan_record, repo_url, token)

    async def generate_fix(self, issue_description: str, code_snippet: str) -> str:
        """
        Expose Fix Generation from Qodo (Layer 2)
        """
        return await self._qodo.generate_fix(issue_description, code_snippet)

    async def validate_checklist(self, diff: str, checklist: List[Dict]) -> List[Dict]:
        """
        Expose Checklist Validation from CodeAnt (Layer 2)
        Returns list of checklist results.
        """
        # Title and description are optional for just checklist validation in this context
        result = await self._codeant.review_diff(title="Checklist Validation", description="N/A", diff=diff, checklist=checklist)
        return result.get("checklist_status", [])

# Singleton Instance
assistant = RevFloAssistant()
