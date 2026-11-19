from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship, backref
from app.database.base import Base

class ErrorCategory(str, enum.Enum):
    LOGIC_ERROR = "LOGIC_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    ALGORITHM_ERROR = "ALGORITHM_ERROR"
    EDGE_CASE = "EDGE_CASE"
    TIME_COMPLEXITY = "TIME_COMPLEXITY"
    INPUT_OUTPUT = "INPUT_OUTPUT"
    DATA_STRUCTURE = "DATA_STRUCTURE"
    OTHER = "OTHER"

class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Who asked for this feedback. student_id is always the submission's owner;
    # a TEACHER can also request feedback on a student's submission, and those
    # rows must not count toward the student's own hint-usage stats. Nullable:
    # rows from before this column existed (added at startup for legacy DBs).
    requested_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    hint_level = Column(Integer, nullable=False, default=1)
    summary = Column(Text, nullable=False)
    error_type = Column(Enum(ErrorCategory), nullable=False, default=ErrorCategory.LOGIC_ERROR)
    explanation = Column(Text, nullable=False)
    hint = Column(Text, nullable=False)
    next_step = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships. Without delete-orphan cascade here, ORM-deleting a
    # Submission (e.g. cascading from a Problem delete) tries to NULL this
    # NOT NULL FK instead of deleting the feedback row -> IntegrityError 500.
    submission = relationship(
        "Submission",
        backref=backref("feedback_list", cascade="all, delete-orphan")
    )
    student = relationship(
        "User",
        foreign_keys=[student_id],
        backref=backref("ai_feedbacks", cascade="all, delete-orphan")
    )
    requester = relationship("User", foreign_keys=[requested_by])
