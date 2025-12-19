export interface User {
  id: string;
  login: string;
  avatar_url: string;
  name?: string;
  email?: string;
  managed_repos: string[];
}

export interface RepoSummary {
  repo_full_name: string;
  owner: string;
  name: string;
  health_score: number;
  is_installed: boolean;
  pr_count: number;
  issue_count: number;
  last_activity?: string;
}

export interface PRSummary {
  pr_number: number;
  title: string;
  author: string;
  created_at: string;
  health_score: number;
  validation_status: 'pending' | 'validated' | 'needs_work';
  merge_decision?: boolean;
  block_reason?: 'BLOCK_CHECKLIST_FAILED' | 'BLOCK_INDETERMINATE_EVIDENCE' | 'BLOCK_SECURITY_CRITICAL' | 'BLOCK_INSUFFICIENT_ISSUE_SPEC' | null;
  github_url: string;
}

export interface ValidationResult {
  pr_number: number;
  status: 'passed' | 'failed' | 'pending' | 'skipped';
  evidence?: string;
  reasoning?: string;
  timestamp: string;
}

export interface ChecklistItem {
  id: string;
  text: string;
  required: boolean;
  status: 'pending' | 'passed' | 'failed' | 'skipped' | 'indeterminate';
  linked_tests: string[];
  latest_validation?: ValidationResult;
  validations?: ValidationResult[];
}

export interface Issue {
  issue_number: number;
  title: string;
  status: 'open' | 'processing' | 'completed';
  created_at: string;
  updated_at: string;
  checklist_summary: {
    total: number;
    passed: number;
    failed: number;
    pending: number;
  };
  checklist?: ChecklistItem[];
  github_url: string;
}

export interface TestResult {
  test_id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration_ms?: number;
  error_message?: string;
  checklist_ids: string[];
}

export interface CodeHealthIssue {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  message: string;
  file_path: string;
  line_number?: number;
  suggestion?: string;
  snippet?: string;
}

export interface SuggestedTest {
  test_id: string;
  name: string;
  framework: string;
  target: string;
  checklist_ids: string[];
  snippet: string;
  reasoning?: string;
}

export interface CoverageAdvice {
  file_path: string;
  lines: number[];
  suggestion: string;
}

export interface PRDetail {
  pr_number: number;
  title: string;
  author: string;
  created_at: string;
  health_score: number;
  validation_status: 'pending' | 'validated' | 'needs_work';
  merge_decision?: boolean;
  block_reason?: 'BLOCK_CHECKLIST_FAILED' | 'BLOCK_INDETERMINATE_EVIDENCE' | 'BLOCK_SECURITY_CRITICAL' | 'BLOCK_INSUFFICIENT_ISSUE_SPEC' | null;
  manifest?: {
    checklist_items: ChecklistItem[];
  };
  test_results: TestResult[];
  code_health: CodeHealthIssue[];
  coverage_advice: CoverageAdvice[];
  suggested_tests: SuggestedTest[];
  github_url: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  repo_full_name?: string;
  created_at: string;
  read: boolean;
}

export interface RiskItem {
  title: string;
  why_it_matters: string;
  affected_areas: string[];
  likelihood: "low" | "medium" | "high";
  recommended_action: string;
  severity: "critical" | "high" | "medium" | "low";
}

export interface FragilityMap {
  high_risk_modules: string[];
  change_sensitive_areas: string[];
}

export interface SecurityReliabilityItem {
  finding: string;
  severity: "critical" | "high" | "medium" | "low";
  context: string;
}

export interface Roadmap {
  fix_now: string[];
  fix_next: string[];
  defer: string[];
}

export interface AuditSummary {
  maintainability: "low" | "medium" | "high";
  security: "low" | "medium" | "high";
  performance: "low" | "medium" | "high";
  testing_confidence: "low" | "medium" | "high";
  overview: string;
}

export interface AuditReport {
  summary: AuditSummary;
  top_risks: RiskItem[];
  fragility_map: FragilityMap;
  security_reliability: SecurityReliabilityItem[];
  roadmap: Roadmap;
  executive_takeaway: string;
}

export interface ScanResult {
  id: string;
  repo_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
  report?: AuditReport;
  raw_metrics?: any;
  error_message?: string;
}
