📘 Product Requirements Document (PRD)
Product: RevFlo
Subtitle: Metric-Driven Code Intelligence Engineers Trust
1. Overview
1.1 Product Vision

RevFlo is a deterministic, metric-driven code intelligence platform that helps engineering teams understand, trust, and improve their codebases.

Unlike AI-heavy tools that invent insights, RevFlo is built on a simple philosophy:

Metrics decide. AI explains. Engineers own the outcome.

RevFlo aims to become the default “code health layer” across repositories, pull requests, and organizations.

1.2 Problem Statement

Modern teams struggle with:

Noisy code quality tools

AI reviews that feel speculative or unfair

Dashboards disconnected from real developer workflows

Low trust in automated findings

Existing tools (e.g., CodeAnt, SonarQube) either:

Overwhelm developers with alerts, or

Hide logic behind opaque scoring systems

This leads to:

Alert fatigue

Ignored findings

Low adoption among senior engineers

1.3 Solution Summary

RevFlo provides:

Metric-driven, reproducible findings

PR-first developer experience

AI used only for explanation, never decision-making

Clear ownership of rules, thresholds, and outcomes

2. Goals & Non-Goals
2.1 Goals

Produce 100% reproducible audit results

Ensure every finding is traceable to metrics

Maximize developer trust and adoption

Reduce alert noise while increasing signal quality

Integrate seamlessly into existing Git workflows

2.2 Non-Goals

No raw AI code analysis

No speculative security findings

No auto-refactoring or code mutation

No “black box” scores without explanation

3. Target Users
3.1 Primary Users

Backend / Full-stack Engineers

Senior Engineers / Tech Leads

3.2 Secondary Users

Engineering Managers

Staff / Principal Engineers

Platform & DevEx teams

4. Core Product Principles (Non-Negotiable)

Determinism over intelligence

Explainability over insight density

PRs over dashboards

Fewer findings > more findings

Trust beats novelty

5. System Architecture (High Level)
Repository
 └─ Scanner (metrics only)
     └─ RiskEngine (rule evaluation)
         └─ Findings (deterministic)
             └─ ScoreEngine (repo health)
                 └─ AuditAI (explanation only)
                     └─ UI / PR Comments

6. Feature Set
6.1 Repository Scanner
Description

Scans repositories to collect objective metrics only.

Metrics Collected

Cyclomatic complexity

Lines of Code (LOC)

Churn (time-windowed)

Indentation / nesting depth

File ownership (contributors)

Test presence

Acceptance Criteria

No AI involved

Metrics reproducible across runs

Cached per commit SHA

6.2 Risk Engine (Deterministic Core)
Description

Transforms metrics into explicit findings using hard rules.

Example Rules
Rule	Condition
Hotspot	complexity > 25 AND churn > 10
Large File	LOC > 300
Deep Nesting	indentation depth > 6
Finding Object
{
  "file": "auth.py",
  "type": "Hotspot",
  "severity": "High",
  "metrics": { "complexity": 45, "churn": 12 },
  "thresholds": { "complexity": 25, "churn": 10 },
  "roadmap_action": "Refactor to reduce complexity"
}

Acceptance Criteria

No inference

No AI

Same metrics → same findings

6.3 Score Engine
Description

Computes a repo health score deterministically.

Scoring Model

Start at 100

Deduct per finding:

Severity	Deduction
Critical	−15
High	−10
Medium	−5
Low	−2
Acceptance Criteria

Score independent of AI

Stable across runs

Diff-able over time

6.4 AuditAI (Explanation Layer)
Description

LLM-based explanation engine that never generates findings.

Inputs

List of Findings

File snippets (optional, read-only)

Responsibilities

Explain why findings matter

Group findings into themes

Write executive summary

Forbidden Actions

Creating findings

Assigning severity

Proposing roadmap items

Acceptance Criteria

Removing AuditAI does not change score or roadmap

Output strictly explanatory

6.5 Roadmap Generator
Description

Maps findings → actions 1:1.

Example Mapping
Finding Type	Action
Hotspot	Reduce complexity
No Tests	Add tests
Deep Nesting	Simplify control flow
Acceptance Criteria

No roadmap without finding

No AI logic involved

6.6 Pull Request Integration (Primary UX)
Description

RevFlo comments directly on PRs with:

New findings

Score deltas

Actionable context

Example PR Comment
🔴 Hotspot detected in auth.py

• Complexity: 45 (threshold: 25)
• Churn (90d): 12 commits

Why this matters:
High-complexity code that changes frequently has a higher regression risk.

Suggested action:
Refactor to reduce complexity.

Acceptance Criteria

Minimal noise

One comment per file max

Deterministic content

6.7 Dashboard (Secondary UX)
Audience

Leads

Managers

Auditors

Views

Repo health over time

Top recurring findings

Team-level trends

Acceptance Criteria

Mirrors PR data

No additional logic

7. Customization & Extensibility
Rule Configuration (Future)
rules:
  hotspot:
    complexity: 30
    churn: 15
  large_file:
    loc: 400


Teams can:

Adjust thresholds

Disable rules

Version rule sets

8. Trust & Safety Guarantees

RevFlo must guarantee:

No hallucinated findings

No hidden heuristics

No AI-only decisions

Full audit traceability

9. Success Metrics
Adoption

% of PRs with RevFlo enabled

PR comment engagement rate

Trust

Findings dismissed / ignored rate

Rule overrides usage

Impact

Reduction in hotspots over time

Improved repo health scores

10. Competitive Positioning
CodeAnt

AI-heavy

Noisy

Less deterministic

RevFlo

Metric-first

Explainable

Developer-owned

Predictable

11. One-Line Product Definition

RevFlo is a deterministic code intelligence system that engineers trust because every finding is backed by math, not opinion.

12. Open Questions (for iteration)

Which metrics ship in v1?

Default thresholds by language?

How much customization in OSS vs paid?

Final Note

If CodeAnt is “AI reviewing your code”,
RevFlo is “your codebase explaining itself.”