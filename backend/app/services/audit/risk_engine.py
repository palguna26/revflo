from typing import List, Dict, Any
from app.models.scan import RiskItem

class RiskEngine:
    def analyze(self, file_metrics: List[Dict[str, Any]], churn_metrics: Dict[str, int]) -> List[RiskItem]:
        """
        Analyze metrics and return top risk items.
        metrics format: [{'path': str, 'size': int, 'complexity': int}]
        churn_metrics: {'path': commit_count}
        """
        scored_files = []
        
        # 1. Normalize and Score
        max_complexity = max((m.get('complexity', 0) for m in file_metrics), default=1)
        max_churn = max(churn_metrics.values(), default=1)
        
        for file in file_metrics:
            path = file['path']
            complexity = file.get('complexity', 0)
            churn = churn_metrics.get(path, 0)
            
            # Normalize 0-1
            norm_complexity = complexity / max_complexity if max_complexity > 0 else 0
            norm_churn = churn / max_churn if max_churn > 0 else 0
            
            # Heuristic Formula: 50% Complexity + 50% Churn
            # (Coupling omitted for MVP efficiency)
            risk_score = (norm_complexity * 0.5) + (norm_churn * 0.5)
            
            scored_files.append({
                "path": path,
                "score": risk_score,
                "raw_complexity": complexity,
                "raw_churn": churn
            })
            
        # 2. Sort by Risk Score
        scored_files.sort(key=lambda x: x['score'], reverse=True)
        
        # 3. Generate Risk Items for Top 10
        top_risks = []
        for item in scored_files[:10]:
            if item['score'] < 0.1: continue # Ignore low risk
            
            reason = []
            if item['raw_complexity'] > 10: reason.append("High Complexity")
            if item['raw_churn'] > 5: reason.append("Frequent Changes")
            
            risk_item = RiskItem(
                title=f"High Risk Module: {item['path']}",
                why_it_matters=f"This file has high engineering friction ({', '.join(reason)}). It is error-prone and hard to maintain.",
                affected_areas=[item['path']],
                likelihood="high" if item['score'] > 0.7 else "medium",
                recommended_action="Refactor to reduce complexity or break into smaller modules.",
                severity="high" if item['score'] > 0.8 else "medium"
            )
            top_risks.append(risk_item)
            
        return top_risks

risk_engine = RiskEngine()
