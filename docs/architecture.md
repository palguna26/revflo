# Project Architecture

This document provides a high-level overview of the QuantumReview (RevFlo) application architecture, detailing the Multi-Engine AI System and the Issue-Centric Validation flow.

## Architecture Diagram

```mermaid
graph TD
    subgraph Client ["Client Layer"]
        UserBrowser[Web Browser]
    end

    subgraph Frontend ["Frontend (React + Vite)"]
        direction TB
        subgraph UI_Components ["UI Components"]
            Dashboard[Dashboard]
            RepoView[Repository View]
            IssuePage[Issue Page (Control Center)]
            PRView[PR Detail View]
        end
        API_Client[API Client (axios/fetch)]
        QueryClient[TanStack Query Cache]
        
        UserBrowser --> UI_Components
        UI_Components --> QueryClient
        QueryClient --> API_Client
    end

    subgraph Backend ["Backend (FastAPI)"]
        direction TB
        
        subgraph API_Layer ["API Endpoints (Routers)"]
            AuthAPI[Auth Router]
            MeAPI[Me Router]
            ReposAPI[Repos Router]
            IssuesAPI[Issues Router]
            PRsAPI[PRs Router]
        end

        subgraph Service_Layer ["Service Layer"]
            RepoSvc[Repo Service]
            IssueSvc[Issue Service]
            PRSvc[PR Service]
            
            subgraph AI_Core ["AI Multi-Engine Core"]
                Quantum[Quantum Engine (Checklists)]
                CodeAnt[CodeAnt Engine (Analysis)]
                Qodo[Qodo Engine (Tests & Fixes)]
            end
        end
        
        subgraph Task_Layer ["Background Tasks"]
            Scheduler[APScheduler]
            SyncTask[Repo Sync Task]
        end
        
        API_Client -->|HTTPS| API_Layer
        
        AuthAPI --> RepoSvc
        MeAPI --> RepoSvc
        ReposAPI --> RepoSvc
        IssuesAPI --> IssueSvc
        IssuesAPI --> Quantum
        PRsAPI --> PRSvc
        
        IssueSvc --> Quantum
        PRSvc --> CodeAnt
        PRSvc --> Qodo
        
        Scheduler -->|Triggers| SyncTask
        SyncTask --> RepoSvc
    end

    subgraph Data_Layer ["Data Persistence (MongoDB)"]
        Collections[(Collections)]
        note[Collections: Users, Repos, Issues, PullRequests]
        
        Service_Layer -->|Reads/Writes| Collections
    end

    subgraph External ["External Integrations"]
        GitHubAPI[GitHub API]
        GroqAPI[Groq LLM API]
        
        Service_Layer -->|OAuth/Data| GitHubAPI
        AI_Core -->|Inference| GroqAPI
    end
```

## Core Components

### 1. The Multi-Engine AI Core
RevFlo utilizes three specialized AI engines, each optimized for a specific stage of the development lifecycle:

-   **Quantum Engine (`quantum.py`)**:
    -   **Role**: Requirements Analysis & Planning.
    -   **Input**: GitHub Issue Title & Description.
    -   **Output**: Unified AC (Acceptance Criteria) Checklist.
    -   **Function**: Converts vague requirements into a structured, validate-able checklist that serves as the "Source of Truth" for PRs.

-   **CodeAnt Engine (`codeant.py`)**:
    -   **Role**: Static Analysis & Code Health.
    -   **Input**: PR Diff & Context.
    -   **Output**: Code Health Issues (Security, Performance, Style) & Health Score.
    -   **Function**: Acts as the automated code reviewer, flagging specific lines and assigning a health score (0-100).

-   **Qodo Engine (`qodo.py`)**:
    -   **Role**: Generation & Test Coverage.
    -   **Input**: PR Diff.
    -   **Output**: Suggested `pytest` Test Cases.
    -   **Function**: Generates executable test code to ensure the new changes are covered, preventing regressions.

### 2. The Issue-Centric Validation Flow
Unlike traditional tools that only look at PRs, RevFlo anchors everything to the **Issue**.

1.  **Plan**: User creates an Issue. **Quantum Engine** generates a Checklist.
2.  **Code**: User opens a PR and links it to the Issue.
3.  **Validate**: User triggers "Run Review" from the **Issue Page**.
    -   **CodeAnt** scans the PR quality.
    -   **Qodo** suggests tests.
    -   The PR is validated *against* the **Quantum Checklist**.
4.  **Merge**: Only when the PR satisfies the Issue's checklist (Source of Truth) is it marked as "Validated".

### 3. Backend (FastAPI + Beanie)
-   **Service Layer Pattern**: All business logic resides in `services/`, keeping endpoints (`api/`) clean.
-   **Async First**: Built on `asyncio` and `Motor` to handle concurrent AI requests and GitHub syncing without blocking.
-   **Background Tasks**: Heavy lifting (syncing repos, long-running analysis) is offloaded to background threads.

### 4. Frontend (React + Vite)
-   **Dashboard**: A 12-column grid layout providing a high-density view of repository health.
-   **Issue Control Center**: The central hub for validation.
-   **PR Detail View**: A read-only report of the analysis, showing Health Score, Issues, and Coverage logic.
