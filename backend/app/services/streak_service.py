from datetime import date, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.submission import Submission


class StreakService:
    """
    Learning Streak Engine.

    A day counts as "active" if the student made at least one submission
    (of any result) that day - practice and failed attempts count just as
    much toward consistency as accepted ones. Streak is personal to the
    student across all of their activity, not scoped to any one classroom:
    a student should not lose their streak just because today's coding
    happened in a different class.
    """

    @staticmethod
    def compute_streak(db: Session, student_id: int) -> Dict[str, Optional[int]]:
        rows = db.query(Submission.created_at).filter(Submission.user_id == student_id).all()
        active_dates = {created_at.date() for (created_at,) in rows}

        if not active_dates:
            return {"current_streak": 0, "longest_streak": 0, "last_active_date": None}

        today = utcnow().date()
        if today in active_dates:
            cursor: Optional[date] = today
        elif (today - timedelta(days=1)) in active_dates:
            cursor = today - timedelta(days=1)
        else:
            cursor = None

        current_streak = 0
        while cursor is not None and cursor in active_dates:
            current_streak += 1
            cursor -= timedelta(days=1)

        longest_streak = 0
        run = 0
        prev: Optional[date] = None
        for d in sorted(active_dates):
            run = run + 1 if prev is not None and (d - prev).days == 1 else 1
            longest_streak = max(longest_streak, run)
            prev = d

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_active_date": max(active_dates).isoformat(),
        }
