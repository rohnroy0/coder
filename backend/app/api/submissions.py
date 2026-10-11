import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus
from app.models.problem import Problem, ProblemStatus
from app.models.classroom import Classroom, ClassroomMember
from app.models.feedback import AIFeedback
from app.schemas.submission import SubmissionCreate, SubmissionResponse, SubmissionHistoryResponse, RunRequest, RunResponse
from app.schemas.feedback import AIFeedbackRequest, AIFeedbackResponse, AIFeedbackContent, RunFeedbackRequest
from app.dependencies.auth import get_current_user, get_current_student
from app.services.submission_service import SubmissionService
from app.services.code_runner import SandboxUnavailableError, SUPPORTED_LANGUAGES
from app.services.ai_service import AIService
from app.services.ollama_provider import AIServiceUnavailableException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"]
)


@router.post("", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_code(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Student submits code for a problem.
    Code is evaluated against all test cases via Docker execution.
    """
    return SubmissionService.create_submission(db, current_user, submission_in)


@router.post("/run", response_model=RunResponse, status_code=status.HTTP_200_OK)
def run_code_against_samples(
    run_in: RunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Student "Run" action: executes code against the problem's sample test cases
    only, without creating a submission or touching score/progress. Lets a
    student sanity-check their solution before using "Submit".
    """
    try:
        return SubmissionService.run_sample_tests(
            db, run_in.problem_id, run_in.language, run_in.source_code
        )
    except SandboxUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Code execution sandbox is unavailable. Ensure Docker is running and try again."
        )


@router.post("/run/feedback", response_model=AIFeedbackResponse, status_code=status.HTTP_200_OK)
def get_ai_tutor_feedback_for_run(
    request: RunFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Generate Socratic AI Tutor feedback for a failing "Run" result, before the
    student has used "Submit" at all. Like Run itself, nothing is persisted here -
    no submission is created and no feedback history is saved for it.
    """
    allowed_statuses = {
        SubmissionStatus.WRONG_ANSWER.value,
        SubmissionStatus.RUNTIME_ERROR.value,
        SubmissionStatus.TIME_LIMIT_EXCEEDED.value,
    }
    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"status must be one of {sorted(allowed_statuses)} - no hint is needed for a passing run."
        )

    if request.language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
        )

    problem = db.query(Problem).filter(Problem.id == request.problem_id).first()
    if not problem or problem.status != ProblemStatus.VERIFIED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    try:
        ai_service = AIService()
        return ai_service.generate_tutor_feedback_for_run(
            problem=problem,
            student_id=current_user.id,
            language=request.language,
            source_code=request.source_code,
            status_value=request.status,
            hint_level=request.hint_level
        )
    except AIServiceUnavailableException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Tutor is currently unavailable. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating AI feedback: {str(e)}"
        )


@router.get("/my", response_model=List[SubmissionHistoryResponse])
def get_my_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Returns the logged-in student's submission history.
    """
    return SubmissionService.get_student_submissions(db, current_user.id)


@router.post("/{submission_id}/feedback", response_model=AIFeedbackResponse, status_code=status.HTTP_200_OK)
def get_ai_tutor_feedback(
    submission_id: int,
    request: AIFeedbackRequest = AIFeedbackRequest(hint_level=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate Socratic AI Tutor feedback for a submission.
    - Students can only request feedback for their own submissions.
    - Teachers can request feedback for students in their classrooms.
    - Uses progressive hint levels (1=Conceptual, 2=Directional, 3=Targeted).
    - Enforces anti-solution validation and server-side security.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Authorization Check
    if current_user.role == UserRole.STUDENT:
        if submission.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only request AI feedback for your own submissions."
            )
    elif current_user.role == UserRole.TEACHER:
        # Check if student is in teacher's classroom OR problem created by teacher
        problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
        is_creator = problem and problem.created_by == current_user.id
        
        # Check classroom enrollment
        teacher_classroom_tuples = db.query(Classroom.id).filter(Classroom.teacher_id == current_user.id).all()
        teacher_classroom_ids = [c[0] for c in teacher_classroom_tuples]
        
        is_student_in_classroom = False
        if teacher_classroom_ids:
            is_student_in_classroom = db.query(ClassroomMember).filter(
                ClassroomMember.student_id == submission.user_id,
                ClassroomMember.classroom_id.in_(teacher_classroom_ids)
            ).first() is not None

        if not is_creator and not is_student_in_classroom:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view feedback for this submission."
            )

    if submission.status == SubmissionStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This submission was already accepted - no hint is needed for a correct solution."
        )

    problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated problem not found"
        )

    # Calculate attempt number for this student on this problem
    attempt_number = db.query(Submission).filter(
        Submission.user_id == submission.user_id,
        Submission.problem_id == submission.problem_id,
        Submission.created_at <= submission.created_at
    ).count()

    try:
        ai_service = AIService()
        return ai_service.generate_tutor_feedback(
            db=db,
            submission=submission,
            problem=problem,
            student_id=submission.user_id,
            hint_level=request.hint_level,
            attempt_number=attempt_number
        )
    except AIServiceUnavailableException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Tutor is currently unavailable. Please try again later."
        )
    except Exception as e:
        logger_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating AI feedback: {logger_msg}"
        )


@router.get("/{submission_id}/feedback", response_model=List[AIFeedbackResponse])
def get_submission_feedback_history(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve previous AI Tutor feedback history for a submission.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if current_user.role == UserRole.STUDENT and submission.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to another student's submission feedback")

    feedbacks = db.query(AIFeedback).filter(AIFeedback.submission_id == submission_id).order_by(AIFeedback.hint_level.asc()).all()
    
    result = []
    for f in feedbacks:
        result.append(AIFeedbackResponse(
            id=f.id,
            submission_id=f.submission_id,
            status=submission.status.value,
            hint_level=f.hint_level,
            feedback=AIFeedbackContent(
                summary=f.summary,
                error_type=f.error_type,
                explanation=f.explanation,
                hint=f.hint,
                next_step=f.next_step,
                confidence=f.confidence
            ),
            created_at=f.created_at
        ))
    return result
