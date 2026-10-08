import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List
from app.schemas.ai import AIGeneratedQuestionSchema, AIGeneratedTestCaseSchema
from app.services.code_runner import run_code, SUPPORTED_LANGUAGES

# Each test case runs in its own Docker container; running them concurrently
# overlaps container start/teardown overhead instead of paying it N times in
# series. Capped so a question with an unusually large test-case count can't
# spawn an unbounded number of containers at once.
MAX_PARALLEL_VERIFICATIONS = 6

logger = logging.getLogger(__name__)

class QuestionValidator:
    """
    Deterministic Question Verification Engine.
    Executes AI-generated reference solutions inside isolated Docker containers
    against generated test cases and validates output correctness.
    """

    @staticmethod
    def normalize_output(text: str) -> str:
        """
        Safely normalizes stdout for comparison by stripping trailing whitespace per line.
        Does not perform overly aggressive normalization that could mask errors.
        """
        if text is None:
            return ""
        return "\n".join(line.rstrip() for line in text.strip().splitlines())

    @staticmethod
    def validate_schema_and_consistency(question: AIGeneratedQuestionSchema) -> Tuple[bool, str]:
        """
        Validation Step 1: Validates required fields, non-empty text, and test case presence.
        """
        if not question.title or not question.title.strip():
            return False, "Problem title is empty."

        if not question.description or not question.description.strip():
            return False, "Problem description is empty."

        if not question.input_format or not question.input_format.strip():
            return False, "Input format description is missing."

        if not question.output_format or not question.output_format.strip():
            return False, "Output format description is missing."

        if not question.reference_solution or not question.reference_solution.strip():
            return False, "Reference solution code is missing."

        if not question.test_cases or len(question.test_cases) == 0:
            return False, "No test cases generated for problem."

        if question.language.lower() not in SUPPORTED_LANGUAGES:
            return False, (
                f"Language '{question.language}' is not supported for execution verification. "
                f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
            )

        return True, "Consistency check passed."

    @staticmethod
    def verify_reference_solution_in_docker(
        question: AIGeneratedQuestionSchema
    ) -> Tuple[bool, str]:
        """
        Validation Steps 2 & 3: Executes reference solution securely in Docker
        against all generated test cases and public sample examples.
        """
        # Step 1: Check problem structure first
        is_consistent, msg = QuestionValidator.validate_schema_and_consistency(question)
        if not is_consistent:
            return False, f"Consistency Validation Failed: {msg}"

        # Combine public examples into test cases if not already present
        all_test_cases: List[AIGeneratedTestCaseSchema] = list(question.test_cases)
        for ex in question.examples:
            all_test_cases.append(AIGeneratedTestCaseSchema(
                input=ex.input,
                expected_output=ex.output
            ))

        logger.info(f"[QuestionValidator] Verifying reference solution for problem '{question.title}' across {len(all_test_cases)} test cases...")

        # Step 2: Run reference solution against each test case using Docker runner.
        # Each test case is an independent container, so run them concurrently rather
        # than paying Docker's per-container startup/teardown overhead N times in a row.
        language = question.language.lower()
        with ThreadPoolExecutor(max_workers=min(len(all_test_cases), MAX_PARALLEL_VERIFICATIONS)) as executor:
            run_results = list(executor.map(
                lambda tc: run_code(language=language, source_code=question.reference_solution, input_data=tc.input),
                all_test_cases
            ))

        for index, (tc, (stdout, stderr, return_code, is_timeout)) in enumerate(zip(all_test_cases, run_results)):
            if is_timeout:
                error_msg = f"Reference solution timed out (exceeded 5s limit) on test case #{index + 1}."
                logger.warning(f"[QuestionValidator] {error_msg}")
                return False, error_msg

            if return_code != 0:
                error_msg = f"Reference solution produced runtime error on test case #{index + 1}: {stderr.strip()}"
                logger.warning(f"[QuestionValidator] {error_msg}")
                return False, error_msg

            actual_normalized = QuestionValidator.normalize_output(stdout)
            expected_normalized = QuestionValidator.normalize_output(tc.expected_output)

            if actual_normalized != expected_normalized:
                error_msg = (
                    f"Output mismatch on test case #{index + 1}. "
                    f"Expected: '{expected_normalized}', Got: '{actual_normalized}'."
                )
                logger.warning(f"[QuestionValidator] {error_msg}")
                return False, error_msg

        logger.info(f"[QuestionValidator] Problem '{question.title}' PASSED all {len(all_test_cases)} test cases!")
        return True, "Reference solution passed all generated test cases."
