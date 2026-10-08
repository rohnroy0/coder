import logging
from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.classroom import ClassroomMember
from app.models.assignment import Assignment
from app.models.submission import Submission, SubmissionStatus
from app.models.points import StudentPointsEvent

logger = logging.getLogger(__name__)

class LeaderboardService:
    """
    Deterministic Leaderboard Ranking Engine for AI Code Classroom.

    RANKING RULES:
    1. Total Points DESC
    2. Problems Solved DESC
    3. Submission Accuracy DESC
    4. Student ID ASC (Tie-breaker)

    All per-student stats are scoped to submissions made under THIS classroom's
    assignments. Problems are shared across classrooms, so a student's practice
    submissions and other classrooms' work must not bleed into this leaderboard.
    """

    @staticmethod
    def get_classroom_leaderboard(db: Session, classroom_id: int) -> List[Dict[str, Any]]:
        # Fetch all enrolled students in the classroom
        members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom_id).all()
        student_ids = [m.student_id for m in members]

        if not student_ids:
            return []

        assignment_ids = [a.id for a in db.query(Assignment.id).filter(Assignment.classroom_id == classroom_id)]

        entries = []

        for sid in student_ids:
            user = db.query(User).filter(User.id == sid).first()
            if not user:
                continue

            if not assignment_ids:
                total_points = 0
                solved_count = 0
                submissions = []
            else:
                # Calculate total points earned from submissions under this classroom's assignments
                total_points = db.query(func.coalesce(func.sum(StudentPointsEvent.points), 0)).join(
                    Submission, StudentPointsEvent.submission_id == Submission.id
                ).filter(
                    StudentPointsEvent.student_id == sid,
                    Submission.assignment_id.in_(assignment_ids)
                ).scalar()

                # Calculate problems solved (distinct problems with ACCEPTED submission) in this classroom
                solved_count = db.query(func.count(func.distinct(Submission.problem_id))).filter(
                    Submission.user_id == sid,
                    Submission.status == SubmissionStatus.ACCEPTED,
                    Submission.assignment_id.in_(assignment_ids)
                ).scalar() or 0

                # Calculate submission statistics scoped to this classroom
                submissions = db.query(Submission).filter(
                    Submission.user_id == sid,
                    Submission.assignment_id.in_(assignment_ids),
                    Submission.status.in_([
                        SubmissionStatus.ACCEPTED,
                        SubmissionStatus.WRONG_ANSWER,
                        SubmissionStatus.RUNTIME_ERROR,
                        SubmissionStatus.TIME_LIMIT_EXCEEDED
                    ])
                ).all()

            total_submissions = len(submissions)
            accepted_submissions = sum(1 for s in submissions if s.status == SubmissionStatus.ACCEPTED)

            # Submission Accuracy (%)
            accuracy = round((accepted_submissions / total_submissions * 100.0), 1) if total_submissions > 0 else 0.0

            # Average attempts per solved problem
            attempts_per_solved = 0.0
            if solved_count > 0:
                attempts_per_solved = round(total_submissions / solved_count, 1)

            # Average execution time
            exec_times = [s.execution_time for s in submissions if s.execution_time is not None]
            avg_exec_time = round(sum(exec_times) / len(exec_times), 3) if exec_times else 0.0

            entries.append({
                "student_id": user.id,
                "student_name": user.name,
                "points": int(total_points),
                "problems_solved": int(solved_count),
                "accuracy": accuracy,
                "avg_attempts": attempts_per_solved,
                "avg_execution_time": avg_exec_time,
            })

        # Sort according to deterministic ranking rules:
        # 1. points DESC, 2. problems_solved DESC, 3. accuracy DESC, 4. student_id ASC
        entries.sort(key=lambda x: (-x["points"], -x["problems_solved"], -x["accuracy"], x["student_id"]))

        # Assign ranks
        for idx, entry in enumerate(entries, start=1):
            entry["rank"] = idx

        return entries
