import pytest
from unittest.mock import patch
from app.models.user import User, UserRole
from app.models.problem import Problem, ProblemStatus, ProblemDifficulty
from app.schemas.ai import AIGeneratedQuestionSchema, AIGeneratedTestCaseSchema, AIGenerateRequest
from app.services.ai_provider import MockAIProvider
from app.services.question_validator import QuestionValidator
from app.services.question_generator import QuestionGenerator
from app.services.ai_service import AIService
from app.services.ollama_provider import AIServiceUnavailableException

# Fixtures for login tokens
def get_teacher_token(client):
    res = client.post("/api/auth/register", json={
        "name": "AI Teacher",
        "email": "aiteacher@example.com",
        "password": "password123",
        "role": "TEACHER"
    })
    return res.json()["access_token"] if "access_token" in res.json() else client.post("/api/auth/login", json={
        "email": "aiteacher@example.com",
        "password": "password123"
    }).json()["access_token"]

def get_student_token(client):
    res = client.post("/api/auth/register", json={
        "name": "AI Student",
        "email": "aistudent@example.com",
        "password": "password123",
        "role": "STUDENT"
    })
    return res.json()["access_token"] if "access_token" in res.json() else client.post("/api/auth/login", json={
        "email": "aistudent@example.com",
        "password": "password123"
    }).json()["access_token"]


