"""
Teacher-facing Student Performance Profile schemas.

These response models are deliberately explicit: only the fields listed here are
serialised, so hidden test cases, reference solutions and AI tutor conversation
text can never leak through the profile endpoints. Source code is only exposed by
the single-submission endpoint (SubmissionCodeResponse).
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class RosterEntry(BaseModel):
    student_id: int
    name: str
    email: str
    joined_at: datetime
    rank: int
    points: int
    problems_solved: int
    accuracy: float
    progress: Optional[float] = None  # % of assignment problems completed; None if no assignments


class ProfileHeader(BaseModel):
    student_id: int
    name: str
    email: str
    classroom_id: int
    classroom_name: str
    joined_at: datetime
    rank: Optional[int] = None
    total_students: int
    total_points: int


class OverallPerformance(BaseModel):
    total_points: int
    problems_solved: int
    problems_attempted: int
    submission_accuracy: float
    completion_rate: float
    avg_attempts: float
    avg_execution_time: float
    total_submissions: int
    assignments_completed: int
    assignments_total: int


class AssignmentProblemDetail(BaseModel):
    problem_id: int
    title: str
    points: int
    attempts: int
    best_result: Optional[str] = None
    solved: bool


class AssignmentPerformance(BaseModel):
    assignment_id: int
    title: str
    assignment_status: str
    progress_status: str
    completed_problems: int
    total_problems: int
    score: int
    max_score: int
    percentage: float
    attempts: int
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    problems: List[AssignmentProblemDetail] = []


class ProblemPerformance(BaseModel):
    problem_id: int
    title: str
    topic: str
    difficulty: str
    assignments: List[str] = []
    attempts: int
    first_result: str
    latest_result: str
    best_result: str
    best_execution_time: Optional[float] = None
    last_submission_at: datetime
    hints_requested: int
    completion_status: str  # "Solved" | "Attempted"


class SubmissionRow(BaseModel):
    submission_id: int
    created_at: datetime
    problem_id: int
    problem: str
    assignment: Optional[str] = None
    language: str
    result: str
    execution_time: Optional[float] = None
    memory_used_mb: Optional[float] = None  # not measured by the sandbox; always None today
    attempt_number: int


class CountItem(BaseModel):
    name: str
    count: int


class HintProgression(BaseModel):
    problem: str
    levels: List[int]  # hint levels requested, in chronological order
    max_level: int


class AITutorActivity(BaseModel):
    total_hints: int
    hints_by_problem: List[CountItem]
    categories: List[CountItem]
    most_common_error: Optional[str] = None
    progression: List[HintProgression]


class ErrorCategoryStat(BaseModel):
    category: str
    count: int
    percentage: float
    topics: List[str]


class ErrorAnalysis(BaseModel):
    ai_categories: List[ErrorCategoryStat]  # from AI tutor classifications
    judge_outcomes: List[CountItem]  # non-accepted judge verdicts (objective)


class TopicMastery(BaseModel):
    topic: str
    attempted: int
    solved: int
    accuracy: float
    classification: str


class TrendPoint(BaseModel):
    date: str  # YYYY-MM-DD
    points: int  # cumulative points at end of day
    problems_solved: int  # cumulative distinct problems solved
    accuracy: float  # cumulative submission accuracy (%)
    daily_accuracy: float  # accuracy of that day's submissions (%)


class LeaderboardInfo(BaseModel):
    rank: Optional[int] = None
    total_students: int
    points: int
    problems_solved: int
    accuracy: float


class PointHistoryItem(BaseModel):
    id: int
    created_at: datetime
    event_type: str
    reason: str
    problem: Optional[str] = None
    points: int
    running_total: int


class ActivityItem(BaseModel):
    type: str  # JOINED | SUBMITTED | ACCEPTED | WRONG_ANSWER | RUNTIME_ERROR | TIME_LIMIT_EXCEEDED | HINT | ASSIGNMENT_STARTED | ASSIGNMENT_COMPLETED
    description: str
    created_at: datetime
    points: Optional[int] = None


class PerformanceSummary(BaseModel):
    lines: List[str]
    strong_topics: List[str]
    developing_topics: List[str]
    needs_practice_topics: List[str]
    most_common_error: Optional[str] = None


class StudentProfileResponse(BaseModel):
    header: ProfileHeader
    summary: PerformanceSummary
    overall: OverallPerformance
    leaderboard: LeaderboardInfo
    assignments: List[AssignmentPerformance]
    problems: List[ProblemPerformance]
    submissions: List[SubmissionRow]
    ai_tutor: AITutorActivity
    errors: ErrorAnalysis
    topics: List[TopicMastery]
    trends: List[TrendPoint]
    points_history: List[PointHistoryItem]
    recent_activity: List[ActivityItem]
    limitations: List[str]


class SubmissionCodeResponse(BaseModel):
    submission_id: int
    student_id: int
    problem: str
    assignment: Optional[str] = None
    language: str
    result: str
    execution_time: Optional[float] = None
    created_at: datetime
    attempt_number: int
    source_code: str
