# RevFlo

RevFlo is an autonomous AI code review platform that anchors validation to the "Issue" as the source of truth. It integrates seamlessly with GitHub to provide a 3-stage validation pipeline: **Plan (Quantum)**, **Analyze (CodeAnt)**, and **Test (Qodo)**.

## Core Features

-   **Issue-Centric Validation**: Convert vague GitHub Issue descriptions into strict technical **Checklists** (Source of Truth).
-   **3-Engine AI Architecture**:
    -   **Quantum Engine**: Requirements analysis & checklist generation.
    -   **CodeAnt Engine**: Deep static analysis for Security, Performance, and Style logic.
    -   **Qodo Engine**: Automated generation of `pytest` test cases for PR coverage.
-   **Live Dashboard**: Real-time health scores (0-100), activity tracking, and critical AI insights.
-   **Smart Revalidation**: Intelligent caching prevents re-analyzing unchanged PRs, saving API costs and time.

## Tech Stack

### Frontend
-   **Framework**: [React](https://react.dev/) (v18) + [Vite](https://vitejs.dev/)
-   **Language**: [TypeScript](https://www.typescriptlang.org/)
-   **UI**: [Shadcn UI](https://ui.shadcn.com/) (Radix + Tailwind) + Lucide Icons
-   **State**: [TanStack Query](https://tanstack.com/query)
-   **Styles**: Strict 12-Column Grid Layout (Tailwind CSS)

### Backend
-   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Async)
-   **Language**: Python 3.10+
-   **Database**: MongoDB (via [Beanie](https://beanie-odm.dev/) ODM)
-   **AI**: [Groq](https://groq.com/) API (Llama 3.1 8b / 70b)
-   **Tasks**: Background Workers for GitHub Sync

## Getting Started

### Prerequisites
-   Node.js (v18+)
-   Python (v3.10+)
-   MongoDB Instance
-   Groq API Key
-   GitHub Token

### Quick Start (Docker)
The easiest way to run RevFlo is with Docker Compose.

```bash
make docker-up
```
-   **Frontend**: http://localhost:80
-   **Backend**: http://localhost:8000

### Manual Setup

1.  **Backend**
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    ```

2.  **Frontend**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Development Workflow
1.  **Create Issue**: Start by creating an issue on GitHub.
2.  **Generate Checklist**: In RevFlo, generate the acceptance criteria.
3.  **Code & PR**: Push code and open a PR.
4.  **Run Review**: Validate the PR *against* the Issue's checklist on RevFlo.
5.  **Merge**: Once validated, merge with confidence.