class TestAIGenerationAndVerification:

    def test_mock_ai_provider_valid_response(self):
        provider = MockAIProvider()
        response = provider.generate_structured_response("sys", "user")
        assert "questions" in response
        assert "Sum of First N Natural Numbers" in response

    def test_validator_schema_validation(self):
        # Test missing title
        q_missing_title = AIGeneratedQuestionSchema(
            title="",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
            language="python",
            topic="math",
            constraints=["1 <= N"],
            input_format="N",
            output_format="sum",
            examples=[],
            test_cases=[AIGeneratedTestCaseSchema(input="5", expected_output="15")],
            reference_solution="print(15)"
        )
        is_valid, msg = QuestionValidator.validate_schema_and_consistency(q_missing_title)
        assert is_valid is False
        assert "empty" in msg.lower()

        # Test missing test cases
        q_no_tc = AIGeneratedQuestionSchema(
            title="Valid Title",
            description="desc",
            difficulty=ProblemDifficulty.EASY,
            language="python",
            topic="math",
            constraints=[],
            input_format="N",
            output_format="sum",
            examples=[],
            test_cases=[],
            reference_solution="print(15)"
        )
        is_valid, msg = QuestionValidator.validate_schema_and_consistency(q_no_tc)
        assert is_valid is False
        assert "no test cases" in msg.lower()

    @patch("app.services.question_validator.run_code")
    def test_reference_solution_passes_verification(self, mock_run):
        # Mock run_code to simulate correct stdout
        def mock_runner(language, source_code, input_data, **kwargs):
            if input_data == "5":
                return "15\n", "", 0, False
            if input_data == "10":
                return "55\n", "", 0, False
            return "0\n", "", 0, False

        mock_run.side_effect = mock_runner

        q = AIGeneratedQuestionSchema(
            title="Sum Problem",
            description="Calculate sum 1 to N",
            difficulty=ProblemDifficulty.EASY,
            language="python",
            topic="math",
            constraints=["1 <= N <= 10"],
            input_format="N",
            output_format="sum",
            examples=[],
            test_cases=[
                AIGeneratedTestCaseSchema(input="5", expected_output="15"),
                AIGeneratedTestCaseSchema(input="10", expected_output="55")
            ],
            reference_solution="n = int(input()); print(n*(n+1)//2)"
        )

        is_verified, msg = QuestionValidator.verify_reference_solution_in_docker(q)
        assert is_verified is True
        assert "passed all" in msg.lower()

    @patch("app.services.question_validator.run_code")
    def test_parallel_verification_reports_correct_failing_test_case_index(self, mock_run):
        """Test cases now verify concurrently (speed fix) - confirm the
        reported failing index still matches its original position, not
        whichever container happened to finish first."""
        def mock_runner(language, source_code, input_data, **kwargs):
            n = int(input_data)
            if n < 3:
                return f"{n}\n", "", 0, False  # correct for test cases #1 and #2
            return "wrong\n", "", 0, False  # wrong for #3 onward

        mock_run.side_effect = mock_runner

        q = AIGeneratedQuestionSchema(
            title="Echo Problem", description="Echo N", difficulty=ProblemDifficulty.EASY,
            language="python", topic="math", constraints=[], input_format="N", output_format="N",
            examples=[],
            test_cases=[
                AIGeneratedTestCaseSchema(input="1", expected_output="1"),
                AIGeneratedTestCaseSchema(input="2", expected_output="2"),
                AIGeneratedTestCaseSchema(input="3", expected_output="3"),
            ],
            reference_solution="n=int(input()); print(n)"
        )

        is_verified, msg = QuestionValidator.verify_reference_solution_in_docker(q)
        assert is_verified is False
        assert "test case #3" in msg

    @patch("app.services.question_validator.run_code")
    def test_reference_solution_failing_output_rejected(self, mock_run):
        # Mock runner returning wrong answer
        mock_run.return_value = ("99999\n", "", 0, False)

        q = AIGeneratedQuestionSchema(
            title="Broken Problem",
            description="Calculate sum",
            difficulty=ProblemDifficulty.EASY,
            language="python",
            topic="math",
            constraints=[],
            input_format="N",
            output_format="sum",
            examples=[],
            test_cases=[AIGeneratedTestCaseSchema(input="5", expected_output="15")],
            reference_solution="print(99999)"
        )

        is_verified, msg = QuestionValidator.verify_reference_solution_in_docker(q)
        assert is_verified is False
        assert "mismatch" in msg.lower()

    @patch("app.services.question_validator.run_code")
    def test_reference_solution_timeout_rejected(self, mock_run):
        # Mock runner timing out
        mock_run.return_value = ("", "TimeoutExpired", -1, True)

        q = AIGeneratedQuestionSchema(
            title="Infinite Loop Problem",
            description="Infinite loop",
            difficulty=ProblemDifficulty.EASY,
            language="python",
            topic="loops",
            constraints=[],
            input_format="N",
            output_format="sum",
            examples=[],
            test_cases=[AIGeneratedTestCaseSchema(input="5", expected_output="15")],
            reference_solution="while True: pass"
        )

        is_verified, msg = QuestionValidator.verify_reference_solution_in_docker(q)
        assert is_verified is False
        assert "timed out" in msg.lower()

    @patch("app.services.question_validator.run_code")
    def test_reference_solution_runtime_error_rejected(self, mock_run):
        # Mock runner producing runtime error
        mock_run.return_value = ("", "ZeroDivisionError: division by zero", 1, False)

        q = AIGeneratedQuestionSchema(
            title="Division Error",
            description="Divide by zero",
            difficulty=ProblemDifficulty.EASY,
            language="python",
            topic="math",
            constraints=[],
            input_format="N",
            output_format="result",
            examples=[],
            test_cases=[AIGeneratedTestCaseSchema(input="5", expected_output="15")],
            reference_solution="print(1/0)"
        )

        is_verified, msg = QuestionValidator.verify_reference_solution_in_docker(q)
        assert is_verified is False
        assert "runtime error" in msg.lower()

    def test_failure_reasons_reported_when_all_attempts_fail(self, db_session):
        class BrokenProvider:
            def generate_structured_response(self, system_prompt, user_prompt):
                return "this is not json"

        teacher = User(name="T", email="t@reasons.com", password_hash="x", role=UserRole.TEACHER)
        db_session.add(teacher)
        db_session.commit()

        result = QuestionGenerator(provider=BrokenProvider()).generate_and_verify_questions(
            db_session, teacher, AIGenerateRequest(topic="loops", count=1))

        assert result.verified == 0 and result.questions == []
        assert len(result.failure_reasons) == result.failed > 0
        assert "not valid problem JSON" in result.failure_reasons[0]

    @patch("app.services.question_validator.run_code")
    def test_empty_output_retry_hint_enables_self_correction(self, mock_run, db_session):
        """
        Simulates the real failure mode this prompt rewrite targets: a small
        local model writes a bare function with no stdin/stdout wiring on the
        first attempt (produces empty output), then - having received an
        explicit "you produced no output" retry hint - writes a complete,
        working program on the second attempt.
        """
        def mock_runner(language, source_code, input_data):
            if "print(" not in source_code:
                return "", "", 0, False  # bare function: runs, but prints nothing
            n = int(input_data.strip())
            result = 1
            for i in range(2, n + 1):
                result *= i
            return f"{result}\n", "", 0, False

        mock_run.side_effect = mock_runner

        BROKEN_SOLUTION = "def factorial(n):\\n    return 1 if n == 0 else n * factorial(n - 1)"
        FIXED_SOLUTION = "n = int(input())\\nresult = 1\\nfor i in range(2, n + 1):\\n    result *= i\\nprint(result)"

        def question_json(reference_solution):
            return f"""{{
  "questions": [
    {{
      "title": "Factorial of a Number",
      "description": "Calculate the factorial of N.",
      "difficulty": "EASY",
      "language": "python",
      "topic": "recursion",
      "constraints": ["0 <= N <= 10"],
      "input_format": "Single integer N",
      "output_format": "Factorial of N",
      "examples": [{{"input": "5", "output": "120"}}],
      "test_cases": [
        {{"input": "5", "expected_output": "120"}},
        {{"input": "6", "expected_output": "720"}}
      ],
      "reference_solution": "{reference_solution}"
    }}
  ]
}}"""

        class EmptyOutputThenFixedProvider:
            def generate_structured_response(self, system_prompt, user_prompt, response_schema=None):
                if "PREVIOUS ATTEMPT FAILED" in user_prompt:
                    # the targeted retry hint actually reached the model
                    assert "only defined a function" in user_prompt
                    return question_json(FIXED_SOLUTION)
                return question_json(BROKEN_SOLUTION)

        teacher = User(name="T2", email="t2@reasons.com", password_hash="x", role=UserRole.TEACHER)
        db_session.add(teacher)
        db_session.commit()

        result = QuestionGenerator(provider=EmptyOutputThenFixedProvider()).generate_and_verify_questions(
            db_session, teacher, AIGenerateRequest(topic="recursion", count=1))

        assert result.verified == 1
        assert result.failed == 1
        assert len(result.questions) == 1
        # Teacher-facing failure reasons stay the original concise message, not the retry hint
        assert "Got: ''" in result.failure_reasons[0]
        assert "only defined a function" not in result.failure_reasons[0]

    @patch("app.services.question_validator.run_code")
    def test_retry_prompt_requests_only_remaining_count(self, mock_run, db_session):
        """
        Speed/efficiency fix: a retry must ask for only the still-missing
        number of questions, not the full original count again - otherwise
        every retry redoes LLM + Docker verification work for questions
        that were already verified on a prior attempt.
        """
        def mock_runner(language, source_code, input_data):
            n = int(input_data.strip())
            return f"{n * 2}\n", "", 0, False
        mock_run.side_effect = mock_runner

        GOOD_SOLUTION = "n = int(input())\\nprint(n * 2)"

        def question_json(title):
            return f"""{{
  "questions": [
    {{
      "title": "{title}", "description": "Double a number.", "difficulty": "EASY",
      "language": "python", "topic": "math", "constraints": ["1 <= N <= 100"],
      "input_format": "A single integer N.", "output_format": "2 * N.",
      "examples": [{{"input": "3", "output": "6"}}],
      "test_cases": [{{"input": "3", "expected_output": "6"}}, {{"input": "5", "expected_output": "10"}}],
      "reference_solution": "{GOOD_SOLUTION}"
    }}
  ]
}}"""

        captured_prompts = []

        class OneAtATimeProvider:
            """Simulates a model that always returns exactly one question per
            call, regardless of how many were actually requested."""
            def __init__(self):
                self.call_count = 0

            def generate_structured_response(self, system_prompt, user_prompt, response_schema=None):
                captured_prompts.append(user_prompt)
                self.call_count += 1
                return question_json(f"Double v{self.call_count}")

        teacher = User(name="T3", email="t3@reasons.com", password_hash="x", role=UserRole.TEACHER)
        db_session.add(teacher)
        db_session.commit()

        result = QuestionGenerator(provider=OneAtATimeProvider()).generate_and_verify_questions(
            db_session, teacher, AIGenerateRequest(topic="math", count=2))

        assert result.verified == 2
        assert len(captured_prompts) == 2
        assert "Generate 2 original coding problem" in captured_prompts[0]
        assert "Generate 1 original coding problem" in captured_prompts[1]  # not "2" again

    @patch("app.services.question_validator.run_code")
    def test_overshooting_attempt_does_not_exceed_requested_count(self, mock_run, db_session):
        """If a single attempt returns more verified-able questions than
        requested, only up to request.count should be verified/saved -
        extras must not be Docker-verified or persisted."""
        def mock_runner(language, source_code, input_data):
            n = int(input_data.strip())
            return f"{n * 2}\n", "", 0, False
        mock_run.side_effect = mock_runner

        GOOD_SOLUTION = "n = int(input())\\nprint(n * 2)"

        def make_question(title, tc_input, tc_output):
            return f"""{{
      "title": "{title}", "description": "Double a number.", "difficulty": "EASY",
      "language": "python", "topic": "math", "constraints": [],
      "input_format": "A single integer N.", "output_format": "2 * N.",
      "examples": [{{"input": "{tc_input}", "output": "{tc_output}"}}],
      "test_cases": [{{"input": "{tc_input}", "expected_output": "{tc_output}"}}],
      "reference_solution": "{GOOD_SOLUTION}"
    }}"""

        class OvershootProvider:
            def generate_structured_response(self, system_prompt, user_prompt, response_schema=None):
                return f"""{{"questions": [{make_question("Q1", "3", "6")}, {make_question("Q2", "4", "8")}]}}"""

        teacher = User(name="T4", email="t4@reasons.com", password_hash="x", role=UserRole.TEACHER)
        db_session.add(teacher)
        db_session.commit()

        result = QuestionGenerator(provider=OvershootProvider()).generate_and_verify_questions(
            db_session, teacher, AIGenerateRequest(topic="math", count=1))

        assert result.verified == 1
        assert len(result.questions) == 1
        assert db_session.query(Problem).filter(Problem.created_by == teacher.id).count() == 1


