# RevFlo Frontend Reconstruction Specification
## UI as Source of Truth

**Version:** 1.0  
**Date:** December 2024  
**Prepared for:** Antigravity Engineering Team  
**Purpose:** Complete specification for faithful frontend reconstruction

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Global App Architecture](#2-global-app-architecture)
3. [Design System](#3-design-system)
4. [Page-by-Page Breakdown](#4-page-by-page-breakdown)
5. [Component Documentation](#5-component-documentation)
6. [State & Status Semantics](#6-state--status-semantics)
7. [UX Behavior Rules](#7-ux-behavior-rules)
8. [Empty, Loading, and Error States](#8-empty-loading-and-error-states)
9. [Navigation Contracts](#9-navigation-contracts)
10. [API Contract Reference](#10-api-contract-reference)
11. [Acceptance Criteria Checklist](#11-acceptance-criteria-checklist)

---

## 1. Executive Summary

**RevFlo** is an enterprise code review platform that provides:
- AI-generated quality checklists for GitHub issues
- Automated PR validation against issue checklists
- Repository health scoring and code audit capabilities
- Test suggestions with code snippets

### Technology Stack (REQUIRED)
- **Framework:** React 18.3+ with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS with custom design tokens
- **UI Components:** shadcn/ui
- **Routing:** react-router-dom v6
- **State Management:** React useState/useEffect (no Redux)
- **Data Fetching:** Native fetch with custom API wrapper
- **Icons:** Lucide React

---

## 2. Global App Architecture

### 2.1 Application Shell

The app uses a **single-column layout** with a sticky header. There is **NO sidebar**.

```
┌─────────────────────────────────────────────────┐
│ HEADER (sticky, 56px height)                    │
├─────────────────────────────────────────────────┤
│                                                 │
│                 MAIN CONTENT                    │
│           (container, max-width)                │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2.2 Route Structure

| Route Pattern | Page Component | Purpose |
|--------------|----------------|---------|
| `/` | Landing | Marketing/unauthenticated homepage |
| `/auth/callback` | LoginCallback | OAuth callback handler |
| `/dashboard` | Dashboard | Multi-repo overview for authenticated users |
| `/repo/:owner/:repo` | RepoPage | Single repository detail view |
| `/repo/:owner/:repo/issues/:issueNumber` | IssueDetail | Issue with checklist |
| `/repo/:owner/:repo/prs/:prNumber` | PRDetail | Pull request validation view |
| `*` | NotFound | 404 catch-all |

### 2.3 Authentication Flow

1. User clicks "Sign in with GitHub" → navigates to `/auth/github` (external)
2. GitHub redirects to `/auth/callback`
3. LoginCallback page:
   - Shows loading spinner with "Authenticating..." text
   - Calls `api.getMe()` to verify authentication
   - On success: shows toast, redirects to `/dashboard`
   - On failure: shows error toast, redirects to `/`

---

## 3. Design System

### 3.1 Typography

| Font Family | Usage | CSS Variable |
|-------------|-------|--------------|
| Work Sans | Body text, UI elements | `--font-sans` |
| Lora | Serif accents (optional) | `--font-serif` |
| Inconsolata | Code, monospace elements | `--font-mono` |

### 3.2 Color Tokens (HSL Format)

#### Light Mode (`:root`)
| Token | HSL Value | Usage |
|-------|-----------|-------|
| `--background` | `0 0% 96%` | Page background |
| `--foreground` | `0 0% 9%` | Primary text |
| `--card` | `0 0% 98%` | Card backgrounds |
| `--primary` | `161 93% 30%` | Brand color (teal-green) |
| `--secondary` | `0 0% 32%` | Secondary UI elements |
| `--muted` | `0 0% 63%` | Muted text/backgrounds |
| `--destructive` | `0 72% 50%` | Error states, critical |
| `--success` | `142 71% 45%` | Success states, passed |
| `--warning` | `38 92% 50%` | Warning states, pending |
| `--border` | `0 0% 83%` | Border color |

#### Dark Mode (`.dark`)
| Token | HSL Value | Usage |
|-------|-----------|-------|
| `--background` | `0 0% 9%` | Page background |
| `--foreground` | `0 0% 98%` | Primary text |
| `--card` | `0 0% 14%` | Card backgrounds |
| `--primary` | `158 64% 51%` | Brand color |
| `--border` | `0 0% 32%` | Border color |

### 3.3 Spacing & Layout

- **Container:** Centered, max-width with `px-4` or `px-6` padding
- **Border Radius:** `0.75rem` (12px) base radius
- **Header Height:** 56px (`h-14`)

### 3.4 Component Classes

| Class Name | Composition |
|------------|-------------|
| `.glass-card` | `bg-card border border-border/50` |

---

## 4. Page-by-Page Breakdown

### 4.1 Landing Page (`/`)

**Purpose:** Marketing page for unauthenticated users

**Layout (top to bottom):**

1. **Header (Local)**
   - Height: 56px, sticky
   - Left: Logo (Workflow icon + "RevFlo" text)
   - Right: "Sign in" button (small, links to `/auth/github`)

2. **Hero Section**
   - Label: "Enterprise Code Review" (uppercase, primary color, small)
   - H1: "Streamline your code review workflow"
   - Subtext: Description paragraph
   - CTAs: 
     - "Get started" (primary button, arrow icon) → `/auth/github`
     - "View demo" (outline button) → `/dashboard`

3. **Features Grid**
   - 6 FeatureCard components in 3-column grid (responsive)
   - Each card: Icon + Title + Description

4. **CTA Section**
   - Centered card with "Ready to get started?" heading
   - "Sign in with GitHub" button

**FeatureCard Component:**
- Icon (primary color)
- Title (font-medium)
- Description (muted text, small)

**Features List (EXACT):**
1. Smart Checklists - CheckCircle2 icon
2. PR Validation - GitPullRequest icon
3. Health Metrics - TrendingUp icon
4. Security Analysis - Shield icon
5. Test Suggestions - Sparkles icon
6. GitHub Integration - Github icon

---

### 4.2 Login Callback Page (`/auth/callback`)

**Purpose:** OAuth redirect handler

**Layout:**
- Full-screen centered content
- Loader2 icon (spinning, primary color, 48px)
- H2: "Authenticating..."
- Subtext: "Please wait while we sign you in."

**Behavior:**
- Immediately calls `api.getMe()` on mount
- Success → toast + redirect to `/dashboard`
- Failure → error toast + redirect to `/`

---

### 4.3 Dashboard Page (`/dashboard`)

**Purpose:** Multi-repository overview for authenticated users

**Layout (top to bottom):**

1. **Header (Global)**
   - Shows user avatar and username
   - Shows RepoSwitcher dropdown
   - Shows ThemeToggle

2. **Welcome Section**
   - H1: "Welcome back, {user.name || user.login}!"
   - Subtext: "Manage your repositories and track code quality across your projects."

3. **Repositories Section**
   - Header row: H2 "Your Repositories" + "Manage Repositories" button
   - Repository grid: 3-column on desktop, 2 on tablet, 1 on mobile
   - Each card is a RepoCard (clickable, navigates to repo page)

4. **Recent Activity Section** (only if repos exist)
   - Two-column layout on desktop
   - Left: "Recent Pull Requests" with PRCard list
   - Right: "Pending Issues" with IssueCard list

**Empty State (no repos):**
- Glass card with centered text
- "No repositories found."
- "Install RevFlo" button → external GitHub app install link

---

### 4.4 Repository Page (`/repo/:owner/:repo`)

**Purpose:** Single repository detail view with tabs

**Layout (top to bottom):**

1. **Header (Global)** - with RepoSwitcher and user info

2. **Repository Header**
   - H1: `{owner}/{repo}` (monospace font)
   - Health Score display: TrendingUp icon + large number + "Health Score" label
   - Actions: "View on GitHub" (outline button, external link)
   - If not installed: "Install QuantumReview" button
   - Stats row: "{pr_count} Pull Requests • {issue_count} Issues • Last activity: {time}"

3. **Tabs Section**
   - Tab triggers: Issues | Pull Requests | Audit | Settings
   - Default tab: "issues"

**Tab Contents:**

#### Issues Tab
- List of IssueCard components
- Empty state: "No issues found"

#### Pull Requests Tab
- List of PRCard components (hardcoded mock data currently)

#### Audit Tab
- AuditPanel component (see Component Documentation)

#### Settings Tab
- Glass card with Settings icon
- H3: "Repository Settings"
- Placeholder text about future settings

---

### 4.5 Issue Detail Page (`/repo/:owner/:repo/issues/:issueNumber`)

**Purpose:** View issue with quality checklist

**Layout (top to bottom):**

1. **Header (Global)**

2. **Breadcrumb**
   - "← Back to {owner}/{repo}" link

3. **Issue Header**
   - Status badge + Issue number
   - H1: Issue title
   - Actions: "GitHub" button (external link)

4. **Progress Summary Card**
   - "Checklist Progress" label + percentage
   - Progress bar (filled portion = passed/total)
   - Legend: Passed (green) / Failed (red) / Pending (yellow)

5. **Quality Checklist Card**
   - Header: "Quality Checklist" + Actions
   - Actions: "Regenerate" button + "Comment" button
   - List of ChecklistItem components
   - Empty state: "No checklist items generated yet."

6. **Issue Details Card**
   - Created date
   - Last Updated date
   - Total Items count

**Regenerate Button Behavior:**
- Shows spinner while regenerating
- Calls `api.regenerateChecklist()`
- Shows toast: "Checklist Regeneration Started"
- Reloads issue data after 2 second delay

---

### 4.6 PR Detail Page (`/repo/:owner/:repo/prs/:prNumber`)

**Purpose:** View PR validation, tests, and code health

**Layout (top to bottom):**

1. **Header (Global)**

2. **Breadcrumb**
   - "← Back to {owner}/{repo}" link

3. **PR Header**
   - Validation status badge + PR number
   - H1: PR title
   - Author line: "by {author}"
   - Health Score display (right-aligned): large number with icon
   - Actions: "View on GitHub" + "Revalidate" + "Recommend Merge" (if validated)

4. **Two-Column Layout (desktop)**

**Left Column:**

5. **Checklist Coverage Card**
   - Lists checklist items from manifest
   - Each item shows: pass/warning icon + text + linked test count

6. **Code Health Issues Card**
   - List of code health issues
   - Each shows: severity icon + badges + message + file path + suggestion
   - Empty state: "No code health issues detected. Great work!"

**Right Column:**

7. **Suggested Tests Section**
   - H2: "Suggested Tests"
   - List of SuggestedTestCard components
   - Empty state: "No test suggestions available"

8. **Coverage Gaps Card** (if advice exists)
   - List of coverage advice items
   - Each shows: file path + line numbers + suggestion

**Revalidate Button Behavior:**
- Shows spinner while revalidating
- Calls `api.revalidatePR()`
- Shows toast: "PR Revalidation Started"
- Reloads PR data after 2 second delay

---

### 4.7 Not Found Page (`/*`)

**Purpose:** 404 error page

**Layout:**
- Full-screen centered
- H1: "404" (large, bold)
- Text: "Oops! Page not found"
- Link: "Return to Home" → `/`

---

## 5. Component Documentation

### 5.1 Header

**Technical Name:** `Header`  
**File:** `src/components/Header.tsx`

**Props:**
```typescript
interface HeaderProps {
  user?: { login: string; avatar_url: string };
  repos?: Array<{ repo_full_name: string; owner: string; name: string }>;
}
```

**Structure:**
- Sticky, 56px height, border-bottom
- Backdrop blur effect
- Left section: Logo link + RepoSwitcher (if authenticated)
- Right section: ThemeToggle + User info OR Sign in button

**States:**
- **Authenticated:** Shows avatar, username, repo switcher
- **Unauthenticated:** Shows "Sign in with GitHub" button

---

### 5.2 ThemeToggle

**Technical Name:** `ThemeToggle`  
**File:** `src/components/ThemeToggle.tsx`

**Behavior:**
- Ghost button, icon-only (9x9)
- Light mode: Shows Moon icon
- Dark mode: Shows Sun icon
- Persists preference to localStorage
- Respects system preference on first load

**State Management:**
- Reads from `localStorage.getItem('theme')`
- Writes to `localStorage.setItem('theme', 'dark'|'light')`
- Toggles `.dark` class on `document.documentElement`

---

### 5.3 RepoSwitcher

**Technical Name:** `RepoSwitcher`  
**File:** `src/components/RepoSwitcher.tsx`

**Props:**
```typescript
interface RepoSwitcherProps {
  repos: Array<{ repo_full_name: string; owner: string; name: string }>;
}
```

**Behavior:**
- Dropdown menu trigger button
- Shows FolderGit2 icon + current repo name (or "Select Repository")
- Dropdown shows up to 8 repos
- Active repo has checkmark
- If more than 8 repos: shows "View all repositories →" link to `/dashboard`

---

### 5.4 ManageReposDialog

**Technical Name:** `ManageReposDialog`  
**File:** `src/components/ManageReposDialog.tsx`

**Props:**
```typescript
interface ManageReposDialogProps {
  repos: RepoSummary[];
  onAddRepo?: (repoFullName: string) => void;
  onRemoveRepo?: (repoFullName: string) => void;
}
```

**Structure:**
- Dialog trigger: "Manage Repositories" outline button with Settings2 icon
- Dialog content:
  - Title: "Manage Repositories"
  - Description: "Add or remove repositories from RevFlo..."
  - Tab buttons: "Connected ({count})" | "+ Add Repository"
  - Search input with Search icon
  - Scrollable list area (300px height)

**Connected Tab:**
- Lists connected repos with: GitHub icon, name, Active badge, stats
- Each row has: External link button, Delete button (destructive style)
- Empty state: "No repositories connected yet." + Add button

**Add Tab:**
- Lists available repos not yet connected
- Each row has: GitHub icon, name, description, "Add" button
- Bottom card: "Configure GitHub App" link
- Empty state: "All available repositories are already connected."

---

### 5.5 IssueCard

**Technical Name:** `IssueCard`  
**File:** `src/components/IssueCard.tsx`

**Props:**
```typescript
interface IssueCardProps {
  issue: Issue;
  repoOwner: string;
  repoName: string;
}
```

**Structure:**
- Clickable card (navigates to issue detail)
- Left content:
  - Status icon + Issue number + Status badge
  - Title (truncated)
  - Checklist summary: passed/failed/pending counts with icons

**Status Icons/Colors:**
| Status | Icon | Color |
|--------|------|-------|
| open | Circle | muted-foreground |
| processing | Clock | warning |
| completed | CheckCircle2 | success |

---

### 5.6 PRCard

**Technical Name:** `PRCard`  
**File:** `src/components/PRCard.tsx`

**Props:**
```typescript
interface PRCardProps {
  prNumber: number;
  title: string;
  author: string;
  healthScore: number;
  repoOwner: string;
  repoName: string;
  validationStatus: 'pending' | 'validated' | 'needs_work';
}
```

**Structure:**
- Clickable card (navigates to PR detail)
- Left content: PR icon + number + status badge + title + author
- Right content: Health score (large number with TrendingUp icon)

**Status Badge Colors:**
| Status | Background | Text |
|--------|------------|------|
| pending | warning/10 | warning |
| validated | success/10 | success |
| needs_work | destructive/10 | destructive |

---

### 5.7 ChecklistItem

**Technical Name:** `ChecklistItem`  
**File:** `src/components/ChecklistItem.tsx`

**Props:**
```typescript
interface ChecklistItemProps {
  item: ChecklistItem;
}
```

**Structure:**
- Rounded container with status-colored background
- Left: Status icon
- Right: Item text + badges (Required, linked test count)

**Status Configuration:**
| Status | Icon | Color | Background |
|--------|------|-------|------------|
| passed | CheckCircle2 | success | success/10 |
| failed | XCircle | destructive | destructive/10 |
| pending | Clock | warning | warning/10 |
| skipped | Circle | muted-foreground | muted/10 |

---

### 5.8 SuggestedTestCard

**Technical Name:** `SuggestedTestCard`  
**File:** `src/components/SuggestedTestCard.tsx`

**Props:**
```typescript
interface SuggestedTestCardProps {
  test: SuggestedTest;
}
```

**Structure:**
- Card with header and content
- Header: Test name + framework badge + target + Copy button
- Content: Reasoning text (optional) + code snippet in pre/code block
- Footer: "Covers X checklist item(s)" text

**Copy Button Behavior:**
- Copies snippet to clipboard
- Shows "Copied" with Check icon for 2 seconds
- Returns to "Copy" with Copy icon

---

### 5.9 AuditPanel

**Technical Name:** `AuditPanel`  
**File:** `src/components/AuditPanel.tsx`

**Props:**
```typescript
interface AuditPanelProps {
  repoFullName: string;
  healthScore: number;
}
```

**Structure:**

1. **Stats Header (4-column grid)**
   - Total Issues (number)
   - Security Issues (destructive color)
   - Code Quality Issues (warning color)
   - Lines Analyzed (primary color, formatted with commas)

2. **Attention Banner** (if critical/high issues exist)
   - AlertCircle icon + message about critical/high count
   - "Export Report" button

3. **Issues Card**
   - Header: "Issues" + count
   - Tab filters: All | Security | Code Quality | Anti-patterns | Dead Code | Documentation | Complexity
   - Each tab shows count in parentheses
   - Empty tabs are hidden (except "All")
   - Issue list sorted by severity (critical → info)

**IssueRow Component (nested):**
- Expandable row with severity-colored background
- Collapsed: Icon + title + severity badge + category + file path
- Expanded: Description + suggested fix box + action buttons

**Severity Configuration:**
| Severity | Icon | Color | Border |
|----------|------|-------|--------|
| critical | AlertCircle | destructive | destructive/30 |
| high | AlertTriangle | warning | warning/30 |
| medium | AlertTriangle | amber-500 | amber-500/30 |
| low | Info | muted-foreground | muted/30 |
| info | Info | primary | primary/30 |

**Category Configuration:**
| Category | Icon | Label |
|----------|------|-------|
| security | ShieldAlert | Security |
| code-quality | FileCode | Code Quality |
| anti-patterns | Bug | Anti-patterns |
| dead-code | Trash2 | Dead Code |
| documentation | BookOpen | Documentation |
| complexity | Layers | Complexity |

---

## 6. State & Status Semantics

### 6.1 Issue Status

| Status | Meaning | Icon | Color |
|--------|---------|------|-------|
| `open` | Issue created, no processing started | Circle | muted |
| `processing` | Checklist is being generated | Clock | warning |
| `completed` | Checklist generation finished | CheckCircle2 | success |

### 6.2 Checklist Item Status

| Status | Meaning | When Used |
|--------|---------|-----------|
| `passed` | Test coverage verified | All linked tests pass |
| `failed` | Test coverage insufficient | Linked test fails |
| `pending` | Not yet evaluated | No test run yet |
| `skipped` | Intentionally not tested | Marked as skip |

### 6.3 PR Validation Status

| Status | Meaning | Badge Color | Action Available |
|--------|---------|-------------|------------------|
| `pending` | Validation in progress | warning | Revalidate |
| `validated` | All checks pass | success | Recommend Merge |
| `needs_work` | Issues found | destructive | Revalidate |

### 6.4 Audit Severity

| Severity | Urgency | Color Token |
|----------|---------|-------------|
| `critical` | Immediate action required | destructive |
| `high` | Should fix soon | warning |
| `medium` | Should address | amber-500 |
| `low` | Minor improvement | muted |
| `info` | Informational only | primary |

### 6.5 Health Score

- Numeric value 0-100
- Displayed with TrendingUp icon
- Always uses `text-primary` color
- Higher = better

---

## 7. UX Behavior Rules

### 7.1 What Must NOT Refresh
- Theme preference (persisted in localStorage)
- Current tab selection on RepoPage (preserved during tab switch)
- Dialog open state (user controls via triggers)

### 7.2 What Preserves State
- Search query in ManageReposDialog (within dialog session)
- Expanded/collapsed state of audit issue rows (within component session)
- Copied state on SuggestedTestCard (2 second timeout)

### 7.3 What is Read-Only
- Health scores (display only)
- Issue/PR metadata (created date, updated date)
- Checklist items (cannot be toggled by user)
- Audit issues (cannot be dismissed from UI)
- Lines analyzed count

### 7.4 What is Clickable vs Informational

**Clickable:**
- Repository cards → navigate to repo page
- Issue cards → navigate to issue detail
- PR cards → navigate to PR detail
- Logo → navigate to home
- External link buttons → open in new tab
- Tab triggers → switch tab content
- Audit issue rows → expand/collapse
- Copy buttons → copy to clipboard
- Action buttons (Regenerate, Revalidate, etc.)

**Informational (not clickable):**
- Health score displays
- Status badges
- Checklist progress bars
- Statistics (PR count, issue count)
- Breadcrumb parent path (back link is clickable)

---

## 8. Empty, Loading, and Error States

### 8.1 Loading States

**Skeleton Loading (used for initial page loads):**
- Dashboard: 3 skeleton cards in grid
- RepoPage: 1 tall skeleton (32px) + 1 very tall skeleton (96px)
- IssueDetail/PRDetail: Same pattern as RepoPage

**Spinner Loading (used for actions):**
- Regenerate button: RefreshCw icon with `animate-spin`
- Revalidate button: RefreshCw icon with `animate-spin`
- LoginCallback page: Loader2 icon with `animate-spin`

### 8.2 Empty States

| Location | Empty Condition | Message | Action |
|----------|-----------------|---------|--------|
| Dashboard repos | No repos | "No repositories found." | Install RevFlo button |
| RepoPage issues | No issues | "No issues found" | None |
| IssueDetail checklist | No items | "No checklist items generated yet." | None |
| PRDetail suggested tests | No tests | "No test suggestions available" | None |
| PRDetail code health | No issues | "No code health issues detected. Great work!" | None |
| Audit issues (filtered) | No matching | "No issues found in this category" | None |
| ManageRepos connected | No repos | "No repositories connected yet." | Add Repository button |
| ManageRepos available | All connected | "All available repositories are already connected." | Install on More Repos link |

### 8.3 Error States

**Not Found (entity missing):**
- Issue: Card with "Issue not found"
- PR: Card with "Pull request not found"
- Repo: Card with "Repository not found"

**Action Failures (toast notifications):**
- Regenerate failed: "Regeneration Failed" / "Unable to regenerate checklist. Please try again."
- Revalidate failed: "Revalidation Failed" / "Unable to revalidate PR. Please try again."
- Auth failed: "Authentication Failed" / "Unable to sign in. Please try again."

---

## 9. Navigation Contracts

### 9.1 Logo Click
- **From any page:** Navigates to `/`

### 9.2 Repository Card Click (Dashboard)
- **Target:** `/repo/{owner}/{name}`
- **Entire card is clickable**

### 9.3 Issue Card Click
- **Target:** `/repo/{owner}/{name}/issues/{issue_number}`
- **Entire card is clickable**

### 9.4 PR Card Click
- **Target:** `/repo/{owner}/{name}/prs/{pr_number}`
- **Entire card is clickable**

### 9.5 RepoSwitcher Selection
- **Target:** `/repo/{owner}/{name}`
- **Clicking "View all repositories":** `/dashboard`

### 9.6 Breadcrumb Back Link
- Issue/PR pages: "← Back to {owner}/{repo}" → `/repo/{owner}/{repo}`

### 9.7 External Links (open in new tab)
- "View on GitHub" buttons
- GitHub icon links
- "Install RevFlo" / "Configure GitHub App" links

### 9.8 What Does NOT Navigate
- Tab triggers (content swap only)
- Action buttons (Regenerate, Revalidate, Copy)
- Theme toggle
- Dialog triggers
- Audit issue rows (expand only)

---

## 10. API Contract Reference

### 10.1 Endpoints

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/me` | User |
| GET | `/api/repos` | RepoSummary[] |
| GET | `/api/repos/:owner/:repo` | RepoSummary |
| GET | `/api/repos/:owner/:repo/issues` | Issue[] |
| GET | `/api/repos/:owner/:repo/issues/:issueNumber` | Issue (with checklist) |
| POST | `/api/repos/:owner/:repo/issues/:issueNumber/regenerate` | void |
| GET | `/api/repos/:owner/:repo/prs/:prNumber` | PRDetail |
| POST | `/api/repos/:owner/:repo/prs/:prNumber/revalidate` | void |
| GET | `/api/notifications` | Notification[] |

### 10.2 Type Definitions

```typescript
interface User {
  id: string;
  login: string;
  avatar_url: string;
  name?: string;
  email?: string;
  managed_repos: string[];
}

interface RepoSummary {
  repo_full_name: string;
  owner: string;
  name: string;
  health_score: number;
  is_installed: boolean;
  pr_count: number;
  issue_count: number;
  last_activity?: string;
}

interface ChecklistItem {
  id: string;
  text: string;
  required: boolean;
  status: 'pending' | 'passed' | 'failed' | 'skipped';
  linked_tests: string[];
}

interface Issue {
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

interface TestResult {
  test_id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration_ms?: number;
  error_message?: string;
  checklist_ids: string[];
}

interface CodeHealthIssue {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  message: string;
  file_path: string;
  line_number?: number;
  suggestion?: string;
}

interface SuggestedTest {
  test_id: string;
  name: string;
  framework: string;
  target: string;
  checklist_ids: string[];
  snippet: string;
  reasoning?: string;
}

interface CoverageAdvice {
  file_path: string;
  lines: number[];
  suggestion: string;
}

interface PRDetail {
  pr_number: number;
  title: string;
  author: string;
  created_at: string;
  health_score: number;
  validation_status: 'pending' | 'validated' | 'needs_work';
  manifest?: {
    checklist_items: ChecklistItem[];
  };
  test_results: TestResult[];
  code_health: CodeHealthIssue[];
  coverage_advice: CoverageAdvice[];
  suggested_tests: SuggestedTest[];
  github_url: string;
}

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  repo_full_name?: string;
  created_at: string;
  read: boolean;
}
```

---

## 11. Acceptance Criteria Checklist

Use this checklist to verify implementation correctness. **If any item differs from this specification, the implementation is incorrect.**

### 11.1 Global Requirements

- [ ] App uses React 18+ with TypeScript
- [ ] Styling uses Tailwind CSS with exact color tokens from Section 3
- [ ] All icons are from Lucide React
- [ ] Header is sticky and 56px tall
- [ ] Theme toggle persists to localStorage
- [ ] Theme respects system preference on first load
- [ ] Logo click navigates to `/` from any page

### 11.2 Landing Page

- [ ] Shows unauthenticated header (no avatar, has Sign in button)
- [ ] Hero has exact heading: "Streamline your code review workflow"
- [ ] Features grid has exactly 6 cards with specified icons
- [ ] "Get started" navigates to `/auth/github`
- [ ] "View demo" navigates to `/dashboard`

### 11.3 Dashboard Page

- [ ] Shows authenticated header with avatar and RepoSwitcher
- [ ] Welcome message uses `user.name || user.login`
- [ ] "Manage Repositories" button opens dialog
- [ ] Repository cards are clickable and navigate to repo page
- [ ] Empty state shows "Install RevFlo" button
- [ ] Loading state shows 3 skeleton cards

### 11.4 Repository Page

- [ ] Shows repo name in monospace font
- [ ] Shows health score with TrendingUp icon
- [ ] Tab order: Issues | Pull Requests | Audit | Settings
- [ ] Default tab is "issues"
- [ ] Issue cards navigate to issue detail
- [ ] PR cards navigate to PR detail
- [ ] Audit tab shows AuditPanel with stats and issue list

### 11.5 Issue Detail Page

- [ ] Shows breadcrumb with back link
- [ ] Shows status badge with correct icon/color
- [ ] Progress bar reflects passed/total ratio
- [ ] Checklist shows items with correct status styling
- [ ] Regenerate button shows spinner while loading
- [ ] Regenerate shows toast notification

### 11.6 PR Detail Page

- [ ] Shows validation status badge
- [ ] Shows health score (large, right-aligned)
- [ ] "Recommend Merge" button only shows if status is "validated"
- [ ] Checklist coverage shows pass/warning icons
- [ ] Code health issues show severity badges
- [ ] Suggested tests have working Copy button
- [ ] Revalidate button shows spinner while loading

### 11.7 Audit Panel

- [ ] Stats header shows 4 cards in grid
- [ ] Attention banner shows if critical/high issues exist
- [ ] Tab filters show counts in parentheses
- [ ] Issues sorted by severity (critical first)
- [ ] Issue rows are expandable
- [ ] Expanded view shows suggestion in highlighted box

### 11.8 Manage Repos Dialog

- [ ] Opens from "Manage Repositories" button
- [ ] Has "Connected" and "Add Repository" tabs
- [ ] Search filters current tab's list
- [ ] Connected repos show Active badge if installed
- [ ] Delete button has destructive styling
- [ ] Add tab shows "Configure GitHub App" card at bottom

### 11.9 Status Semantics

- [ ] Issue status colors match specification
- [ ] Checklist item status colors match specification
- [ ] PR validation status colors match specification
- [ ] Audit severity colors match specification
- [ ] All status uses semantic color tokens (not hardcoded colors)

### 11.10 Empty & Loading States

- [ ] All empty states show exact messages from Section 8.2
- [ ] Loading uses skeletons for page loads
- [ ] Loading uses spinners for action buttons
- [ ] Error toasts match exact messages from Section 8.3

---

## Document End

This specification is complete. The Antigravity team should be able to rebuild the RevFlo frontend identically using this document as the sole reference.

**If any UI behavior is ambiguous or not covered in this document, consider it a specification gap to be clarified with the RevFlo team before implementing.**
