import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings, DEFAULT_INSECURE_SECRET_KEY
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

logger = logging.getLogger(__name__)


def _ensure_column(engine_, table: str, column: str, ddl_type: str) -> None:
    """Add a column to an existing table if it's missing (lightweight startup
    migration for deployments created before the column existed). No-op when
    the table doesn't exist yet or the column is already present."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine_)
    if table not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    if column in existing:
        return
    with engine_.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
    logger.info("Added missing column %s.%s to existing database", table, column)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.SECRET_KEY == DEFAULT_INSECURE_SECRET_KEY:
        logger.warning(
            "SECURITY: SECRET_KEY is the publicly committed default. Anyone who has "
            "read the repository can forge login tokens for any user. Set a unique "
            "SECRET_KEY in backend/.env before exposing this server to a network."
        )
    if not settings.TEACHER_SIGNUP_CODE:
        logger.warning(
            "TEACHER_SIGNUP_CODE is not set: anyone can self-register a TEACHER "
            "account. Set it in backend/.env for any non-local deployment."
        )
    if settings.AI_PROVIDER_TYPE.lower() in ("groq", "gemini", "openai_compat") and not settings.AI_API_KEY:
        logger.warning(
            "AI_PROVIDER_TYPE=%s is selected but AI_API_KEY is empty - every AI "
            "feature will return 'unavailable' until a key is set in backend/.env.",
            settings.AI_PROVIDER_TYPE,
        )

    # Auto-create tables on startup (works with PostgreSQL & SQLite)
    Base.metadata.create_all(bind=engine)

    # create_all only creates MISSING tables - it never alters existing ones,
    # so columns added to a model after a deployment's DB was first created
    # must be patched in here or every query on that table breaks.
    _ensure_column(engine, "ai_feedback", "requested_by", "INTEGER")

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
