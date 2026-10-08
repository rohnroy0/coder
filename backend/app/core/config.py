from typing import List
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Coder"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "super_secret_jwt_key_change_me_in_production_12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Browser origins allowed to call the API directly. The Vite dev server proxies /api
    # (same origin), so this only matters when the frontend is served from elsewhere.
    # Override in .env as a JSON list, e.g. CORS_ORIGINS=["https://classroom.example.com"]
    CORS_ORIGINS: List[str] = ["http://localhost:5180", "http://127.0.0.1:5180"]

    # Database URL. Defaults to local SQLite if PostgreSQL is not provided or unavailable
    DATABASE_URL: str = "sqlite:///./ai_code_classroom.db"

    # Ollama AI Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_TIMEOUT: int = 120
    AI_MAX_RETRIES: int = 3
    AI_PROVIDER_TYPE: str = "ollama"

    # Debug: keep finished code-runner containers (visible in Docker Desktop as "Exited")
    # instead of auto-removing them. Clean up with: docker container prune --filter label=app=code-runner
    RUNNER_KEEP_CONTAINERS: bool = False

    # Phase 6 Configurable Scoring System & Analytics Thresholds
    POINTS_ACCEPTED: int = 100
    POINTS_FAST_BONUS: int = 20
    POINTS_CLEAN_BONUS: int = 10
    POINTS_WRONG: int = -5
    POINTS_RUNTIME_ERROR: int = -5
    POINTS_TIMEOUT: int = -5
    FAST_EXECUTION_THRESHOLD: float = 0.05
    MAX_PENALTY_EVENTS_PER_PROBLEM: int = 5
    STRENGTH_THRESHOLD_STRONG: float = 80.0
    STRENGTH_THRESHOLD_DEVELOPING: float = 50.0

    # Gamification: points required to advance one level (flat, transparent curve)
    POINTS_PER_LEVEL: int = 200

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
