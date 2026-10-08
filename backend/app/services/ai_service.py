import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.submission import Submission
from app.models.problem import Problem
from app.schemas.ai import AIGenerateRequest, AIGenerateResponse
from app.schemas.feedback import AIFeedbackResponse
from app.services.ai_provider import AIProvider, MockAIProvider
from app.services.question_generator import QuestionGenerator
from app.services.question_validator import QuestionValidator
from app.services.tutor_service import TutorService

logger = logging.getLogger(__name__)

class AIService:
    """
    Main AI Service Facade for AI Code Classroom.
    Provides entrypoints for AI problem generation, verification, and AI Tutor feedback.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        if provider is None and settings.AI_PROVIDER_TYPE == "mock":
            provider = MockAIProvider()
        self.generator = QuestionGenerator(provider=provider)
        self.tutor = TutorService(provider=provider)

    def generate_problems(
        self,
        db: Session,
        teacher: User,
        request: AIGenerateRequest
    ) -> AIGenerateResponse:
        """Generates and verifies AI coding problems for a teacher."""
        logger.info(f"[AIService] Teacher ID {teacher.id} requested AI problem generation for topic '{request.topic}'...")
        return self.generator.generate_and_verify_questions(db, teacher, request)

    def verify_problem(self, question_schema) -> bool:
        """Verifies a single question schema deterministically."""
        is_valid, _ = QuestionValidator.verify_reference_solution_in_docker(question_schema)
        return is_valid

    def generate_tutor_feedback(
        self,
        db: Session,
        submission: Submission,
        problem: Problem,
        student_id: int,
        hint_level: int = 1,
        attempt_number: int = 1
    ) -> AIFeedbackResponse:
        """Generates Socratic AI Tutor feedback for a student submission."""
        logger.info(f"[AIService] Student ID {student_id} requested AI Tutor feedback for submission {submission.id} (Hint Level {hint_level})...")
        return self.tutor.generate_feedback(db, submission, problem, student_id, hint_level, attempt_number)
