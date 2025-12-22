"""
Test fixtures for V1 regression tests.
Synthetic data to ensure deterministic testing without API calls.
"""

# Sample file metrics for testing RiskEngine
SAMPLE_METRICS_CLEAN = [
    {"path": "utils.py", "complexity": 10, "loc": 50, "indent_depth": 2, "size": 1200},
    {"path": "helpers.py", "complexity": 8, "loc": 80, "indent_depth": 3, "size": 2000}
]

SAMPLE_METRICS_WITH_HOTSPOT = [
    {"path": "auth.py", "complexity": 45, "loc": 200, "indent_depth": 4, "size": 5000},
    {"path": "utils.py", "complexity": 10, "loc": 50, "indent_depth": 2, "size": 1200}
]

SAMPLE_METRICS_DEEP_NESTING = [
    {"path": "nested.py", "complexity": 20, "loc": 150, "indent_depth": 8, "size": 3000}
]

SAMPLE_METRICS_LARGE_FILE = [
    {"path": "models.py", "complexity": 15, "loc": 350, "indent_depth": 3, "size": 8000}
]

SAMPLE_METRICS_COMPLEX = [
    {"path": "engine.py", "complexity": 40, "loc": 250, "indent_depth": 5, "size": 6000}
]

# Sample churn data
CHURN_LOW = {
    "auth.py": 2,
    "utils.py": 1,
    "models.py": 3
}

CHURN_HIGH = {
    "auth.py": 15,
    "utils.py": 2,
    "models.py": 8
}

CHURN_EMPTY = {}

# Expected findings
EXPECTED_HOTSPOT_FINDING = {
    "title": "Hotspot: auth.py",
    "severity": "critical",
    "why_it_matters_contains": "complexity",
    "recommended_action_contains": "Refactor"
}

EXPECTED_DEEP_NESTING_FINDING = {
    "title": "Deeply Nested Logic: nested.py",
    "severity": "high",
    "why_it_matters_contains": "Indentation",
    "recommended_action_contains": "Flatten"
}

EXPECTED_LARGE_FILE_FINDING = {
    "title": "Large File: models.py",
    "severity": "medium",
    "why_it_matters_contains": "lines exceeds",
    "recommended_action_contains": "Split"
}

EXPECTED_COMPLEX_FINDING = {
    "title": "Complex Module: engine.py",
    "severity": "high",
    "why_it_matters_contains": "complexity",
    "recommended_action_contains": "Simplification"
}
