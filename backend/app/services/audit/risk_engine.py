from typing import List, Dict, Any
from app.models.scan import RiskItem

class RiskEngine:
    def analyze(self, file_metrics: List[Dict[str, Any]], churn_metrics: Dict[str, int]) -> List[RiskItem]:
        """
        Analyze metrics and return deterministic findings based on hard thresholds.
        metrics format: [{'path': str, 'lox': int, 'complexity': int, 'indent_depth': int}]
        """
        findings = []
        
        for file in file_metrics:
            path = file['path']
            complexity = file.get('complexity', 0)
            loc = file.get('loc', 0) 
            indent = file.get('indent_depth', 0)
            churn = churn_metrics.get(path, 0)
            
            # Rule 1: Hotspot (High Complexity + High Churn)
            # Threshold: Complexity > 25 AND Churn > 10
            if complexity > 25 and churn > 10:
                findings.append(RiskItem(
                    title=f"Hotspot: {path}",
                    why_it_matters=f"High complexity ({complexity}) combined with frequent changes ({churn} commits) indicates a major stability risk.",
                    affected_areas=[path],
                    likelihood="high",
                    recommended_action="Refactor to reduce complexity immediately.",
                    severity="critical"
                ))
            
            # Rule 2: Deep Nesting (Cognitive Load)
            # Threshold: Indentation > 6
            elif indent > 6:
                findings.append(RiskItem(
                    title=f"Deeply Nested Logic: {path}",
                    why_it_matters=f"Indentation depth of {indent} makes code hard to read and test.",
                    affected_areas=[path],
                    likelihood="medium",
                    recommended_action="Flatten logic using early returns or extract methods.",
                    severity="high" 
                ))

            # Rule 3: Large File (Monolith)
            # Threshold: LOC > 300
            elif loc > 300:
                findings.append(RiskItem(
                    title=f"Large File: {path}",
                    why_it_matters=f"File size of {loc} lines exceeds 300, suggesting too many responsibilities.",
                    affected_areas=[path],
                    likelihood="low",
                    recommended_action="Split into smaller, focused modules.",
                    severity="medium"
                ))
                
            # Fallback Rule: High Complexity without Churn info
            elif complexity > 35:
                 findings.append(RiskItem(
                    title=f"Complex Module: {path}",
                    why_it_matters=f"Cyclomatic complexity of {complexity} is very high.",
                    affected_areas=[path],
                    likelihood="medium",
                    recommended_action="Simplification required.",
                    severity="high"
                ))
            
            # V2 Rule: Missing Tests (Only for substantial files)
            # Threshold: LOC > 100 AND no test coverage
            if loc > 100 and not file.get('has_test', False):
                findings.append(RiskItem(
                    title=f"No Tests: {path}",
                    why_it_matters=f"File has {loc} lines but no test coverage detected.",
                    affected_areas=[path],
                    likelihood="medium",
                    recommended_action="Add unit tests to improve code reliability.",
                    severity="medium"
                ))

        return findings

risk_engine = RiskEngine()
