from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.assignment import AssignmentStatus, AssignmentProgressStatus

class AssignmentProblemCreate(BaseModel):
    problem_id: int
    points: int = 100
    order: int = 0

class AssignmentProblemResponse(BaseModel):
    id: int
    assignment_id: int
    problem_id: int
    points: int
    order: int
    title: Optional[str] = None
    difficulty: Optional[str] = None
    topic: Optional[str] = None
    solved: bool = False

    class Config:
        from_attributes = True

class AssignmentCreate(BaseModel):
    classroom_id: int
    title: str
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    problems: List[AssignmentProblemCreate] = []

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AssignmentStatus] = None
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    problems: Optional[List[AssignmentProblemCreate]] = None

class AssignmentStudentProgressResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    student_name: Optional[str] = None
    completed_problems: int
    total_problems: int
    score: int
    status: AssignmentProgressStatus
    last_activity_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentResponse(BaseModel):
    id: int
    classroom_id: int
    teacher_id: int
    title: str
    description: Optional[str] = None
    status: AssignmentStatus
    start_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    total_points: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    problems: List[AssignmentProblemResponse] = []
    my_progress: Optional[AssignmentStudentProgressResponse] = None
    student_progress_list: Optional[List[AssignmentStudentProgressResponse]] = None

    class Config:
        from_attributes = True
