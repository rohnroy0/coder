from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.submission import SubmissionStatus
from app.schemas.badge import EarnedBadge

class RunRequest(BaseModel):
    problem_id: int
    language: str
    source_code: str

class RunTestCaseResult(BaseModel):
    input: str
    expected_output: str
    actual_output: Optional[str] = None
    passed: bool
    status: str  # PASSED | WRONG_ANSWER | RUNTIME_ERROR | TIME_LIMIT_EXCEEDED
    error_message: Optional[str] = None

class RunResponse(BaseModel):
    results: List[RunTestCaseResult]
    all_passed: bool

class SubmissionCreate(BaseModel):
    problem_id: int
    language: str
    source_code: str
    assignment_id: Optional[int] = None

class SubmissionResponse(BaseModel):
    id: int
    user_id: int
    problem_id: int
    language: str
    source_code: str
    status: SubmissionStatus
    execution_time: Optional[float] = None
    assignment_id: Optional[int] = None
    created_at: datetime
    # Evaluation details, only present on the response to a new submission
    failed_test_case: Optional[int] = None  # 1-based number of the first failing test
    total_test_cases: Optional[int] = None
    error_message: Optional[str] = None  # tail of the traceback for runtime errors
    newly_earned_badges: List[EarnedBadge] = []  # badges unlocked by this submission, if any

    class Config:
        from_attributes = True

class SubmissionHistoryResponse(BaseModel):
    id: int
    problem: str
    language: str
    status: SubmissionStatus
    created_at: datetime
    source_code: Optional[str] = None
    execution_time: Optional[float] = None
    
    class Config:
        from_attributes = True

