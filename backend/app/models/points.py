from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database.base import Base

class PointEventType(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    FAST_BONUS = "FAST_BONUS"
    QUALITY_BONUS = "QUALITY_BONUS"
    WRONG_ANSWER = "WRONG_ANSWER"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"

class StudentPointsEvent(Base):
    __tablename__ = "student_points_events"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type = Column(Enum(PointEventType), nullable=False)
    points = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    student = relationship("User", backref="points_events")
    classroom = relationship("Classroom", backref="points_events")
    submission = relationship("Submission", backref="points_events")
