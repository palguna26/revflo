"""
V1 Regression Tests for RiskEngine

Tests verify that RiskEngine produces deterministic findings from metrics.
These tests serve as a CONTRACT for V1 behavior - any changes that break
these tests require explicit user approval and engine_version bump.
"""
import pytest
from app.services.audit.risk_engine import risk_engine
from tests.fixtures.sample_data import (
    SAMPLE_METRICS_CLEAN,
    SAMPLE_METRICS_WITH_HOTSPOT,
    SAMPLE_METRICS_DEEP_NESTING,
    SAMPLE_METRICS_LARGE_FILE,
    SAMPLE_METRICS_COMPLEX,
    CHURN_LOW,
    CHURN_HIGH,
    CHURN_EMPTY
)


class TestRiskEngineV1:
    """V1 Regression Tests - RiskEngine deterministic behavior"""
    
    def test_hotspot_detection(self):
        """Hotspot rule: complexity > 25 AND churn > 10 → critical"""
        findings = risk_engine.analyze(SAMPLE_METRICS_WITH_HOTSPOT, CHURN_HIGH)
        
        # Should detect hotspot in auth.py (complexity=45, churn=15)
        hotspots = [f for f in findings if "Hotspot" in f.title]
        assert len(hotspots) == 1
        assert hotspots[0].title == "Hotspot: auth.py"
        assert hotspots[0].severity == "critical"
        assert "complexity" in hotspots[0].why_it_matters.lower()
        assert "auth.py" in hotspots[0].affected_areas
    
    def test_deep_nesting_detection(self):
        """Deep Nesting rule: indent_depth > 6 → high"""
        findings = risk_engine.analyze(SAMPLE_METRICS_DEEP_NESTING, CHURN_EMPTY)
        
        # Should detect deep nesting (indent=8)
        deep_nesting = [f for f in findings if "Deeply Nested" in f.title or "Deep" in f.title]
        assert len(deep_nesting) == 1
        assert deep_nesting[0].severity == "high"
        assert "nested.py" in deep_nesting[0].affected_areas
    
    def test_large_file_detection(self):
        """Large File rule: LOC > 300 → medium"""
        findings = risk_engine.analyze(SAMPLE_METRICS_LARGE_FILE, CHURN_EMPTY)
        
        # Should detect large file (LOC=350)
        large_files = [f for f in findings if "Large File" in f.title]
        assert len(large_files) == 1
        assert large_files[0].severity == "medium"
        assert "models.py" in large_files[0].affected_areas
    
    def test_complex_module_detection(self):
        """Complex Module rule: complexity > 35 (without churn) → high"""
        findings = risk_engine.analyze(SAMPLE_METRICS_COMPLEX, CHURN_EMPTY)
        
        # Should detect complex module (complexity=40)
        complex_modules = [f for f in findings if "Complex Module" in f.title]
        assert len(complex_modules) == 1
        assert complex_modules[0].severity == "high"
        assert "engine.py" in complex_modules[0].affected_areas
    
    def test_no_findings_for_clean_metrics(self):
        """Clean metrics below all thresholds → no findings"""
        findings = risk_engine.analyze(SAMPLE_METRICS_CLEAN, CHURN_LOW)
        
        # Should have no findings
        assert len(findings) == 0
    
    def test_determinism_same_metrics_same_findings(self):
        """V1 DETERMINISM: Same metrics run 10x → identical findings"""
        # Run analysis 10 times
        results = []
        for _ in range(10):
            findings = risk_engine.analyze(SAMPLE_METRICS_WITH_HOTSPOT, CHURN_HIGH)
            results.append(findings)
        
        # All results should be identical
        for result in results[1:]:
            assert len(result) == len(results[0])
            for i, finding in enumerate(result):
                assert finding.title == results[0][i].title
                assert finding.severity == results[0][i].severity
                assert finding.affected_areas == results[0][i].affected_areas
    
    def test_rule_priority_hotspot_over_complex(self):
        """Hotspot (critical) should trigger before Complex Module (high)"""
        # auth.py has complexity=45 AND churn=15 → should be Hotspot, not Complex
        findings = risk_engine.analyze(SAMPLE_METRICS_WITH_HOTSPOT, CHURN_HIGH)
        
        auth_findings = [f for f in findings if "auth.py" in f.affected_areas]
        # Should only have Hotspot (high priority), not Complex Module
        assert len(auth_findings) == 1
        assert "Hotspot" in auth_findings[0].title
        assert auth_findings[0].severity == "critical"
    
    def test_churn_threshold_exactly_10(self):
        """Edge case: churn=10 should NOT trigger Hotspot (threshold is > 10)"""
        churn_at_threshold = {"auth.py": 10}  # Exactly at threshold
        findings = risk_engine.analyze(SAMPLE_METRICS_WITH_HOTSPOT, churn_at_threshold)
        
        # Should NOT detect hotspot (churn must be > 10, not >= 10)
        hotspots = [f for f in findings if "Hotspot" in f.title]
        assert len(hotspots) == 0
        
        # But should still detect as Complex Module (complexity > 35)
        complex_findings = [f for f in findings if "Complex" in f.title]
        assert len(complex_findings) == 1
