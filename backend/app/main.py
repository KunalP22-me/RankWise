"""RankWise FastAPI application — main entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import bias, candidates, chat, evaluation, jobs, overrides, rankings

logger = logging.getLogger("rankwise")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("RankWise starting up...")
    create_tables()
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("Database tables created, upload dir ready.")
    yield
    # Shutdown
    logger.info("RankWise shutting down.")


app = FastAPI(
    title="RankWise",
    description="AI-Powered Resume Screening & Candidate Ranking System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(jobs.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(rankings.router, prefix="/api")
app.include_router(overrides.router, prefix="/api")
app.include_router(bias.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "llm_provider": settings.llm_provider,
    }
