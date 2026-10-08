import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.models.user import User, UserRole
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus, TestCase
from app.models.submission import Submission, SubmissionStatus
from app.models.feedback import AIFeedback, ErrorCategory
from app.schemas.feedback import AIFeedbackContent
from app.services.ai_provider import MockAIProvider
from app.services.ai_service import AIService
from app.services.tutor_validator import TutorValidator
from app.services.ollama_provider import AIServiceUnavailableException


def register_and_login(client: TestClient, email: str, password: str, role: str) -> str:
    client.post("/api/auth/register", json={
        "name": email.split("@")[0],
        "email": email,
        "password": password,
        "role": role,
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_token(client: TestClient) -> str:
    return register_and_login(client, "tutor_teacher@test.com", "pass1234", "TEACHER")


@pytest.fixture
def student_token(client: TestClient) -> str:
    return register_and_login(client, "tutor_student@test.com", "pass1234", "STUDENT")


@pytest.fixture
def student_user_obj(db_session, client: TestClient, student_token: str) -> User:
    return db_session.query(User).filter(User.email == "tutor_student@test.com").first()


@pytest.fixture
def problem_obj(db_session, client: TestClient, teacher_token: str) -> Problem:
    user = db_session.query(User).filter(User.email == "tutor_teacher@test.com").first()
    prob = Problem(
        title="Sum of Elements",
        description="Compute sum of input integers",
        difficulty=ProblemDifficulty.EASY,
        status=ProblemStatus.VERIFIED,
        topic="arrays",
        language="python",
        constraints="1 <= N <= 100",
        input_format="Space separated numbers",
        output_format="Single sum int",
        examples='[{"input": "1 2", "output": "3"}]',
        reference_solution="print(sum(map(int, input().split())))",
        created_by=user.id
    )
    db_session.add(prob)
    db_session.commit()
    db_session.refresh(prob)
    return prob


class TestAITutorService:

    def test_accepted_submission_feedback(self, db_session, student_user_obj, problem_obj):
        submission = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print(sum(map(int, input().split())))",
            status=SubmissionStatus.ACCEPTED,
            execution_time=0.012
        )
        db_session.add(submission)
        db_session.commit()

        ai_service = AIService(provider=MockAIProvider())
        feedback_res = ai_service.generate_tutor_feedback(
            db=db_session,
            submission=submission,
            problem=problem_obj,
            student_id=student_user_obj.id,
            hint_level=1,
            attempt_number=1
        )

        assert feedback_res.submission_id == submission.id
        assert feedback_res.status == "ACCEPTED"
        assert feedback_res.hint_level == 1
        assert "passed" in feedback_res.feedback.summary.lower()

    def test_wrong_answer_feedback_progressive_hints(self, db_session, student_user_obj, problem_obj):
        submission = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="for i in range(len(arr) - 1): pass",
            status=SubmissionStatus.WRONG_ANSWER,
            execution_time=0.04
        )
        db_session.add(submission)
        db_session.commit()

        ai_service = AIService(provider=MockAIProvider())

        # Test Hint Level 1
        f1 = ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=1, attempt_number=1)
        assert f1.hint_level == 1
        assert f1.feedback.error_type == ErrorCategory.LOGIC_ERROR
        assert "Level 1" in f1.feedback.hint

        # Test Hint Level 2
        f2 = ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=2, attempt_number=2)
        assert f2.hint_level == 2
        assert "Level 2" in f2.feedback.hint

        # Test Hint Level 3
        f3 = ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=3, attempt_number=3)
        assert f3.hint_level == 3
        assert "Level 3" in f3.feedback.hint

    def test_runtime_error_feedback(self, db_session, student_user_obj, problem_obj):
        submission = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print(1/0)",
            status=SubmissionStatus.RUNTIME_ERROR,
            execution_time=0.01
        )
        db_session.add(submission)
        db_session.commit()

        ai_service = AIService(provider=MockAIProvider())
        res = ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=1)
        assert res.feedback.error_type == ErrorCategory.RUNTIME_ERROR
        assert "Runtime error" in res.feedback.summary or "exception" in res.feedback.explanation.lower()

    def test_time_limit_exceeded_feedback(self, db_session, student_user_obj, problem_obj):
        submission = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="while True: pass",
            status=SubmissionStatus.TIME_LIMIT_EXCEEDED,
            execution_time=5.001
        )
        db_session.add(submission)
        db_session.commit()

        ai_service = AIService(provider=MockAIProvider())
        res = ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=1)
        assert res.feedback.error_type == ErrorCategory.TIME_COMPLEXITY
        assert "Time Limit" in res.feedback.summary

    def test_compilation_error_feedback(self, db_session, student_user_obj, problem_obj):
        submission = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="def broken_func(",
            status=SubmissionStatus.RUNTIME_ERROR,
            execution_time=0.01
        )
        db_session.add(submission)
        db_session.commit()

        mock = MockAIProvider()
        ai_service = AIService(provider=mock)
        res = ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=1)
        assert res.feedback is not None

    def test_anti_solution_guard_rejects_full_code_exposure(self):
        candidate = AIFeedbackContent(
            summary="Here is your solution",
            error_type=ErrorCategory.LOGIC_ERROR,
            explanation="You can fix your code using def solution():\n    return 42",
            hint="def solution():\n    x = 10\n    y = 20\n    return x + y\n    print(123)",
            next_step="Copy code above",
            confidence=0.99
        )

        is_valid, msg = TutorValidator.validate_tutor_feedback(candidate)
        assert is_valid is False
        assert "full function implementation" in msg or "excessive code" in msg

    def test_anti_solution_guard_rejects_short_response_with_oneliner_leak(self):
        """
        Regression test: the old Rule 1 checked the TOTAL line count of the whole
        response (summary+explanation+hint+next_step), so a short 4-field
        response smuggling in a complete one-line solution (`def foo(): return 42`)
        never exceeded the 5-line threshold and was never rejected.
        """
        candidate = AIFeedbackContent(
            summary="Check your loop.",
            error_type=ErrorCategory.LOGIC_ERROR,
            explanation="Your function never returns.",
            hint="def foo(): return 42",
            next_step="Try again.",
            confidence=0.9
        )

        is_valid, msg = TutorValidator.validate_tutor_feedback(candidate)
        assert is_valid is False
        assert "full function implementation" in msg

    def test_anti_solution_guard_rejects_cpp_function_leak(self):
        """The old regex only matched Python's `def`, so a leaked C/C++ solution
        was never caught at all."""
        candidate = AIFeedbackContent(
            summary="Here is the fix",
            error_type=ErrorCategory.LOGIC_ERROR,
            explanation="Use this instead",
            hint="int add(int a, int b) { int result = a + b; return result; }",
            next_step="Copy this",
            confidence=0.9
        )

        is_valid, msg = TutorValidator.validate_tutor_feedback(candidate)
        assert is_valid is False
        assert "full function implementation" in msg

    def test_anti_solution_guard_allows_tiny_prose_mention_of_a_function(self):
        """A bare mention of a function's signature in prose (no real
        implementation following it) must still be allowed - only an actual
        body/one-liner should be rejected."""
        candidate = AIFeedbackContent(
            summary="Logic issue in your helper.",
            error_type=ErrorCategory.LOGIC_ERROR,
            explanation="Look at where your def solve(): function processes the last element.",
            hint="Consider what happens inside def solve(): when the list is empty.",
            next_step="Trace through with an empty list.",
            confidence=0.9
        )

        is_valid, msg = TutorValidator.validate_tutor_feedback(candidate)
        assert is_valid is True

    def test_hidden_tests_and_reference_solution_not_sent_to_ai_prompt(self, db_session, student_user_obj, problem_obj):
        # Create a hidden test case
        tc = TestCase(problem_id=problem_obj.id, input="SECRET_INPUT_123", expected_output="SECRET_OUTPUT_456")
        db_session.add(tc)
        problem_obj.reference_solution = "DEF_SECRET_SOLUTION_789"
        db_session.commit()

        submission = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print('student')",
            status=SubmissionStatus.WRONG_ANSWER
        )
        db_session.add(submission)
        db_session.commit()

        captured_prompts = []

        class InspectingProvider(MockAIProvider):
            def generate_structured_response(self, system_prompt, user_prompt, response_schema=None):
                captured_prompts.append(user_prompt)
                return super().generate_structured_response(system_prompt, user_prompt, response_schema)

        ai_service = AIService(provider=InspectingProvider())
        ai_service.generate_tutor_feedback(db_session, submission, problem_obj, student_user_obj.id, hint_level=1)

        assert len(captured_prompts) == 1
        prompt = captured_prompts[0]
        # Assert hidden test cases and reference solution are strictly ABSENT from prompt
        assert "SECRET_INPUT_123" not in prompt
        assert "SECRET_OUTPUT_456" not in prompt
        assert "DEF_SECRET_SOLUTION_789" not in prompt


