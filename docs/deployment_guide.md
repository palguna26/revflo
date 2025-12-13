# RevFlo Deployment Guide 🚀

## 1. Pre-Deployment Checklist
- [ ] **Docker Installed**: Ensure Docker & Docker Compose are installed on the target server (Ubuntu LTS recommended).
- [ ] **Domain Name**: Have a domain ready (e.g., `revflo.yourdomain.com`) and DNS access.
- [ ] **GitHub App**: Created in GitHub Developer Settings.
- [ ] **Groq API Key**: Valid key with sufficient credits.
- [ ] **MongoDB**: A production MongoDB Atlas instance is recommended (or use the included container with volumes).

## 2. Environment Variables
Create a `.env.production` file on your server (or inject via CI/CD).

```ini
# --- Backend ---
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=revflo_production
API_PREFIX=/api
FRONTEND_URL=https://revflo.yourdomain.com

# Auth
SECRET_KEY=<generate_secure_random_string_openssl_rand_base64_32>
ACCESS_TOKEN_EXPIRE_MINUTES=10080 # 7 Days

# GitHub App Integration
GITHUB_CLIENT_ID=<from_github_app>
GITHUB_CLIENT_SECRET=<from_github_app>
GITHUB_REDIRECT_URI=https://revflo.yourdomain.com/auth/github/callback

# AI
GROQ_API_KEY=gsk_...

# --- Frontend (Build Time) ---
VITE_API_BASE=https://revflo.yourdomain.com/api
```

## 3. GitHub App Configuration
1.  Go to **GitHub Developer Settings > GitHub Apps > New GitHub App**.
2.  **Homepage URL**: `https://revflo.yourdomain.com`
3.  **Callback URL**: `https://revflo.yourdomain.com/auth/github/callback`
4.  **Webhook URL**: `https://revflo.yourdomain.com/api/webhook` (Ensure this is reachable!)
5.  **Permissions**:
    *   **Repository limits**: All repositories (or strictly public).
    *   **Contents**: `Read` (to fetch code).
    *   **Pull Requests**: `Read & Write` (to comment/review).
    *   **Issues**: `Read & Write` (to post checklists).
    *   **Metadata**: `Read`.
6.  **Subscribe to events**: `Pull request`, `Issue`, `Push`.

## 4. Production Deployment (Docker Compose)
We will use a production-optimized `docker-compose.prod.yml`.

**Step 1: Create `docker-compose.prod.yml`**
```yaml
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    env_file: .env.production
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_BASE=https://revflo.yourdomain.com/api
    restart: always
    ports:
      - "80:80"

  # Optional: Nginx proxy if not using an external load balancer
  # nginx: ...
```

**Step 2: Deploy**
```bash
# Pull latest code
git pull origin main

# Build and Start
docker-compose -f docker-compose.prod.yml up -d --build
```

## 5. Domain & HTTPS (Caddy Example)
The easiest way to handle HTTPS is using Caddy as a reverse proxy in front of your Docker containers.

**Caddyfile**:
```caddy
revflo.yourdomain.com {
    reverse_proxy /api/* localhost:8000
    reverse_proxy /* localhost:80
}
```

## 6. Post-Deployment Validation
1.  **Health Check**: Visit `https://revflo.yourdomain.com/api/docs`. Ensure Swagger UI loads.
2.  **Login**: Try logging in via GitHub.
3.  **Webhook Test**:
    *   Install the GitHub App on a *test* repository.
    *   Create a stored issue.
    *   Verify a checklist appears in RevFlo within 30 seconds.

## 7. Rollback Plan
If deployment fails:

1.  **Revert Code**: `git checkout <previous_commit_hash>`
2.  **Rebuild**: `docker-compose -f docker-compose.prod.yml up -d --build`
3.  **Verify**: Log in and check `git log` on server.

---
**Status**: 🟢 READY TO DEPLOY
