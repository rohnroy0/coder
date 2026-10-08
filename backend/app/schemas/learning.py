from typing import List, Optional
from pydantic import BaseModel


class ChapterProblemSummary(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    order: int
    solved: bool = False


class ChapterPathItem(BaseModel):
    """One chapter/concept node as seen by a student: progress, lock state,
    difficulty and XP included, ready to render as a learning-path node."""
    id: int
    language: str
    title: str
    description: Optional[str] = None
    order: int
    difficulty: str  # EASY | MEDIUM | HARD
    total_problems: int
    completed_problems: int
    progress_pct: float
    xp_reward: int  # total XP available for this chapter
    xp_earned: int  # XP earned so far (0 until problems are solved)
    state: str  # LOCKED | AVAILABLE | IN_PROGRESS | COMPLETED | MASTERED
    is_unlocked: bool
    is_completed: bool
    is_mastered: bool
    prerequisite_title: Optional[str] = None  # set only when locked
    problems: List[ChapterProblemSummary] = []
