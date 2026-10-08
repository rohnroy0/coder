from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.problem import Problem, TestCase, ProblemStatus
from app.models.user import User, UserRole
from app.schemas.problem import ProblemCreate, ProblemResponse, TestCaseCreate, TestCaseResponse
from app.schemas.ai import AIGenerateRequest, AIGenerateResponse
from app.dependencies.auth import get_current_user, get_current_teacher
from app.services.ai_service import AIService
from app.services.ollama_provider import AIServiceUnavailableException
from app.services.code_runner import SUPPORTED_LANGUAGES

router = APIRouter(
    prefix="/problems",
    tags=["Problems"]
)

@router.post("", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
def create_problem(
    problem_in: ProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    new_problem = Problem(
        title=problem_in.title,
        description=problem_in.description,
        difficulty=problem_in.difficulty,
        status=ProblemStatus.VERIFIED,  # Manually created by teacher -> VERIFIED
        topic=problem_in.topic,
        language=problem_in.language or "python",
        constraints=problem_in.constraints,
        input_format=problem_in.input_format,
        output_format=problem_in.output_format,
        examples=problem_in.examples,
        created_by=current_user.id
    )
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)
    return new_problem

@router.post("/generate", response_model=AIGenerateResponse, status_code=status.HTTP_200_OK)
def generate_ai_problems(
    request: AIGenerateRequest,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Teacher-only AI problem generation endpoint.
    Uses Ollama to generate structured programming problems and verifies them
    in Docker before returning verified previews.
    """
    if request.language.lower() not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
        )
    try:
        ai_service = AIService()
        return ai_service.generate_problems(db, current_teacher, request)
    except AIServiceUnavailableException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during AI generation: {str(e)}"
        )

@router.post("/{problem_id}/confirm", response_model=ProblemResponse)
def confirm_ai_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Teacher confirms/saves a previewed AI problem, setting status to VERIFIED (student-visible).
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_teacher.id:
        raise HTTPException(status_code=403, detail="Not authorized to confirm this problem")

    problem.status = ProblemStatus.VERIFIED
    db.commit()
    db.refresh(problem)
    problem.test_case_count = db.query(TestCase).filter(TestCase.problem_id == problem.id).count()
    return problem

@router.post("/{problem_id}/discard", status_code=status.HTTP_200_OK)
def discard_ai_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """
    Teacher discards an unconfirmed AI problem preview.
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_teacher.id:
        raise HTTPException(status_code=403, detail="Not authorized to discard this problem")

    db.delete(problem)
    db.commit()
    return {"message": "Problem discarded successfully"}

@router.get("", response_model=List[ProblemResponse])
def get_problems(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get problems list.
    Students ONLY see VERIFIED problems.
    Teachers can see all problems.
    """
    if current_user.role == UserRole.STUDENT:
        problems = db.query(Problem).filter(Problem.status == ProblemStatus.VERIFIED).all()
    else:
        problems = db.query(Problem).all()

    for p in problems:
        p.test_case_count = db.query(TestCase).filter(TestCase.problem_id == p.id).count()
    return problems

@router.get("/{problem_id}", response_model=ProblemResponse)
def get_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get problem detail.
    Students cannot access unverified/draft problems.
    Reference solution is never exposed to students.
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if current_user.role == UserRole.STUDENT and problem.status != ProblemStatus.VERIFIED:
        raise HTTPException(status_code=404, detail="Problem not found")

    problem.test_case_count = db.query(TestCase).filter(TestCase.problem_id == problem.id).count()
    return problem

@router.get("/{problem_id}/sample-testcases", response_model=List[TestCaseResponse])
def get_sample_testcases(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns up to the first 3 test cases for a problem as student-visible samples,
    so students can see worked examples and use "Run" to check their code before
    submitting. The remaining hidden test cases are never exposed here.
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if current_user.role == UserRole.STUDENT and problem.status != ProblemStatus.VERIFIED:
        raise HTTPException(status_code=404, detail="Problem not found")

    return (
        db.query(TestCase)
        .filter(TestCase.problem_id == problem.id)
        .order_by(TestCase.id)
        .limit(3)
        .all()
    )

@router.post("/{problem_id}/testcases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
def add_testcase(
    problem_id: int,
    testcase_in: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this problem")

    new_tc = TestCase(
        problem_id=problem.id,
        input=testcase_in.input,
        expected_output=testcase_in.expected_output
    )
    db.add(new_tc)
    db.commit()
    db.refresh(new_tc)
    return new_tc

@router.get("/{problem_id}/testcases", response_model=List[TestCaseResponse])
def get_testcases_for_teacher(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this problem's test cases")
    return db.query(TestCase).filter(TestCase.problem_id == problem.id).all()

@router.delete("/{problem_id}/testcases/{testcase_id}", status_code=status.HTTP_200_OK)
def delete_testcase(
    problem_id: int,
    testcase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this problem")

    tc = db.query(TestCase).filter(TestCase.id == testcase_id, TestCase.problem_id == problem_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.delete(tc)
    db.commit()
    return {"message": "Test case deleted successfully"}

@router.delete("/{problem_id}", status_code=status.HTTP_200_OK)
def delete_problem(
    problem_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this problem")
    db.delete(problem)
    db.commit()
    return {"message": "Problem deleted successfully"}
