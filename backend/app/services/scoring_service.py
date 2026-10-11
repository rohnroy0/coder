import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.submission import Submission, SubmissionStatus
from app.models.problem import Problem
from app.models.assignment import Assignment
from app.models.points import StudentPointsEvent, PointEventType

logger = logging.getLogger(__name__)

class ScoringService:
    """
    Transparent Point & Reward System for AI Code Classroom.
    Calculates points, bonuses, and penalties according to configurable rules.
    Prevents point farming by ensuring base problem rewards are awarded once.
    """

    @staticmethod
    def process_submission_scoring(
        db: Session,
        submission: Submission,
        problem: Problem
    ) -> List[StudentPointsEvent]:
        """
        Evaluates submission judge result and records StudentPointsEvent entries.
        """
        student_id = submission.user_id
        problem_id = problem.id

        # The classroom this submission counts toward, if any - derived from the
        # assignment it was submitted under, not an arbitrary classroom the student
        # happens to belong to (a student can be enrolled in several classrooms).
        classroom_id = None
        if submission.assignment_id:
            assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
            classroom_id = assignment.classroom_id if assignment else None

        # Calculate student's total attempt count on this problem up to this submission
        attempt_number = db.query(Submission).filter(
            Submission.user_id == student_id,
            Submission.problem_id == problem_id,
            Submission.created_at <= submission.created_at
        ).count()

        events_created: List[StudentPointsEvent] = []

        if submission.status == SubmissionStatus.ACCEPTED:
            # Check if base ACCEPTED points were already awarded for this problem
            # *within this same classroom* (or, for classroom_id None, within
            # practice submissions). Scoped per classroom_id - not globally per
            # problem - so that a problem reused across several classrooms (or
            # solved once in practice and later through an assignment) still
            # earns points the first time it's solved in each classroom, which
            # keeps this in sync with the leaderboard's per-classroom solved count.
            already_solved = db.query(StudentPointsEvent).filter(
                StudentPointsEvent.student_id == student_id,
                StudentPointsEvent.submission_id != submission.id,
                StudentPointsEvent.event_type == PointEventType.ACCEPTED,
                StudentPointsEvent.classroom_id == classroom_id
            ).join(Submission, StudentPointsEvent.submission_id == Submission.id).filter(
                Submission.problem_id == problem_id
            ).first() is not None

            if not already_solved:
                # Base Accepted Reward
                ev_accepted = StudentPointsEvent(
                    student_id=student_id,
                    classroom_id=classroom_id,
                    submission_id=submission.id,
                    event_type=PointEventType.ACCEPTED,
                    points=settings.POINTS_ACCEPTED,
                    description=f"Solved problem '{problem.title}'"
                )
                db.add(ev_accepted)
                events_created.append(ev_accepted)

                # Fast Execution Bonus
                if submission.execution_time is not None and submission.execution_time <= settings.FAST_EXECUTION_THRESHOLD:
                    ev_fast = StudentPointsEvent(
                        student_id=student_id,
                        classroom_id=classroom_id,
                        submission_id=submission.id,
                        event_type=PointEventType.FAST_BONUS,
                        points=settings.POINTS_FAST_BONUS,
                        description=f"Fast execution bonus ({round(submission.execution_time, 3)}s)"
                    )
                    db.add(ev_fast)
                    events_created.append(ev_fast)

                # First Attempt Quality Bonus
                if attempt_number == 1:
                    ev_clean = StudentPointsEvent(
                        student_id=student_id,
                        classroom_id=classroom_id,
                        submission_id=submission.id,
                        event_type=PointEventType.QUALITY_BONUS,
                        points=settings.POINTS_CLEAN_BONUS,
                        description="First attempt clean solution bonus"
                    )
                    db.add(ev_clean)
                    events_created.append(ev_clean)

        elif submission.status in (SubmissionStatus.WRONG_ANSWER, SubmissionStatus.RUNTIME_ERROR, SubmissionStatus.TIME_LIMIT_EXCEEDED):
            # Count penalties already applied for this student on this problem,
            # scoped per classroom_id for the same reason as already_solved above.
            penalty_types = [PointEventType.WRONG_ANSWER, PointEventType.RUNTIME_ERROR, PointEventType.TIME_LIMIT_EXCEEDED]
            penalty_count = db.query(StudentPointsEvent).join(
                Submission, StudentPointsEvent.submission_id == Submission.id
            ).filter(
                StudentPointsEvent.student_id == student_id,
                Submission.problem_id == problem_id,
                StudentPointsEvent.event_type.in_(penalty_types),
                StudentPointsEvent.classroom_id == classroom_id
            ).count()

            if penalty_count < settings.MAX_PENALTY_EVENTS_PER_PROBLEM:
                if submission.status == SubmissionStatus.WRONG_ANSWER:
                    ev_pen = StudentPointsEvent(
                        student_id=student_id,
                        classroom_id=classroom_id,
                        submission_id=submission.id,
                        event_type=PointEventType.WRONG_ANSWER,
                        points=settings.POINTS_WRONG,
                        description=f"Wrong answer penalty on '{problem.title}'"
                    )
                elif submission.status == SubmissionStatus.RUNTIME_ERROR:
                    ev_pen = StudentPointsEvent(
                        student_id=student_id,
                        classroom_id=classroom_id,
                        submission_id=submission.id,
                        event_type=PointEventType.RUNTIME_ERROR,
                        points=settings.POINTS_RUNTIME_ERROR,
                        description=f"Runtime error penalty on '{problem.title}'"
                    )
                else:
                    ev_pen = StudentPointsEvent(
                        student_id=student_id,
                        classroom_id=classroom_id,
                        submission_id=submission.id,
                        event_type=PointEventType.TIME_LIMIT_EXCEEDED,
                        points=settings.POINTS_TIMEOUT,
                        description=f"Time limit exceeded penalty on '{problem.title}'"
                    )

                db.add(ev_pen)
                events_created.append(ev_pen)

        db.commit()
        return events_created