class TestAITutorApiAndSecurity:

    def test_student_can_request_feedback_for_own_submission(self, client, student_token, db_session, student_user_obj, problem_obj):
        sub = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="x = int(input()); print(x)",
            status=SubmissionStatus.WRONG_ANSWER
        )
        db_session.add(sub)
        db_session.commit()

        with patch("app.core.config.settings.AI_PROVIDER_TYPE", "mock"):
            res = client.post(
                f"/api/submissions/{sub.id}/feedback",
                json={"hint_level": 1},
                headers=auth_header(student_token)
            )
            assert res.status_code == 200
            data = res.json()
            assert data["submission_id"] == sub.id
            assert data["hint_level"] == 1
            assert "feedback" in data
            assert "summary" in data["feedback"]

    def test_student_cannot_request_another_students_feedback(self, client, student_token, db_session, problem_obj):
        # Create student B
        other_student = User(
            name="Other Student",
            email="other_student@classroom.com",
            password_hash="hashed",
            role=UserRole.STUDENT
        )
        db_session.add(other_student)
        db_session.commit()

        sub = Submission(
            user_id=other_student.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print(1)",
            status=SubmissionStatus.WRONG_ANSWER
        )
        db_session.add(sub)
        db_session.commit()

        # Student A tries to get Student B's feedback
        with patch("app.core.config.settings.AI_PROVIDER_TYPE", "mock"):
            res = client.post(
                f"/api/submissions/{sub.id}/feedback",
                json={"hint_level": 1},
                headers=auth_header(student_token)
            )
            assert res.status_code == 403
            assert "Access denied" in res.json()["detail"]

    def test_teacher_authorization_for_student_submission(self, client, teacher_token, db_session, student_user_obj, problem_obj):
        # Problem created by teacher_user. Not ACCEPTED, since that's blocked
        # regardless of role (no hint is needed for an already-correct solution) -
        # this test is about authorization, not acceptance status.
        sub = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print('test')",
            status=SubmissionStatus.WRONG_ANSWER
        )
        db_session.add(sub)
        db_session.commit()

        # Teacher should be authorized to view feedback
        with patch("app.core.config.settings.AI_PROVIDER_TYPE", "mock"):
            res = client.post(
                f"/api/submissions/{sub.id}/feedback",
                json={"hint_level": 1},
                headers=auth_header(teacher_token)
            )
            assert res.status_code == 200

    def test_accepted_submission_cannot_request_hint(self, client, student_token, db_session, student_user_obj, problem_obj):
        sub = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print(sum(map(int, input().split())))",
            status=SubmissionStatus.ACCEPTED
        )
        db_session.add(sub)
        db_session.commit()

        with patch("app.core.config.settings.AI_PROVIDER_TYPE", "mock"):
            res = client.post(
                f"/api/submissions/{sub.id}/feedback",
                json={"hint_level": 1},
                headers=auth_header(student_token)
            )
        assert res.status_code == 400
        assert "no hint is needed" in res.json()["detail"].lower()

    def test_teacher_also_cannot_request_hint_for_accepted_submission(self, client, teacher_token, db_session, student_user_obj, problem_obj):
        sub = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print('test')",
            status=SubmissionStatus.ACCEPTED
        )
        db_session.add(sub)
        db_session.commit()

        with patch("app.core.config.settings.AI_PROVIDER_TYPE", "mock"):
            res = client.post(
                f"/api/submissions/{sub.id}/feedback",
                json={"hint_level": 1},
                headers=auth_header(teacher_token)
            )
        assert res.status_code == 400

    def test_invalid_submission_id_returns_404(self, client, student_token):
        with patch("app.core.config.settings.AI_PROVIDER_TYPE", "mock"):
            res = client.post(
                "/api/submissions/999999/feedback",
                json={"hint_level": 1},
                headers=auth_header(student_token)
            )
            assert res.status_code == 404

    def test_invalid_ai_response_triggers_retry_and_fallback(self, db_session, student_user_obj, problem_obj):
        sub = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print('hello')",
            status=SubmissionStatus.WRONG_ANSWER
        )
        db_session.add(sub)
        db_session.commit()

        failing_provider = MockAIProvider(should_fail_validation=True)
        ai_service = AIService(provider=failing_provider)

        res = ai_service.generate_tutor_feedback(
            db=db_session,
            submission=sub,
            problem=problem_obj,
            student_id=student_user_obj.id,
            hint_level=1
        )
        assert res.feedback is not None
        assert "evaluation completed" in res.feedback.summary.lower() or "logic error" in res.feedback.summary.lower()

    def test_ollama_unavailable_returns_503_without_modifying_submission_result(self, client, student_token, db_session, student_user_obj, problem_obj):
        sub = Submission(
            user_id=student_user_obj.id,
            problem_id=problem_obj.id,
            language="python",
            source_code="print('hello')",
            status=SubmissionStatus.WRONG_ANSWER
        )
        db_session.add(sub)
        db_session.commit()

        with patch("app.services.ollama_provider.OllamaProvider.generate_structured_response") as mock_gen, \
             patch("app.core.config.settings.AI_PROVIDER_TYPE", "ollama"):
            mock_gen.side_effect = AIServiceUnavailableException("AI service is currently unavailable. Please make sure Ollama is running.")

            res = client.post(
                f"/api/submissions/{sub.id}/feedback",
                json={"hint_level": 1},
                headers=auth_header(student_token)
            )
            assert res.status_code == 503
            assert "AI Tutor is currently unavailable" in res.json()["detail"]

            # CRITICAL CHECK: Submission status in DB remains untouched as WRONG_ANSWER
            db_session.refresh(sub)
            assert sub.status == SubmissionStatus.WRONG_ANSWER
