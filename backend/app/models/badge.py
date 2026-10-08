from app.core.time import utcnow
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class StudentBadge(Base):
    """
    Records that a student has earned a badge. Badge metadata (name, description,
    icon, unlock criteria) lives in code (BadgeService.BADGE_CATALOG), not the
    database - this table only tracks the student/badge/earned-at fact, keyed by
    the badge's stable `code`.
    """
    __tablename__ = "student_badges"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_code = Column(String(50), nullable=False, index=True)
    earned_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "badge_code", name="uq_student_badge"),
    )

    student = relationship("User", backref="badges")
