from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.feedback import ErrorCategory

class AIFeedbackContent(BaseModel):
    summary: str = Field(..., description="Brief 1-sentence summary of the evaluation")
    error_type: ErrorCategory = Field(default=ErrorCategory.LOGIC_ERROR, description="Category of error or feedback")
    explanation: str = Field(..., description="Socratic explanation of the issue or implementation")
    hint: str = Field(..., description="Progressive conceptual hint tailored to requested hint_level")
    next_step: str = Field(..., description="Actionable debugging question or exercise for student")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")

class AIFeedbackRequest(BaseModel):
    hint_level: int = Field(default=1, ge=1, le=3, description="Progressive hint level (1=conceptual, 2=directional, 3=specific)")

class RunFeedbackRequest(BaseModel):
    problem_id: int
    language: str
    source_code: str
    status: str = Field(..., description="The failing status from a Run result: WRONG_ANSWER, RUNTIME_ERROR, or TIME_LIMIT_EXCEEDED")
    hint_level: int = Field(default=1, ge=1, le=3, description="Progressive hint level (1=conceptual, 2=directional, 3=specific)")

class AIFeedbackResponse(BaseModel):
    id: Optional[int] = None
    submission_id: Optional[int] = None
    status: str
    hint_level: int
    feedback: AIFeedbackContent
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
