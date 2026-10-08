from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.submission import Submission, SubmissionStatus
from app.models.points import StudentPointsEvent, PointEventType
from app.models.assignment import AssignmentStudentProgress, AssignmentProgressStatus
from app.models.badge import StudentBadge
from app.services.streak_service import StreakService

JUDGED_STATUSES = (
    SubmissionStatus.ACCEPTED,
    SubmissionStatus.WRONG_ANSWER,
    SubmissionStatus.RUNTIME_ERROR,
    SubmissionStatus.TIME_LIMIT_EXCEEDED,
)

# Badge catalog: static, code-defined metadata + unlock criteria over a student's
# lifetime stats. `code` is the stable key persisted in StudentBadge - never
# rename or reuse a code without migrating existing earned records.
BADGE_CATALOG: List[Dict[str, Any]] = [
    {
        "code": "FIRST_SOLVE", "name": "First Blood", "icon": "🥇",
        "description": "Solve your first problem.",
        "check": lambda s: s["problems_solved"] >= 1,
        "hint": lambda s: f"{min(s['problems_solved'], 1)}/1 problems solved",
    },
    {
        "code": "SOLVED_10", "name": "Problem Solver", "icon": "🧩",
        "description": "Solve 10 problems.",
        "check": lambda s: s["problems_solved"] >= 10,
        "hint": lambda s: f"{min(s['problems_solved'], 10)}/10 problems solved",
    },
    {
        "code": "SOLVED_25", "name": "Problem Crusher", "icon": "💪",
        "description": "Solve 25 problems.",
        "check": lambda s: s["problems_solved"] >= 25,
        "hint": lambda s: f"{min(s['problems_solved'], 25)}/25 problems solved",
    },
    {
        "code": "SHARPSHOOTER", "name": "Sharpshooter", "icon": "🎯",
        "description": "Maintain 80%+ submission accuracy over at least 10 submissions.",
        "check": lambda s: s["total_submissions"] >= 10 and s["submission_accuracy"] >= 80.0,
        "hint": lambda s: (
            f"{s['total_submissions']}/10 submissions made"
            if s["total_submissions"] < 10
            else f"{s['submission_accuracy']}% accuracy (need 80%+)"
        ),
    },
    {
        "code": "SPEED_DEMON", "name": "Speed Demon", "icon": "⚡",
        "description": "Earn a fast-execution bonus on a submission.",
        "check": lambda s: s["fast_bonus_count"] >= 1,
        "hint": lambda s: "Get a solution running in ≤ 0.05s",
    },
    {
        "code": "CLEAN_CODER", "name": "Clean Coder", "icon": "✨",
        "description": "Solve a problem correctly on your very first attempt.",
        "check": lambda s: s["quality_bonus_count"] >= 1,
        "hint": lambda s: "Solve any problem correctly on attempt #1",
    },
    {
        "code": "STREAK_3", "name": "Getting Started", "icon": "🔥",
        "description": "Reach a 3-day learning streak.",
        "check": lambda s: s["longest_streak"] >= 3,
        "hint": lambda s: f"{min(s['longest_streak'], 3)}/3 day streak",
    },
    {
        "code": "STREAK_7", "name": "Consistent Coder", "icon": "🔥",
        "description": "Reach a 7-day learning streak.",
        "check": lambda s: s["longest_streak"] >= 7,
        "hint": lambda s: f"{min(s['longest_streak'], 7)}/7 day streak",
    },
    {
        "code": "STREAK_30", "name": "Unstoppable", "icon": "🔥",
        "description": "Reach a 30-day learning streak.",
        "check": lambda s: s["longest_streak"] >= 30,
        "hint": lambda s: f"{min(s['longest_streak'], 30)}/30 day streak",
    },
    {
        "code": "ASSIGNMENT_ACE", "name": "Assignment Ace", "icon": "🏆",
        "description": "Complete 5 assignments.",
        "check": lambda s: s["assignments_completed"] >= 5,
        "hint": lambda s: f"{min(s['assignments_completed'], 5)}/5 assignments completed",
    },
]


