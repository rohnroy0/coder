import json
import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.problem import Problem, TestCase, ProblemDifficulty, ProblemStatus
from app.models.user import User
from app.schemas.ai import (
    AIGenerateRequest,
    AIGeneratedQuestionSchema,
    AIGeneratedQuestionListSchema,
    AIGeneratedQuestionPreview,
    AIGenerateResponse
)
from app.services.ai_provider import AIProvider, MockAIProvider
from app.services.ollama_provider import OllamaProvider, AIServiceUnavailableException
from app.services.question_validator import QuestionValidator

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert Computer Science educator and competitive programming author.
Your task is to generate high-quality, original coding problems for students in strict JSON format.

RULES:
1. Output MUST be valid JSON only. Do NOT wrap output in markdown code blocks like ```json ... ```. Do NOT include introductory or concluding text.
2. The problem MUST strictly match the requested programming language, difficulty, and topic.
3. Provide an unambiguous problem description, input format, output format, and realistic constraints.
4. Include at least 1 public example and at least 2 hidden test cases with correct expected outputs.
5. CRITICAL - "reference_solution" MUST be a COMPLETE, STANDALONE, EXECUTABLE PROGRAM, never just a bare
   function definition. It MUST explicitly read every input value from standard input AND explicitly
   print the final answer to standard output. A solution that defines a function (e.g.
   `def factorial(n): ...` or `int factorial(int n) { ... }`) but never calls it, never reads input, or
   never prints a result produces NO output when actually run, and will be automatically rejected.
   - Python: read with input() or sys.stdin, then call print(...) with the final answer. You may still
     define helper functions, but top-level code (or an `if __name__ == "__main__":` block) MUST call
     them and print the result.
   - C: read with scanf(...) inside main(), and call printf(...) with the final answer before returning.
   - C++: read with cin >> ... inside main(), and call cout << ... with the final answer before returning.
6. Ensure test case expected outputs match EXACTLY what the reference solution prints when actually run
   against that test case's input (trailing whitespace is ignored, but the content must match).
7. Do NOT require external libraries, files, interactive prompts, or network access.
8. If the target language is C or C++, #include every standard header the reference solution needs (e.g. <stdio.h> for scanf/printf, <stdlib.h> for malloc in C; <iostream> for cin/cout in C++).

EXAMPLE of a correctly-shaped reference_solution (Python) for a "sum of two numbers" problem whose test
input is "3 5" and whose required output is "8":
    a, b = map(int, input().split())
    print(a + b)
Notice it reads input AND prints the answer - never submit just a function with no I/O. Apply the same
read-then-print shape in whichever language is requested.

