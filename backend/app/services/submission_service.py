import time
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.problem import Problem, ProblemStatus, TestCase
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.submission import SubmissionCreate, RunResponse, RunTestCaseResult
from app.services.code_runner import run_code, SandboxUnavailableError, SUPPORTED_LANGUAGES
from app.services.scoring_service import ScoringService
from app.services.badge_service import BadgeService

# "Run" only ever checks the student against this many sample test cases, so the
# remaining hidden test cases stay hidden until the real "Submit".
SAMPLE_TEST_CASE_LIMIT = 3


class SubmissionService:

    @staticmethod
    def run_sample_tests(
        db: Session, problem_id: int, language: str, source_code: str
    ) -> RunResponse:
        """
        Runs source_code against the first few (sample) test cases of a problem and
        returns per-test-case actual output. Unlike create_submission, nothing is
        persisted - this lets a student sanity-check their code before submitting.
        """
        problem = db.query(Problem).filter(Problem.id == problem_id).first()
        if not problem or problem.status != ProblemStatus.VERIFIED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        language = language.lower()
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
            )

        test_cases = (
            db.query(TestCase)
            .filter(TestCase.problem_id == problem.id)
            .order_by(TestCase.id)
            .limit(SAMPLE_TEST_CASE_LIMIT)
            .all()
        )

        results = []
        for tc in test_cases:
            stdout, stderr, return_code, is_timeout = run_code(language, source_code, tc.input)

            if is_timeout:
                results.append(RunTestCaseResult(
                    input=tc.input, expected_output=tc.expected_output,
                    actual_output=None, passed=False,
                    status="TIME_LIMIT_EXCEEDED", error_message=None,
                ))
                continue

            if return_code != 0:
                results.append(RunTestCaseResult(
                    input=tc.input, expected_output=tc.expected_output,
                    actual_output=stdout.strip() or None, passed=False,
                    status="RUNTIME_ERROR", error_message=SubmissionService._format_error(stderr),
                ))
                continue

            actual = "\n".join(line.rstrip() for line in stdout.strip().splitlines())
            expected = "\n".join(line.rstrip() for line in tc.expected_output.strip().splitlines())
            passed = actual == expected
            results.append(RunTestCaseResult(
                input=tc.input, expected_output=tc.expected_output,
                actual_output=stdout.strip(), passed=passed,
                status="PASSED" if passed else "WRONG_ANSWER", error_message=None,
            ))

        return RunResponse(results=results, all_passed=all(r.passed for r in results))

    @staticmethod
    def _evaluate(
        source_code: str, test_cases: List[TestCase], language: str
    ) -> Tuple[SubmissionStatus, float]:
        """
        Run source_code against all test cases and return (status, total_execution_time).
        """
        status, total_time, _, _ = SubmissionService._evaluate_detailed(source_code, test_cases, language)
        return status, total_time

    @staticmethod
    def _evaluate_detailed(
        source_code: str, test_cases: List[TestCase], language: str
    ) -> Tuple[SubmissionStatus, float, Optional[int], Optional[str]]:
        """
        Run source_code against all test cases and return
        (status, total_execution_time, failed_test_case_number, error_message).
        The failed test number is 1-based. Expected outputs are never included, so
        hidden test cases stay hidden.
        """
        if not test_cases:
            return SubmissionStatus.ACCEPTED, 0.0, None, None

        total_time = 0.0

        for number, tc in enumerate(test_cases, start=1):
            start = time.monotonic()
            stdout, stderr, return_code, is_timeout = run_code(language, source_code, tc.input)
            elapsed = time.monotonic() - start
            total_time += elapsed

            if is_timeout:
                return SubmissionStatus.TIME_LIMIT_EXCEEDED, total_time, number, None

            if return_code != 0:
                # Only echo stderr for the sample (publicly visible) test cases.
                # The student's program controls its own stderr, so echoing it for
                # hidden tests lets code like `raise Exception(sys.stdin.read())`
                # exfiltrate every hidden test input one submission at a time.
                if number <= SAMPLE_TEST_CASE_LIMIT:
                    error = SubmissionService._format_error(stderr)
                else:
                    error = "Runtime error on a hidden test case (details are hidden)."
                return SubmissionStatus.RUNTIME_ERROR, total_time, number, error

            # Normalize output: strip trailing whitespace/newlines per line
            actual = "\n".join(line.rstrip() for line in stdout.strip().splitlines())
            expected = "\n".join(line.rstrip() for line in tc.expected_output.strip().splitlines())

            if actual != expected:
                return SubmissionStatus.WRONG_ANSWER, total_time, number, None

        return SubmissionStatus.ACCEPTED, total_time, None, None

    @staticmethod
    def _format_error(stderr: str, max_lines: int = 15, max_chars: int = 2000) -> Optional[str]:
        """Keep the tail of the traceback (where the actual exception is) and cap its size."""
        lines = stderr.strip().splitlines()
        if not lines:
            return None
        return "\n".join(lines[-max_lines:])[-max_chars:]

    @staticmethod
    def create_submission(
        db: Session,
        student: User,
        schema: SubmissionCreate
    ) -> Submission:
        problem = db.query(Problem).filter(Problem.id == schema.problem_id).first()
        # Unverified (draft/preview/failed) problems are invisible to students
        # everywhere else; accepting submissions against them would let a student
        # farm points off a teacher's unpublished drafts by guessing IDs.
        if not problem or problem.status != ProblemStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem not found"
            )

        language = schema.language.lower()
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
            )

        # A problem with no test cases can't be judged - without this guard,
        # _evaluate_detailed's loop simply never runs and its correctness-rank
        # fallthrough silently reports ACCEPTED for any submission, including
        # empty code. Fail the request instead of fabricating a grade.
        test_cases = (
            db.query(TestCase)
            .filter(TestCase.problem_id == problem.id)
            .order_by(TestCase.id)
            .all()
        )
        if not test_cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This problem has no test cases configured yet and cannot be judged. Please contact your teacher."
            )

        if schema.assignment_id:
            from app.models.assignment import Assignment, AssignmentProblem
            from app.models.classroom import ClassroomMember
            from app.services.deadline_service import DeadlineService
            assignment = db.query(Assignment).filter(Assignment.id == schema.assignment_id).first()
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            # assignment_id is client-supplied: without these two checks a student
            # can attach the submission to any published assignment on the platform,
            # earning per-classroom points again and injecting themselves into
            # other teachers' progress dashboards.
            is_member = db.query(ClassroomMember).filter(
                ClassroomMember.classroom_id == assignment.classroom_id,
                ClassroomMember.student_id == student.id
            ).first() is not None
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not enrolled in this assignment's classroom."
                )
            problem_in_assignment = db.query(AssignmentProblem).filter(
                AssignmentProblem.assignment_id == assignment.id,
                AssignmentProblem.problem_id == problem.id
            ).first() is not None
            if not problem_in_assignment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This problem is not part of the given assignment."
                )
            DeadlineService.check_submission_allowed(assignment)

        # Create PENDING record
        submission = Submission(
            user_id=student.id,
            problem_id=problem.id,
            language=language,
            source_code=schema.source_code,
            status=SubmissionStatus.PENDING,
            assignment_id=schema.assignment_id,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

        # Update to RUNNING
        submission.status = SubmissionStatus.RUNNING
        db.commit()

        # Evaluate. If the sandbox is down, drop the record rather than penalising the student.
        try:
            result_status, exec_time, failed_test_case, error_message = \
                SubmissionService._evaluate_detailed(schema.source_code, test_cases, language)
        except SandboxUnavailableError:
            db.delete(submission)
            db.commit()
            raise

        submission.status = result_status
        submission.execution_time = round(exec_time, 4)
        db.commit()
        db.refresh(submission)

        # Phase 6: Trigger Scoring Service to compute points & events
        ScoringService.process_submission_scoring(db, submission, problem)

        # Phase 7: Sync Assignment Progress. Beyond the assignment this submission
        # was explicitly made under (if any), also sync every other assignment in
        # one of the student's classrooms that contains this same problem -
        # problems are shared/reusable across assignments, so solving one must
        # count everywhere it's assigned, not only when reached through that
        # specific assignment's link.
        #
        # Only assignments that are currently OPEN are synced. Syncing closed or
        # overdue assignments would let a student bypass the deadline entirely:
        # solve the problem from the general browser after the due date and the
        # closed assignment's gradebook entry silently flips to COMPLETED.
        from app.services.assignment_service import AssignmentService
        assignment_ids_to_sync = AssignmentService.find_student_assignments_for_problem(
            db, student.id, problem.id, open_only=True
        )
        if schema.assignment_id:
            # Already validated above: student is enrolled, problem belongs to
            # it, and the deadline check passed.
            assignment_ids_to_sync.add(schema.assignment_id)
        for aid in assignment_ids_to_sync:
            AssignmentService.sync_student_progress_on_submission(
                db=db,
                assignment_id=aid,
                student_id=student.id,
                problem_id=problem.id,
                submission_status=submission.status
            )

        # Gamification: check for newly-unlocked badges after scoring/progress are up to date
        newly_earned_badges = BadgeService.evaluate_and_award(db, student.id)

        # Evaluation details for the response only (not persisted)
        submission.failed_test_case = failed_test_case
        submission.total_test_cases = len(test_cases)
        submission.error_message = error_message
        submission.newly_earned_badges = newly_earned_badges
        return submission

    @staticmethod
    def get_student_submissions(db: Session, student_id: int) -> List[dict]:
        submissions = (
            db.query(Submission)
            .filter(Submission.user_id == student_id)
            .order_by(Submission.created_at.desc())
            .all()
        )
        result = []
        for sub in submissions:
            problem = db.query(Problem).filter(Problem.id == sub.problem_id).first()
            result.append({
                "id": sub.id,
                "problem": problem.title if problem else "Unknown",
                "language": sub.language,
                "status": sub.status,
                "created_at": sub.created_at,
                "source_code": sub.source_code,
                "execution_time": sub.execution_time,
            })
        return result
