from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.base import Base

class ProblemDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"

class ProblemStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum(ProblemDifficulty), nullable=False, default=ProblemDifficulty.EASY)
    status = Column(Enum(ProblemStatus), nullable=False, default=ProblemStatus.VERIFIED)
    topic = Column(String(100), nullable=True)
    language = Column(String(50), nullable=True, default="python")
    constraints = Column(Text, nullable=True)
    input_format = Column(Text, nullable=True)
    output_format = Column(Text, nullable=True)
    examples = Column(Text, nullable=True)
    reference_solution = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    creator = relationship("User", backref="created_problems")
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem", cascade="all, delete-orphan")
    # Without these two, deleting a Problem that's attached to any assignment or
    # learning-path chapter raises an IntegrityError: SQLAlchemy's default for an
    # uncascaded relationship is to null the child's FK, but both of these FKs are
    # NOT NULL - cascade-deleting the join rows (same as test_cases/submissions
    # above) is what actually lets the delete succeed.
    assignment_associations = relationship("AssignmentProblem", back_populates="problem", cascade="all, delete-orphan")
    chapter_associations = relationship("LearningChapterProblem", back_populates="problem", cascade="all, delete-orphan")

class TestCase(Base):
    __test__ = False  # not a pytest test class
    __tablename__ = "testcases"

    id = Column(Integer, primary_key=True, index=True)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)

    # Relationships
    problem = relationship("Problem", back_populates="test_cases")
