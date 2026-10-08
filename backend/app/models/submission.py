from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from app.database.base import Base

class SubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(50), nullable=False)
    source_code = Column(Text, nullable=False)
    status = Column(Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.PENDING)
    execution_time = Column(Float, nullable=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="submissions")
    problem = relationship("Problem", back_populates="submissions")
    assignment = relationship("Assignment", backref="submissions")
