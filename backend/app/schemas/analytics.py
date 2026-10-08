from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class StudentOverviewSchema(BaseModel):
    points: int
    problems_attempted: int
    problems_solved: int
    problems_failed: int
    submission_accuracy: float
    problem_completion_rate: float
    total_submissions: int
    avg_attempts_per_solved: float
    avg_execution_time: float
    best_execution_time: Optional[float] = None
    rank_in_classroom: Optional[int] = None
    ai_hints_requested: int
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: Optional[str] = None  # YYYY-MM-DD
    level: int = 1
    level_title: str = "Novice"
    points_in_level: int = 0
    points_per_level: int = 200
    level_progress_pct: float = 0.0

class TopicAnalyticsSchema(BaseModel):
    topic: str
    attempted: int
    solved: int
    accuracy: float
    classification: str

class ClassTopicAnalyticsSchema(BaseModel):
    topic: str
    students_attempting: int
    avg_accuracy: float
    avg_attempts: float
    classification: str

class LeaderboardEntrySchema(BaseModel):
    rank: int
    student_id: int
    student_name: str
    points: int
    problems_solved: int
    accuracy: float
    avg_attempts: float
    avg_execution_time: float

class StudentAnalyticsResponse(BaseModel):
    overview: StudentOverviewSchema
    topics: List[TopicAnalyticsSchema]
    error_distribution: Dict[str, int]
    progress: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

class ClassroomAnalyticsOverview(BaseModel):
    total_students: int
    total_submissions: int
    problems_solved: int
    avg_class_score: float
    avg_class_accuracy: float

class ClassroomAnalyticsResponse(BaseModel):
    overview: ClassroomAnalyticsOverview
    topics: List[ClassTopicAnalyticsSchema]
    struggling_students: List[LeaderboardEntrySchema]
    leaderboard: List[LeaderboardEntrySchema]
