"""FastAPI entrypoint for the multi-tenant SaaS MVP API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routers import auth_router, doc_router, admin_router, webhook_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API for the multi-tenant SaaS MVP (auth, transfers, admin, webhooks).",
)

# Demo-friendly CORS. Tighten allow_origins before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(doc_router.router)
app.include_router(admin_router.router)
app.include_router(webhook_router.router)

# Exposes GET /metrics for Prometheus.
Instrumentator().instrument(app).expose(app)


@app.get("/")
def read_root():
    """Liveness-style root used by quick health checks."""
    return {
        "status": "OK",
        "message": f"{settings.PROJECT_NAME} is running",
        "docs_url": "/docs",
        "author": "cesar-andress",
    }
