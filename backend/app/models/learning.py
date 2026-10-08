from app.core.time import utcnow
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base


class LearningChapter(Base):
    """
    One chapter in a language's self-paced learning path (Duolingo-style):
    an ordered set of existing Problems a student must all solve to complete
    the chapter. Chapters are global (not classroom-scoped) and ordered within
    their language via `order` - completing chapter N unlocks chapter N+1.
    """
    __tablename__ = "learning_chapters"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String(20), nullable=False, index=True)  # python | c | cpp
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    creator = relationship("User", backref="created_chapters")
    problems = relationship(
        "LearningChapterProblem", back_populates="chapter",
        cascade="all, delete-orphan", order_by="LearningChapterProblem.order"
    )


class LearningChapterProblem(Base):
    __tablename__ = "learning_chapter_problems"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("learning_chapters.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(Integer, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    order = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("chapter_id", "problem_id", name="uq_chapter_problem"),
    )

    chapter = relationship("LearningChapter", back_populates="problems")
    problem = relationship("Problem", back_populates="chapter_associations")
