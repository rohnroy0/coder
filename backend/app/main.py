from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.code_runner import SandboxUnavailableError
from app.core.seed_learning_curriculum import seed_learning_curriculum
from app.database.base import Base
from app.database.session import engine, SessionLocal
# Import models to ensure they are registered with Base metadata
import app.models  # noqa

from app.api.auth import router as auth_router
from app.api.classrooms import router as classrooms_router
from app.api.problems import router as problems_router
from app.api.submissions import router as submissions_router
from app.api.analytics import router as analytics_router
from app.api.assignments import router as assignments_router
from app.api.badges import router as badges_router
from app.api.learning import router as learning_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup (works with PostgreSQL & SQLite)
    Base.metadata.create_all(bind=engine)

    # Seed the built-in self-paced learning curriculum (no-op once it exists)
    db = SessionLocal()
    try:
        seed_learning_curriculum(db)
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Coder - A Smarter Coding Platform for Every Student and Teacher",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(classrooms_router, prefix=settings.API_V1_STR)
app.include_router(problems_router, prefix=settings.API_V1_STR)
app.include_router(submissions_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(assignments_router, prefix=settings.API_V1_STR)
app.include_router(badges_router, prefix=settings.API_V1_STR)
app.include_router(learning_router, prefix=settings.API_V1_STR)

@app.exception_handler(SandboxUnavailableError)
async def sandbox_unavailable_handler(request: Request, exc: SandboxUnavailableError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

@app.get("/")
def root():
    return {
        "message": "Welcome to the Coder API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
