from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import interview
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered interview assessment API. Upload audio or video recordings "
        "to receive transcript, audio metrics, and LLM-based evaluation across "
        "communication, technical, and behavioral dimensions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "analyze_endpoint": "POST /api/v1/interview/analyze",
    }
