import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.database.base import Base
from app.database.session import get_db

# Explicitly import models so Base.metadata contains all table definitions
from app.models.user import User, UserRole
from app.models.classroom import Classroom, ClassroomMember
from app.models.problem import Problem, TestCase, ProblemDifficulty
from app.models.submission import Submission, SubmissionStatus
from app.models.assignment import Assignment, AssignmentProblem, AssignmentStudentProgress

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

# StaticPool ensures all connections share the same in-memory SQLite database.
# Without this, each new connection gets an empty DB and tables are missing.
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Override get_db to use the shared in-memory test DB.
    TestClient is NOT used as a context manager to avoid triggering the
    FastAPI lifespan (which calls create_all on the real production engine).
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(fastapi_app, raise_server_exceptions=True)
    yield test_client
    fastapi_app.dependency_overrides.clear()