class BadgeService:

    @staticmethod
    def get_catalog() -> List[Dict[str, str]]:
        """All badges that exist, earned or not - for a locked/unlocked display."""
        return [{"code": b["code"], "name": b["name"], "description": b["description"], "icon": b["icon"]}
                 for b in BADGE_CATALOG]

    @staticmethod
    def get_status_for_student(db: Session, student_id: int) -> List[Dict[str, Any]]:
        """
        Full catalog merged with this student's progress: earned badges carry
        their earned_at timestamp, locked ones carry a short "how close am I"
        hint computed from the student's current stats.
        """
        earned_at_by_code = {
            row.badge_code: row.earned_at
            for row in db.query(StudentBadge).filter(StudentBadge.student_id == student_id)
        }
        stats = None
        if any(b["code"] not in earned_at_by_code for b in BADGE_CATALOG):
            stats = BadgeService._compute_stats(db, student_id)

        statuses = []
        for b in BADGE_CATALOG:
            earned_at = earned_at_by_code.get(b["code"])
            statuses.append({
                "code": b["code"], "name": b["name"],
                "description": b["description"], "icon": b["icon"],
                "earned": earned_at is not None,
                "earned_at": earned_at,
                "unlock_hint": None if earned_at is not None else b["hint"](stats),
            })
        return statuses

    @staticmethod
    def _compute_stats(db: Session, student_id: int) -> Dict[str, Any]:
        submissions = db.query(Submission).filter(
            Submission.user_id == student_id, Submission.status.in_(JUDGED_STATUSES)
        ).all()
        accepted = [s for s in submissions if s.status == SubmissionStatus.ACCEPTED]
        total_submissions = len(submissions)

        fast_bonus_count = db.query(StudentPointsEvent).filter(
            StudentPointsEvent.student_id == student_id,
            StudentPointsEvent.event_type == PointEventType.FAST_BONUS
        ).count()
        quality_bonus_count = db.query(StudentPointsEvent).filter(
            StudentPointsEvent.student_id == student_id,
            StudentPointsEvent.event_type == PointEventType.QUALITY_BONUS
        ).count()
        assignments_completed = db.query(AssignmentStudentProgress).filter(
            AssignmentStudentProgress.student_id == student_id,
            AssignmentStudentProgress.status == AssignmentProgressStatus.COMPLETED
        ).count()

        streak = StreakService.compute_streak(db, student_id)

        return {
            "problems_solved": len({s.problem_id for s in accepted}),
            "total_submissions": total_submissions,
            "submission_accuracy": round(len(accepted) / total_submissions * 100.0, 1) if total_submissions else 0.0,
            "current_streak": streak["current_streak"],
            "longest_streak": streak["longest_streak"],
            "fast_bonus_count": fast_bonus_count,
            "quality_bonus_count": quality_bonus_count,
            "assignments_completed": assignments_completed,
        }

    @staticmethod
    def evaluate_and_award(db: Session, student_id: int) -> List[Dict[str, Any]]:
        """
        Checks all not-yet-earned badges against the student's current stats and
        persists any newly met ones. Returns the list of badges newly awarded by
        this call (empty if none), so callers can surface an "earned!" moment.
        """
        already_earned = {
            row[0] for row in db.query(StudentBadge.badge_code).filter(StudentBadge.student_id == student_id)
        }
        pending = [b for b in BADGE_CATALOG if b["code"] not in already_earned]
        if not pending:
            return []

        stats = BadgeService._compute_stats(db, student_id)

        newly_awarded = []
        for badge in pending:
            if not badge["check"](stats):
                continue
            row = StudentBadge(student_id=student_id, badge_code=badge["code"])
            db.add(row)
            db.flush()
            newly_awarded.append({
                "code": badge["code"], "name": badge["name"],
                "description": badge["description"], "icon": badge["icon"],
                "earned_at": row.earned_at,
            })

        if newly_awarded:
            db.commit()
        return newly_awarded
