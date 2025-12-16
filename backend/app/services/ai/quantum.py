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
        You are a Senior Technical Lead acting as a strict requirements gatekeeper.

        Your job is to convert a User Issue into a rigid, atomic, and verifiable checklist
        that determines whether a Pull Request should be merged.

        INPUT:
        Issue Title: "{title}"
        Issue Description: "{body}"

        NON-NEGOTIABLE RULES:
        1. Atomic: Each checklist item tests exactly ONE condition.
        2. Verifiable: Each item must be provable by inspecting a code diff.
        3. Traceable: Derive requirements ONLY from the Issue text.
        4. Anti-Vagueness: Reject vague language unless tied to a measurable or structural condition.

        CHECKLIST SELF-AUDIT (MANDATORY):
        Before finalizing the checklist:
        - Identify any implied requirements that are missing.
        - Identify any items that are ambiguous or not directly testable.
        - If ambiguity exists, explicitly add a checklist item noting the ambiguity.

        FAIL-SAFE:
        - If the Issue description lacks actionable technical detail, output:
          "Issue description is insufficient for technical validation."

        OUTPUT FORMAT (STRICT JSON):
        {{
          "checklist": [
            {{
              "text": "Verify that [Component] [Action] when [Condition].",
              "required": true
            }}
          ],
          "audit_notes": [
            "Requirement for error handling is implied but not explicitly stated."
          ],
          "complexity": <1-10>,
          "priority": "Critical|High|Medium|Low"
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
            # We only extract the checklist for now to maintain interface compatibility
            data = json.loads(res.choices[0].message.content)
            return data.get("checklist", [])
        except Exception as e:
            print(f"QuantumEngine Error: {e}")
            return []
