from typing import List, Dict
import json
from groq import AsyncGroq

class QodoEngine:
    """
    Generation & Automation Layer:
    - Generates Unit Tests
    - Suggests Fixes
    - Writes Boilerplate
    """
    def __init__(self, client: AsyncGroq):
        self.client = client

    async def generate_tests(self, diff: str) -> List[Dict]:
        import uuid
        prompt = f"""
        You are Qodo AI. Generate pytest test cases for the following code changes.
        
        Diff:
        {diff[:10000]}
        
        Output Schema:
        {{
            "tests": [
                {{
                    "name": "Name of the test (e.g. test_login_success)",
                    "code": "Full python code for this SINGLE test function, including imports if needed locally.",
                    "reasoning": "Explanation of what this test verifies."
                }}
            ]
        }}
        
        Requirements:
        1. Output MUST be valid JSON.
        2. The root object MUST have a "tests" key.
        3. "tests" MUST be a list of objects.
        4. "code" MUST contain the full executable python code for that test. Escape newlines (\\n).
        5. Generate exactly 3 tests.
        """
        
        try:
            res = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a JSON generator. You always return structured JSON data following the user's schema."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1, # Lower temperature for structure
                max_tokens=4096,
                response_format={"type": "json_object"},
                timeout=20.0
            )
            raw_tests = json.loads(res.choices[0].message.content).get("tests", [])
            
            # Map to Schema
            formatted_tests = []
            for t in raw_tests:
                formatted_tests.append({
                    "test_id": str(uuid.uuid4()),
                    "name": t.get("name", "unknown_test"),
                    "framework": t.get("framework", "pytest"),
                    "target": t.get("target", "unknown"),
                    "checklist_ids": [],
                    "snippet": t.get("code", ""),
                    "reasoning": t.get("reasoning", "")
                })
            return formatted_tests
        except Exception as e:
             print(f"QodoEngine Error: {e}")
             return []

    async def generate_fix(self, issue_description: str, code_snippet: str) -> str:
        prompt = f"""
        You are Qodo AI, an expert code repair agent.
        
        Issue To Fix:
        {issue_description}
        
        Broken Code:
        {code_snippet}
        
        Task:
        Rewrite the "Broken Code" to resolve the "Issue".
        Return ONLY the fixed code block. Do not include markdown (```) or explanations.
        """
        
        try:
            res = await self.client.chat.completions.create(
                messages=[ 
                   {"role": "system", "content": "You are a Code Fixer. Output raw code only."},
                   {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            print(f"QodoEngine Fix Error: {e}")
            return "# Fix generation failed"
