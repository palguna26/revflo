from typing import List, Dict
from groq import AsyncGroq
from app.core.config import get_settings
from app.services.ai.quantum import QuantumEngine
from app.services.ai.codeant import CodeAntEngine
from app.services.ai.qodo import QodoEngine

class AIReviewService:
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncGroq(api_key=self.settings.groq_api_key)
        
        # Initialize Sub-Engines
        self.quantum = QuantumEngine(self.client)
        self.codeant = CodeAntEngine(self.client)
        self.qodo = QodoEngine(self.client)

    async def generate_checklist(self, title: str, body: str) -> List[Dict]:
        """Delegates to QuantumEngine"""
        return await self.quantum.generate_checklist(title, body)

    async def perform_unified_review(self, title: str, description: str, diff: str, checklist_items: List[dict]) -> dict:
        """
        Orchestrates CodeAnt (Review) and Qodo (Tests)
        """
        # 1. Run Analysis (CodeAnt)
        review_data = await self.codeant.review_diff(title, description, diff, checklist_items)
        
        # 2. Generate Tests (Qodo)
        tests = await self.qodo.generate_tests(diff)
        
        # 3. Merge Results
        return {
            "summary": review_data.get("summary"),
            "health_score": review_data.get("health_score"),
            "code_health": review_data.get("issues", []),
            "checklist_items": review_data.get("checklist_status", []),
            "suggested_tests": tests
        }

# Singleton Instance
ai_service = AIReviewService()