class TestAIApiAndSecurity:

    @patch("app.api.problems.AIService")
    def test_teacher_can_generate_ai_problems(self, mock_ai_service_cls, client):
        teacher_token = get_teacher_token(client)
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # Setup mock AI service instance
        mock_instance = mock_ai_service_cls.return_value
        mock_instance.generate_problems.return_value = {
            "generated": 1,
            "verified": 1,
            "failed": 0,
            "questions": [{
                "id": 101,
                "title": "Generated Problem",
                "description": "Desc",
                "difficulty": "EASY",
                "status": "DRAFT",
                "language": "python",
                "topic": "recursion",
                "test_case_count": 2,
                "verification_message": "Verified"
            }]
        }

        res = client.post("/api/problems/generate", json={
            "language": "python",
            "difficulty": "EASY",
            "topic": "recursion",
            "count": 1
        }, headers=headers)

        assert res.status_code == 200
        data = res.json()
        assert data["verified"] == 1
        assert data["questions"][0]["title"] == "Generated Problem"

    def test_student_cannot_call_ai_generator(self, client):
        student_token = get_student_token(client)
        headers = {"Authorization": f"Bearer {student_token}"}

        res = client.post("/api/problems/generate", json={
            "language": "python",
            "difficulty": "EASY",
            "topic": "recursion",
            "count": 1
        }, headers=headers)

        # Student role forbidden from generating problems
        assert res.status_code == 403

    def test_student_cannot_see_draft_or_unverified_problems(self, client, db_session):
        teacher_token = get_teacher_token(client)
        student_token = get_student_token(client)

        # Create a DRAFT problem manually
        draft_prob = Problem(
            title="Secret Draft Problem",
            description="Top secret problem in draft state",
            difficulty=ProblemDifficulty.HARD,
            status=ProblemStatus.DRAFT,
            created_by=1
        )
        db_session.add(draft_prob)
        db_session.commit()
        db_session.refresh(draft_prob)

        # Student lists problems -> should NOT contain draft_prob
        res_student = client.get("/api/problems", headers={"Authorization": f"Bearer {student_token}"})
        assert res_student.status_code == 200
        prob_ids = [p["id"] for p in res_student.json()]
        assert draft_prob.id not in prob_ids

        # Student gets problem detail directly -> 404 Not Found
        res_detail = client.get(f"/api/problems/{draft_prob.id}", headers={"Authorization": f"Bearer {student_token}"})
        assert res_detail.status_code == 404

        # Teacher lists problems -> CAN see draft_prob
        res_teacher = client.get("/api/problems", headers={"Authorization": f"Bearer {teacher_token}"})
        assert res_teacher.status_code == 200
        teacher_ids = [p["id"] for p in res_teacher.json()]
        assert draft_prob.id in teacher_ids

    def test_reference_solution_not_exposed_in_public_api(self, client, db_session):
        student_token = get_student_token(client)

        # Create a verified problem with reference_solution set
        verified_prob = Problem(
            title="Public Problem",
            description="Normal problem",
            difficulty=ProblemDifficulty.EASY,
            status=ProblemStatus.VERIFIED,
            reference_solution="import sys\nprint('secret_solution')",
            created_by=1
        )
        db_session.add(verified_prob)
        db_session.commit()
        db_session.refresh(verified_prob)

        res = client.get(f"/api/problems/{verified_prob.id}", headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 200
        data = res.json()
        assert "reference_solution" not in data

    def test_ollama_unavailable_returns_clean_503_error(self, client):
        teacher_token = get_teacher_token(client)
        headers = {"Authorization": f"Bearer {teacher_token}"}

        with patch("app.api.problems.AIService") as mock_ai:
            mock_ai.return_value.generate_problems.side_effect = AIServiceUnavailableException(
                "AI service is currently unavailable. Please make sure Ollama is running."
            )

            res = client.post("/api/problems/generate", json={
                "language": "python",
                "difficulty": "EASY",
                "topic": "math",
                "count": 1
            }, headers=headers)

            assert res.status_code == 503
            assert "Ollama is running" in res.json()["detail"]
