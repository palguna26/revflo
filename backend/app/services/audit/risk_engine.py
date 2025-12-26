from typing import List, Dict, Any, Optional
from app.models.scan import RiskItem
from app.services.audit.config_parser import RevFloConfig
import uuid

class RiskEngine:
    """
    Deterministic risk analysis engine with configurable rules.
    V2: Now supports custom thresholds and severity via RevFloConfig.
    """
    
    def __init__(self, config: RevFloConfig = None):
        """Initialize with custom or default configuration."""
        self.config = config or RevFloConfig()
    
    def analyze(self, file_metrics: List[Dict[str, Any]], churn_metrics: Dict[str, int]) -> List[RiskItem]:
        """
        Analyze metrics using configured rules and thresholds.
        Returns deterministic findings based on hard rules.
        """
        findings = []
        
        # Filter out test files - we don't want to audit tests themselves
        production_files = []
        for file in file_metrics:
            path_lower = file['path'].lower()
            # Skip test files, test directories, and spec files
            if any(pattern in path_lower for pattern in ['test', 'spec', '__test__', '__tests__']):
                continue
            production_files.append(file)
        
        for file in production_files:
            path = file['path']
            complexity = file.get('complexity', 0)
            loc = file.get('loc', 0)
            indent = file.get('indent_depth', 0)
            churn = churn_metrics.get(path, 0)
            
            # Rule 1: Hotspot (High Complexity + High Churn)
            if self.config.is_rule_enabled("hotspot"):
                complexity_threshold = self.config.get_threshold("hotspot", "complexity")
                churn_threshold = self.config.get_threshold("hotspot", "churn")
                
                if complexity > complexity_threshold and churn > churn_threshold:
                    findings.append(RiskItem(
                        id=str(uuid.uuid4()),
                        rule_type="Hotspot",
                        severity=self.config.get_severity("hotspot"),
                        file_path=path,
                        description=f"High complexity ({complexity}) combined with frequent changes ({churn} commits)",
                        explanation=(
                            f"This file has both high complexity AND high churn, making it a major stability risk. "
                            f"Thresholds: complexity > {complexity_threshold}, churn > {churn_threshold}"
                        ),
                        metrics={"complexity": complexity, "churn": churn}
                    ))
            
            # Rule 2: Deep Nesting (Cognitive Load)
            if self.config.is_rule_enabled("deep_nesting"):
                indent_threshold = self.config.get_threshold("deep_nesting", "indent_depth")
                
                if indent > indent_threshold:
                    findings.append(RiskItem(
                        id=str(uuid.uuid4()),
                        rule_type="Deep Nesting",
                        severity=self.config.get_severity("deep_nesting"),
                        file_path=path,
                        description=f"Indentation depth of {indent} makes code hard to read and test",
                        explanation=(
                            f"Deep nesting reduces code readability and increases cognitive load. "
                            f"Threshold: indent_depth > {indent_threshold}"
                        ),
                        metrics={"indent_depth": indent}
                    ))
            
            # Rule 3: Large File (Monolith)
            if self.config.is_rule_enabled("large_file"):
                loc_threshold = self.config.get_threshold("large_file", "loc")
                
                if loc > loc_threshold:
                    findings.append(RiskItem(
                        id=str(uuid.uuid4()),
                        rule_type="Large File",
                        severity=self.config.get_severity("large_file"),
                        file_path=path,
                        description=f"File size of {loc} lines suggests too many responsibilities",
                        explanation=(
                            f"Large files often indicate violation of Single Responsibility Principle. "
                            f"Threshold: loc > {loc_threshold}"
                        ),
                        metrics={"loc": loc}
                    ))
            
            # Rule 4: Complex Module (High Complexity without Churn)
            if self.config.is_rule_enabled("complex_module"):
                complexity_threshold = self.config.get_threshold("complex_module", "complexity")
                
                if complexity > complexity_threshold:
                    findings.append(RiskItem(
                        id=str(uuid.uuid4()),
                        rule_type="Complex Module",
                        severity=self.config.get_severity("complex_module"),
                        file_path=path,
                        description=f"Cyclomatic complexity of {complexity} is very high",
                        explanation=(
                            f"High complexity makes code harder to understand, test, and maintain. "
                            f"Threshold: complexity > {complexity_threshold}"
                        ),
                        metrics={"complexity": complexity}
                    ))
            
            # Rule 5: No Tests (V2 Feature)
            if self.config.is_rule_enabled("no_tests"):
                min_loc = self.config.get_threshold("no_tests", "min_loc")
                
                if loc > min_loc and not file.get('has_test', False):
                    findings.append(RiskItem(
                        id=str(uuid.uuid4()),
                        rule_type="No Tests",
                        severity=self.config.get_severity("no_tests"),
                        file_path=path,
                        description=f"File has {loc} lines but no test coverage detected",
                        explanation=(
                            f"Substantial files without tests are risky and harder to refactor safely. "
                            f"Threshold: loc > {min_loc} without tests"
                        ),
                        metrics={"loc": loc, "has_test": False}
                    ))
        
        return findings

# Default instance uses default config (V1 behavior)
risk_engine = RiskEngine()

def create_risk_engine(config: RevFloConfig) -> RiskEngine:
    """Factory function for creating RiskEngine with custom config."""
    return RiskEngine(config)
