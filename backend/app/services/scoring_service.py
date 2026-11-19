import logging
import threading
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.submission import Submission, SubmissionStatus
from app.models.problem import Problem, TestCase
from app.models.assignment import Assignment
from app.models.points import StudentPointsEvent, PointEventType
from app.models.user import User

logger = logging.getLogger(__name__)

# Scoring is check-then-insert (already_solved / penalty_count), and evaluation
# takes seconds, so two concurrent submissions of the same solve would both pass
# the check and both award points. This lock serializes the check+insert+commit
# critical section within the process; the with_for_update() row lock below
# covers multi-worker PostgreSQL deployments (it is a no-op on SQLite, where
# this single-process lock is the effective guard).
_scoring_lock = threading.Lock()

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
        with _scoring_lock:
            return ScoringService._process_submission_scoring_locked(db, submission, problem)

    @staticmethod
    def _process_submission_scoring_locked(
        db: Session,
        submission: Submission,
        problem: Problem
    ) -> List[StudentPointsEvent]:
        student_id = submission.user_id
        problem_id = problem.id

        # Serialize concurrent scoring for the same student across processes.
        db.query(User).filter(User.id == student_id).with_for_update().first()

        # The classrooms this submission counts toward: the classroom of every
        # OPEN assignment (in the student's classrooms) that contains this
        # problem - the same rule assignment-progress sync uses. Deriving this
        # only from submission.assignment_id made the gradebook and leaderboard
        # disagree: a student who solved an assignment problem from the general
        # problem browser was marked COMPLETED in the teacher's gradebook but
        # earned no classroom points, so the leaderboard showed 0. No open
        # assignment -> practice (classroom None). The per-classroom
        # already_solved dedupe below still guarantees at most one ACCEPTED
        # award per (problem, classroom).
        from app.services.assignment_service import AssignmentService
        relevant_assignment_ids = AssignmentService.find_student_assignments_for_problem(
            db, student_id, problem_id, open_only=True
        )
        if submission.assignment_id:
            # Validated at submission time: enrolled, problem in assignment, open.
            relevant_assignment_ids.add(submission.assignment_id)
        if relevant_assignment_ids:
            target_classroom_ids = sorted({
                row[0] for row in db.query(Assignment.classroom_id).filter(
                    Assignment.id.in_(relevant_assignment_ids)
                )
            })
        else:
            target_classroom_ids = [None]

        # Calculate student's total attempt count on this problem up to this submission
        attempt_number = db.query(Submission).filter(
            Submission.user_id == student_id,
            Submission.problem_id == problem_id,
            Submission.created_at <= submission.created_at
        ).count()

        events_created: List[StudentPointsEvent] = []
        for classroom_id in target_classroom_ids:
            events_created.extend(ScoringService._score_for_classroom(
                db, submission, problem, classroom_id, attempt_number
            ))

        db.commit()
        return events_created

    @staticmethod
    def _score_for_classroom(
        db: Session,
        submission: Submission,
        problem: Problem,
        classroom_id: Optional[int],
        attempt_number: int
    ) -> List[StudentPointsEvent]:
        """Award/penalize this submission within ONE classroom scope (or
        practice when classroom_id is None). Adds events to the session;
        the caller commits."""
        student_id = submission.user_id
        problem_id = problem.id
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

                # Fast Execution Bonus. execution_time is the TOTAL measured
                # in-container program runtime across all test cases, so the
                # threshold is compared against the per-test average - a
                # problem with more test cases must not be harder to earn the
                # bonus on than one with fewer.
                if submission.execution_time is not None:
                    test_count = db.query(TestCase).filter(TestCase.problem_id == problem_id).count()
                    avg_time = submission.execution_time / max(test_count, 1)
                    if avg_time <= settings.FAST_EXECUTION_THRESHOLD:
                        ev_fast = StudentPointsEvent(
                            student_id=student_id,
                            classroom_id=classroom_id,
                            submission_id=submission.id,
                            event_type=PointEventType.FAST_BONUS,
                            points=settings.POINTS_FAST_BONUS,
                            description=f"Fast execution bonus (avg {round(avg_time, 3)}s per test)"
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

        return events_created
