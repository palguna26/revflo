"""
V1 Regression Tests for ScoreEngine (calculate_score)

Tests verify that scoring algorithm is deterministic and follows V1 contract.
These tests serve as a CONTRACT for V1 behavior.
"""
import pytest
from app.services.audit.scanner import calculate_score
from app.models.scan import RiskItem


class TestScoreEngineV1:
    """V1 Regression Tests - Scoring algorithm deterministic behavior"""
    
    def test_score_perfect_no_findings(self):
        """No findings → score = 100"""
        score = calculate_score([])
        assert score == 100
    
    def test_score_deduction_critical(self):
        """1 critical finding → score = 85 (100 - 15)"""
        findings = [
            RiskItem(
                title="Critical Issue",
                why_it_matters="Test",
                affected_areas=["test.py"],
                likelihood="high",
                recommended_action="Fix",
                severity="critical"
            )
        ]
        score = calculate_score(findings)
        assert score == 85
    
    def test_score_deduction_high(self):
        """1 high finding → score = 90 (100 - 10)"""
        findings = [
            RiskItem(
                title="High Issue",
                why_it_matters="Test",
                affected_areas=["test.py"],
                likelihood="medium",
                recommended_action="Fix",
                severity="high"
            )
        ]
        score = calculate_score(findings)
        assert score == 90
    
    def test_score_deduction_medium(self):
        """1 medium finding → score = 95 (100 - 5)"""
        findings = [
            RiskItem(
                title="Medium Issue",
                why_it_matters="Test",
                affected_areas=["test.py"],
                likelihood="medium",
                recommended_action="Fix",
                severity="medium"
            )
        ]
        score = calculate_score(findings)
        assert score == 95
    
    def test_score_deduction_low(self):
        """1 low finding → score = 98 (100 - 2)"""
        findings = [
            RiskItem(
                title="Low Issue",
                why_it_matters="Test",
                affected_areas=["test.py"],
                likelihood="low",
                recommended_action="Fix",
                severity="low"
            )
        ]
        score = calculate_score(findings)
        assert score == 98
    
    def test_score_deduction_mixed(self):
        """1 critical + 2 high + 1 medium → score = 60 (100 - 15 - 10 - 10 - 5)"""
        findings = [
            RiskItem(title="C1", why_it_matters="T", affected_areas=["t"], likelihood="h", recommended_action="F", severity="critical"),
            RiskItem(title="H1", why_it_matters="T", affected_areas=["t"], likelihood="m", recommended_action="F", severity="high"),
            RiskItem(title="H2", why_it_matters="T", affected_areas=["t"], likelihood="m", recommended_action="F", severity="high"),
            RiskItem(title="M1", why_it_matters="T", affected_areas=["t"], likelihood="l", recommended_action="F", severity="medium"),
        ]
        score = calculate_score(findings)
        assert score == 60
    
    def test_score_floor_at_zero(self):
        """10 critical findings → score = 0 (not negative)"""
        findings = [
            RiskItem(title=f"C{i}", why_it_matters="T", affected_areas=["t"], likelihood="h", recommended_action="F", severity="critical")
            for i in range(10)
        ]
        score = calculate_score(findings)
        assert score == 0  # Should be 100 - (10 * 15) = -50, but clamped to 0
    
    def test_score_exactly_zero(self):
        """7 critical findings → score = -5, clamped to 0"""
        findings = [
            RiskItem(title=f"C{i}", why_it_matters="T", affected_areas=["t"], likelihood="h", recommended_action="F", severity="critical")
            for i in range(7)
        ]
        score = calculate_score(findings)
        # 100 - (7 * 15) = 100 - 105 = -5 → clamped to 0
        assert score == 0
    
    def test_determinism_same_findings_same_score(self):
        """V1 DETERMINISM: Same findings run 10x → identical score"""
        findings = [
            RiskItem(title="C", why_it_matters="T", affected_areas=["t"], likelihood="h", recommended_action="F", severity="critical"),
            RiskItem(title="H", why_it_matters="T", affected_areas=["t"], likelihood="m", recommended_action="F", severity="high"),
        ]
        
        # Run 10 times
        scores = [calculate_score(findings) for _ in range(10)]
        
        # All scores should be identical
        assert all(s == scores[0] for s in scores)
        assert scores[0] == 75  # 100 - 15 - 10
    
    def test_score_order_independence(self):
        """Score should be same regardless of finding order"""
        findings_order1 = [
            RiskItem(title="C", why_it_matters="T", affected_areas=["t"], likelihood="h", recommended_action="F", severity="critical"),
            RiskItem(title="H", why_it_matters="T", affected_areas=["t"], likelihood="m", recommended_action="F", severity="high"),
            RiskItem(title="M", why_it_matters="T", affected_areas=["t"], likelihood="l", recommended_action="F", severity="medium"),
        ]
        
        findings_order2 = [
            RiskItem(title="M", why_it_matters="T", affected_areas=["t"], likelihood="l", recommended_action="F", severity="medium"),
            RiskItem(title="C", why_it_matters="T", affected_areas=["t"], likelihood="h", recommended_action="F", severity="critical"),
            RiskItem(title="H", why_it_matters="T", affected_areas=["t"], likelihood="m", recommended_action="F", severity="high"),
        ]
        
        score1 = calculate_score(findings_order1)
        score2 = calculate_score(findings_order2)
        
        assert score1 == score2 == 70  # 100 - 15 - 10 - 5
