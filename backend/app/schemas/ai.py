from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from app.models.problem import ProblemDifficulty, ProblemStatus

class AIGenerateRequest(BaseModel):
    language: str = Field("python", description="Programming language: 'python', 'c', or 'cpp'")
    difficulty: ProblemDifficulty = Field(ProblemDifficulty.EASY, description="EASY, MEDIUM, or HARD")
    topic: str = Field(..., description="Programming concept/topic (e.g., recursion, dynamic programming)")
    count: int = Field(1, ge=1, le=5, description="Number of questions to generate (1-5)")

class AIGeneratedExampleSchema(BaseModel):
    input: str
    output: str

class AIGeneratedTestCaseSchema(BaseModel):
    input: str
    expected_output: str

class AIGeneratedQuestionSchema(BaseModel):
    title: str
    description: str
    difficulty: ProblemDifficulty
    language: str
    topic: str
    constraints: List[str] = Field(default_factory=list)
    input_format: str
    output_format: str
    examples: List[AIGeneratedExampleSchema] = Field(default_factory=list)
    test_cases: List[AIGeneratedTestCaseSchema] = Field(default_factory=list)
    reference_solution: str

class AIGeneratedQuestionListSchema(BaseModel):
    questions: List[AIGeneratedQuestionSchema]

class AIGeneratedQuestionPreview(BaseModel):
    id: Optional[int] = None
    title: str
    description: str
    difficulty: ProblemDifficulty
    status: ProblemStatus
    language: str
    topic: str
    constraints: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    examples: Optional[str] = None
    test_case_count: int = 0
    verification_message: str = "Verified: Reference solution passed all generated test cases."

class AIGenerateResponse(BaseModel):
    generated: int
    verified: int
    failed: int
    questions: List[AIGeneratedQuestionPreview]
    failure_reasons: List[str] = []  # why attempts were rejected (teacher-only endpoint)
