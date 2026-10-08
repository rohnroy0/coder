from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
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
    hint_level = Column(Integer, nullable=False, default=1)
    summary = Column(Text, nullable=False)
    error_type = Column(Enum(ErrorCategory), nullable=False, default=ErrorCategory.LOGIC_ERROR)
    explanation = Column(Text, nullable=False)
    hint = Column(Text, nullable=False)
    next_step = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    submission = relationship("Submission", backref="feedback_list")
    student = relationship("User", backref="ai_feedbacks")
