import logging
from typing import List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.classroom import ClassroomMember
from app.models.assignment import Assignment, AssignmentProblem
from app.models.submission import Submission, SubmissionStatus
from app.models.points import StudentPointsEvent, PointEventType

logger = logging.getLogger(__name__)

JUDGED_STATUSES = (
    SubmissionStatus.ACCEPTED,
    SubmissionStatus.WRONG_ANSWER,
    SubmissionStatus.RUNTIME_ERROR,
    SubmissionStatus.TIME_LIMIT_EXCEEDED,
)

class LeaderboardService:
    """
    Deterministic Leaderboard Ranking Engine for AI Code Classroom.

    RANKING RULES:
    1. Total Points DESC
    2. Problems Solved DESC
    3. Submission Accuracy DESC
    4. Student ID ASC (Tie-breaker)

    SCOPING:
    - points: StudentPointsEvent rows attributed to THIS classroom
      (scoring stamps classroom_id on every event; a submission that counts
      toward an open assignment here earns classroom-scoped events regardless
      of whether it was made through the assignment link or the problem
      browser - the same rule assignment-progress sync uses, so the
      leaderboard and the teacher's gradebook always agree).
    - problems_solved: ACCEPTED events in this classroom. The scoring dedupe
      guarantees exactly one ACCEPTED event per (student, problem, classroom),
      so this is a simple count.
    - accuracy / attempts / exec time: the student's judged submissions on
      problems assigned in this classroom. Work on problems never assigned
      here does not bleed in.
    """

    @staticmethod
    def get_classroom_leaderboard(db: Session, classroom_id: int) -> List[Dict[str, Any]]:
        member_ids = [
            row[0] for row in db.query(ClassroomMember.student_id).filter(
                ClassroomMember.classroom_id == classroom_id
            )
        ]
        if not member_ids:
            return []

        users = {
            u.id: u for u in db.query(User).filter(User.id.in_(member_ids))
        }

        # Problems assigned in this classroom (any non-draft assignment)
        classroom_problem_ids = {
            row[0] for row in db.query(AssignmentProblem.problem_id).join(
                Assignment, AssignmentProblem.assignment_id == Assignment.id
            ).filter(Assignment.classroom_id == classroom_id)
        }

        # Points + solved per student, from classroom-scoped events (one query each)
        points_by_student = dict(
            db.query(StudentPointsEvent.student_id, func.coalesce(func.sum(StudentPointsEvent.points), 0))
            .filter(
                StudentPointsEvent.classroom_id == classroom_id,
                StudentPointsEvent.student_id.in_(member_ids),
            ).group_by(StudentPointsEvent.student_id).all()
        )
        solved_by_student = dict(
            db.query(StudentPointsEvent.student_id, func.count(StudentPointsEvent.id))
            .filter(
                StudentPointsEvent.classroom_id == classroom_id,
                StudentPointsEvent.student_id.in_(member_ids),
                StudentPointsEvent.event_type == PointEventType.ACCEPTED,
            ).group_by(StudentPointsEvent.student_id).all()
        )

        # Judged submissions on this classroom's assigned problems, grouped per student
        subs_by_student: Dict[int, list] = {sid: [] for sid in member_ids}
        if classroom_problem_ids:
            classroom_subs = db.query(Submission).filter(
                Submission.user_id.in_(member_ids),
                Submission.problem_id.in_(classroom_problem_ids),
                Submission.status.in_(JUDGED_STATUSES),
            ).all()
            for s in classroom_subs:
                subs_by_student[s.user_id].append(s)

        entries = []
        for sid in member_ids:
            user = users.get(sid)
            if not user:
                continue

            submissions = subs_by_student.get(sid, [])
            total_submissions = len(submissions)
            accepted_submissions = sum(1 for s in submissions if s.status == SubmissionStatus.ACCEPTED)
            total_points = points_by_student.get(sid, 0)
            solved_count = solved_by_student.get(sid, 0)

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
                # Lets consumers tell "no data yet" (0 submissions) apart from
                # a genuine 0% accuracy; used by the struggling-students filter.
                "total_submissions": total_submissions,
            })

        # Sort according to deterministic ranking rules:
        # 1. points DESC, 2. problems_solved DESC, 3. accuracy DESC, 4. student_id ASC
        entries.sort(key=lambda x: (-x["points"], -x["problems_solved"], -x["accuracy"], x["student_id"]))

        # Assign ranks
        for idx, entry in enumerate(entries, start=1):
            entry["rank"] = idx

        return entries
