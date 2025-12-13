from typing import List, Dict
import json
from groq import AsyncGroq
from app.core.config import get_settings

class QuantumEngine:
    """
    Core Intelligence Layer:
    - Parses vague issues
    - Generates checklists
    - Assigns priority/complexity
    """
    def __init__(self, client: AsyncGroq):
        self.client = client

    async def generate_checklist(self, title: str, body: str) -> List[Dict]:
        prompt = f"""
        You are RevFlo's Issue Analyst.
        User Issue: "{title}"
        Description: "{body}"
        
        Task:
        1. Understand the core problem.
        2. Break it down into 3-6 actionable, technical acceptance criteria (Checklist).
        3. Assign a Complexity Score (1-10) and Priority (Low/Medium/High/Critical).
        
        Output JSON:
        {{
            "checklist": [{{"text": "...", "required": true}}],
            "complexity": int,
            "priority": "string"
        }}
        """
        
        try:
            res = await self.client.chat.completions.create(
                messages=[
                   {"role": "system", "content": "You are a Technical PM. Output JSON."},
                   {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                timeout=10.0 # 10s timeout
            )
            return json.loads(res.choices[0].message.content).get("checklist", [])
        except Exception as e:
            print(f"QuantumEngine Error: {e}")
            return []
