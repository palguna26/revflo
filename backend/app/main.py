from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1.endpoints import auth, issues, me, notifications, prs, repos, analytics, settings as repo_settings, ai_endpoints, webhook, audit

# Placeholder for scheduler - will be implemented later
from app.tasks.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    start_scheduler()
    yield
    # Shutdown
    await stop_scheduler()

settings = get_settings()

app = FastAPI(
    title="RevFlo API",
    version="1.0.0",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    lifespan=lifespan,
)

# CORS
allowed_origins = {settings.frontend_url}
allowed_origins.update(
    {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI(openapi_url=None, docs_url=None)

api.include_router(auth.router)
api.include_router(me.router)
api.include_router(repos.router)
api.include_router(issues.router)
api.include_router(prs.router)
api.include_router(notifications.router)
api.include_router(analytics.router)
api.include_router(repo_settings.router)
api.include_router(ai_endpoints.router)
api.include_router(webhook.router)
api.include_router(audit.router)


app.mount(settings.api_prefix, api)
@app.get("/health")
def health():
    return {"status": "ok"}