STRICT JSON SCHEMA REQUIRED:
{
  "questions": [
    {
      "title": "Problem Title",
      "description": "Problem description statement...",
      "difficulty": "EASY|MEDIUM|HARD",
      "language": "python",
      "topic": "topic_name",
      "constraints": ["1 <= N <= 1000"],
      "input_format": "Input format description",
      "output_format": "Output format description",
      "examples": [
        {"input": "5", "output": "15"}
      ],
      "test_cases": [
        {"input": "5", "expected_output": "15"},
        {"input": "10", "expected_output": "55"}
      ],
      "reference_solution": "A COMPLETE runnable program as a single string (use \\n for newlines) that reads input and prints the final answer - see the EXAMPLE above. Never just a function definition."
    }
  ]
}
"""

class QuestionGenerator:
    """
    Orchestrates AI question generation, Pydantic parsing, retry loops,
    and Docker container reference solution verification.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        if provider:
            self.provider = provider
        elif settings.AI_PROVIDER_TYPE == "mock":
            self.provider = MockAIProvider()
        else:
            self.provider = OllamaProvider()

    def _extract_json_str(self, raw_text: str) -> str:
        """Helper to extract JSON object from raw response string."""
        text = raw_text.strip()
        # Remove markdown code block fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    def generate_and_verify_questions(
        self,
        db: Session,
        teacher: User,
        request: AIGenerateRequest
    ) -> AIGenerateResponse:
        """
        Main Question Generation & Verification Pipeline:
        1. Prompts AI for requested question count.
        2. Validates JSON & Pydantic schema.
        3. Executes reference solution against test cases in Docker.
        4. Retries up to AI_MAX_RETRIES if verification fails.
        5. Saves verified questions to database in DRAFT status for teacher preview.
        """
        verified_previews: List[AIGeneratedQuestionPreview] = []
        total_generated = 0
        total_verified = 0
        total_failed = 0

        max_attempts = settings.AI_MAX_RETRIES
        attempt = 0
        feedback_history = ""
        failure_reasons: List[str] = []  # shown to the teacher when attempts fail

        while attempt < max_attempts and total_verified < request.count:
            attempt += 1
            # Ask for only what's still missing, not the full count again - a prior
            # attempt may have already verified some of the batch, and re-requesting
            # the full count both wastes an LLM + Docker-verification pass per
            # already-satisfied question and can overshoot request.count.
            remaining = request.count - total_verified
            current_prompt = (
                f"Generate {remaining} original coding problem(s) in language '{request.language}', "
                f"difficulty '{request.difficulty.value}', topic '{request.topic}'."
            )
            if feedback_history:
                current_prompt += f"\n\nPREVIOUS ATTEMPT FAILED WITH ERROR:\n{feedback_history}\nPlease fix all issues and generate valid JSON again."

            logger.info(f"[QuestionGenerator] AI Generation attempt {attempt}/{max_attempts}...")

            try:
                raw_response = self.provider.generate_structured_response(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=current_prompt
                )
            except Exception as e:
                logger.error(f"[QuestionGenerator] AI Provider error: {str(e)}")
                if isinstance(e, AIServiceUnavailableException):
                    raise e
                raise AIServiceUnavailableException(f"AI generation failed: {str(e)}")

            json_str = self._extract_json_str(raw_response)

            # Step 1: Pydantic Schema Parsing
            try:
                data_dict = json.loads(json_str)
                parsed_list = AIGeneratedQuestionListSchema.model_validate(data_dict)
            except Exception as parse_err:
                feedback_history = f"JSON parsing / schema validation error: {str(parse_err)}"
                logger.warning(f"[QuestionGenerator] {feedback_history}")
                failure_reasons.append(f"Attempt {attempt}: the AI response was not valid problem JSON ({str(parse_err)[:200]})")
                total_failed += 1
                continue

            total_generated += len(parsed_list.questions)

            # Step 2: Validate and verify each generated question
            for q in parsed_list.questions:
                if total_verified >= request.count:
                    # Already have everything requested - don't spend Docker
                    # verification time on extra questions this attempt returned.
                    break

                is_valid, verification_msg = QuestionValidator.verify_reference_solution_in_docker(q)

                if is_valid:
                    # Save problem to DB in DRAFT status so it's ready for teacher preview/confirmation
                    db_problem = Problem(
                        title=q.title,
                        description=q.description,
                        difficulty=q.difficulty,
                        status=ProblemStatus.DRAFT,  # Draft until teacher clicks Save/Confirm
                        topic=q.topic,
                        language=q.language,
                        constraints="\n".join(q.constraints) if q.constraints else None,
                        input_format=q.input_format,
                        output_format=q.output_format,
                        examples=json.dumps([ex.model_dump() for ex in q.examples]),
                        reference_solution=q.reference_solution,
                        created_by=teacher.id
                    )
                    db.add(db_problem)
                    db.commit()
                    db.refresh(db_problem)

                    # Save test cases for this problem
                    for tc in q.test_cases:
                        db_tc = TestCase(
                            problem_id=db_problem.id,
                            input=tc.input,
                            expected_output=tc.expected_output
                        )
                        db.add(db_tc)
                    db.commit()

                    total_verified += 1
                    verified_previews.append(AIGeneratedQuestionPreview(
                        id=db_problem.id,
                        title=q.title,
                        description=q.description,
                        difficulty=q.difficulty,
                        status=ProblemStatus.DRAFT,
                        language=q.language,
                        topic=q.topic,
                        constraints="\n".join(q.constraints) if q.constraints else None,
                        input_format=q.input_format,
                        output_format=q.output_format,
                        examples=json.dumps([ex.model_dump() for ex in q.examples]),
                        test_case_count=len(q.test_cases),
                        verification_message=verification_msg
                    ))
                else:
                    total_failed += 1
                    retry_hint = verification_msg
                    if "Got: ''" in verification_msg:
                        # Empty output almost always means the model wrote a bare function
                        # (def factorial(n): ...) and never called it / read input / printed
                        # the result. Spell this out so the retry can actually self-correct.
                        retry_hint += (
                            " This means your reference_solution produced NO output at all - it almost "
                            "certainly only defined a function without reading input, calling it, or "
                            "printing the result. Rewrite it as a complete runnable program: read the "
                            "input, compute the answer, and print it (see the EXAMPLE in the system prompt)."
                        )
                    feedback_history = f"Problem '{q.title}' failed Docker verification: {retry_hint}"
                    failure_reasons.append(f"'{q.title}' failed verification: {verification_msg[:300]}")

        return AIGenerateResponse(
            generated=total_generated,
            verified=total_verified,
            failed=total_failed,
            questions=verified_previews,
            failure_reasons=failure_reasons
        )
