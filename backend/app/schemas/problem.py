from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.problem import ProblemDifficulty, ProblemStatus

class TestCaseCreate(BaseModel):
    input: str
    expected_output: str

class TestCaseResponse(BaseModel):
    id: int
    problem_id: int
    input: str
    expected_output: str
    
    class Config:
        from_attributes = True

class ProblemCreate(BaseModel):
    title: str
    description: str
    difficulty: ProblemDifficulty
    topic: Optional[str] = None
    language: Optional[str] = "python"
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[str] = None

class ProblemResponse(BaseModel):
    id: int
    title: str
    description: str
    difficulty: ProblemDifficulty
    status: ProblemStatus = ProblemStatus.VERIFIED
    topic: Optional[str] = None
    language: Optional[str] = "python"
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[str] = None
    created_by: int
    created_at: datetime
    test_case_count: int = 0
    
    class Config:
        from_attributes = True
