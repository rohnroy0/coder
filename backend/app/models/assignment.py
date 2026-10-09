from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base

class AssignmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"

class AssignmentProgressStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(AssignmentStatus), nullable=False, default=AssignmentStatus.DRAFT)
    start_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    total_points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    classroom = relationship("Classroom", back_populates="assignments")
    teacher = relationship("User", backref="created_assignments")
    problems = relationship("AssignmentProblem", back_populates="assignment", cascade="all, delete-orphan", order_by="AssignmentProblem.order")
    student_progress = relationship("AssignmentStudentProgress", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentProblem(Base):
    __tablename__ = "assignment_problems"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False, default=100)
    order = Column(Integer, nullable=False, default=0)

    # Relationships
    assignment = relationship("Assignment", back_populates="problems")
    problem = relationship("Problem", back_populates="assignment_associations")


class AssignmentStudentProgress(Base):
    __tablename__ = "assignment_student_progress"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    completed_problems = Column(Integer, nullable=False, default=0)
    total_problems = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=False, default=0)
    status = Column(Enum(AssignmentProgressStatus), nullable=False, default=AssignmentProgressStatus.NOT_STARTED)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),
    )

    # Relationships
    assignment = relationship("Assignment", back_populates="student_progress")
    student = relationship("User", backref="assignment_progress")
