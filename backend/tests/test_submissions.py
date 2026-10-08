"""
tests/test_submissions.py
=========================
Phase 2 – Code Submission & Execution Tests

Docker is not available in the test environment, so we patch
`app.services.submission_service.run_code` with a mock that
simulates different execution outcomes without actually running Docker.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


# ─── Helpers ──────────────────────────────────────────────────────────────────

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


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def teacher_token(client: TestClient) -> str:
    return register_and_login(client, "teacher@sub.com", "pass1234", "TEACHER")


@pytest.fixture
def student_token(client: TestClient) -> str:
    return register_and_login(client, "student@sub.com", "pass1234", "STUDENT")


@pytest.fixture
def problem_with_testcases(client: TestClient, teacher_token: str) -> dict:
    """Create a problem and attach test cases; return the problem dict."""
    prob_resp = client.post(
        "/api/problems",
        json={"title": "Add Two Numbers", "description": "Print sum of two ints", "difficulty": "EASY"},
        headers=auth_header(teacher_token),
    )
    assert prob_resp.status_code == 201
    prob = prob_resp.json()

    tc_resp = client.post(
        f"/api/problems/{prob['id']}/testcases",
        json={"input": "5 10", "expected_output": "15"},
        headers=auth_header(teacher_token),
    )
    assert tc_resp.status_code == 201
    return prob


CORRECT_CODE = "a,b=map(int,input().split())\nprint(a+b)"
WRONG_CODE   = "print(999)"
ERROR_CODE   = "raise ValueError('boom')"


# ─── Mock helpers ─────────────────────────────────────────────────────────────

def mock_correct(language, source_code, input_data):
    # Simulate running the code: compute the sum correctly
    parts = input_data.strip().split()
    result = sum(int(p) for p in parts)
    return str(result) + "\n", "", 0, False


def mock_wrong(language, source_code, input_data):
    return "999\n", "", 0, False


def mock_runtime_error(language, source_code, input_data):
    return "", "ValueError: boom\n", 1, False


def mock_timeout(language, source_code, input_data):
    return "", "", -1, True


# ─── Tests ────────────────────────────────────────────────────────────────────

RUNNER_PATH = "app.services.submission_service.run_code"


class TestSubmitCode:
    def test_submitting_to_problem_with_no_testcases_fails_closed(self, client, teacher_token, student_token):
        """
        Regression test: a problem with zero test cases must not silently
        auto-accept submissions (the evaluation loop simply never runs, so the
        old code's implicit fallthrough reported ACCEPTED for anything,
        including empty code).
        """
        prob = client.post(
            "/api/problems",
            json={"title": "No Test Cases Yet", "description": "d", "difficulty": "EASY"},
            headers=auth_header(teacher_token),
        ).json()

        resp = client.post(
            "/api/submissions",
            json={"problem_id": prob["id"], "language": "python", "source_code": "print(1)"},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 400
        assert "no test cases" in resp.json()["detail"].lower()

    def test_teacher_cannot_submit(self, client, teacher_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": CORRECT_CODE,
                },
                headers=auth_header(teacher_token),
            )
        assert resp.status_code == 403

    def test_student_can_submit_correct_code(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": CORRECT_CODE,
                },
                headers=auth_header(student_token),
            )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["status"] == "ACCEPTED"
        assert data["execution_time"] is not None

    def test_wrong_answer_returns_wrong_answer(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_wrong):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": WRONG_CODE,
                },
                headers=auth_header(student_token),
            )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "WRONG_ANSWER"

    def test_runtime_error_handled(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_runtime_error):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": ERROR_CODE,
                },
                headers=auth_header(student_token),
            )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["status"] == "RUNTIME_ERROR"
        assert data["failed_test_case"] == 1
        assert data["total_test_cases"] == 1
        assert data["error_message"] == "ValueError: boom"

    def test_wrong_answer_reports_failed_test_without_leaking_expected(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_wrong):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": WRONG_CODE,
                },
                headers=auth_header(student_token),
            )
        data = resp.json()
        assert data["failed_test_case"] == 1
        assert data["error_message"] is None
        assert "15" not in resp.text  # hidden expected output must not be exposed

    def test_accepted_has_no_failure_details(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": CORRECT_CODE,
                },
                headers=auth_header(student_token),
            )
        data = resp.json()
        assert data["failed_test_case"] is None
        assert data["error_message"] is None

    def test_timeout_returns_tle(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_timeout):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": "while True: pass",
                },
                headers=auth_header(student_token),
            )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "TIME_LIMIT_EXCEEDED"

    def test_submit_nonexistent_problem(self, client, student_token):
        resp = client.post(
            "/api/submissions",
            json={"problem_id": 99999, "language": "python", "source_code": "print(1)"},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 404

    def test_unsupported_language_rejected(self, client, student_token, problem_with_testcases):
        resp = client.post(
            "/api/submissions",
            json={
                "problem_id": problem_with_testcases["id"],
                "language": "java",
                "source_code": "System.out.println(1);",
            },
            headers=auth_header(student_token),
        )
        assert resp.status_code == 400

    def test_student_can_submit_correct_c_code(self, client, student_token, problem_with_testcases):
        c_code = (
            "#include <stdio.h>\n"
            "int main() { int a, b; scanf(\"%d %d\", &a, &b); printf(\"%d\\n\", a + b); return 0; }"
        )
        with patch(RUNNER_PATH, side_effect=mock_correct):
            resp = client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "c",
                    "source_code": c_code,
                },
                headers=auth_header(student_token),
            )
        assert resp.status_code == 201, resp.text
        assert resp.json()["status"] == "ACCEPTED"


class TestRunCode:
    def test_student_can_run_correct_code(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            resp = client.post(
                "/api/submissions/run",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": CORRECT_CODE,
                },
                headers=auth_header(student_token),
            )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["all_passed"] is True
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "PASSED"
        assert data["results"][0]["actual_output"] == "15"
        assert data["results"][0]["expected_output"] == "15"

    def test_run_does_not_create_submission(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post(
                "/api/submissions/run",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": CORRECT_CODE,
                },
                headers=auth_header(student_token),
            )
        resp = client.get("/api/submissions/my", headers=auth_header(student_token))
        assert resp.json() == []

    def test_run_wrong_answer(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_wrong):
            resp = client.post(
                "/api/submissions/run",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": WRONG_CODE,
                },
                headers=auth_header(student_token),
            )
        data = resp.json()
        assert data["all_passed"] is False
        assert data["results"][0]["status"] == "WRONG_ANSWER"
        assert data["results"][0]["actual_output"] == "999"

    def test_run_runtime_error(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_runtime_error):
            resp = client.post(
                "/api/submissions/run",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": ERROR_CODE,
                },
                headers=auth_header(student_token),
            )
        data = resp.json()
        assert data["results"][0]["status"] == "RUNTIME_ERROR"
        assert data["results"][0]["error_message"] == "ValueError: boom"

    def test_run_timeout(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_timeout):
            resp = client.post(
                "/api/submissions/run",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": "while True: pass",
                },
                headers=auth_header(student_token),
            )
        assert resp.json()["results"][0]["status"] == "TIME_LIMIT_EXCEEDED"

    def test_teacher_cannot_run_code(self, client, teacher_token, problem_with_testcases):
        resp = client.post(
            "/api/submissions/run",
            json={
                "problem_id": problem_with_testcases["id"],
                "language": "python",
                "source_code": CORRECT_CODE,
            },
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 403

    def test_run_nonexistent_problem(self, client, student_token):
        resp = client.post(
            "/api/submissions/run",
            json={"problem_id": 99999, "language": "python", "source_code": "print(1)"},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 404

    def test_run_only_checks_sample_limit(self, client, student_token, teacher_token):
        """Only the first 3 test cases are run, even if the problem has more."""
        prob_resp = client.post(
            "/api/problems",
            json={"title": "Many Cases", "description": "desc", "difficulty": "EASY"},
            headers=auth_header(teacher_token),
        )
        problem_id = prob_resp.json()["id"]
        for i in range(5):
            client.post(
                f"/api/problems/{problem_id}/testcases",
                json={"input": str(i), "expected_output": str(i)},
                headers=auth_header(teacher_token),
            )

        with patch(RUNNER_PATH, side_effect=lambda language, source, input_data: (input_data, "", 0, False)):
            resp = client.post(
                "/api/submissions/run",
                json={"problem_id": problem_id, "language": "python", "source_code": "pass"},
                headers=auth_header(student_token),
            )
        assert len(resp.json()["results"]) == 3


class TestSampleTestCases:
    def test_student_sees_up_to_three_sample_testcases(self, client, student_token, teacher_token):
        prob_resp = client.post(
            "/api/problems",
            json={"title": "Many Cases", "description": "desc", "difficulty": "EASY"},
            headers=auth_header(teacher_token),
        )
        problem_id = prob_resp.json()["id"]
        for i in range(5):
            client.post(
                f"/api/problems/{problem_id}/testcases",
                json={"input": str(i), "expected_output": str(i)},
                headers=auth_header(teacher_token),
            )

        resp = client.get(
            f"/api/problems/{problem_id}/sample-testcases",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert [tc["input"] for tc in data] == ["0", "1", "2"]

    def test_sample_testcases_nonexistent_problem(self, client, student_token):
        resp = client.get(
            "/api/problems/99999/sample-testcases",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 404


class TestSubmissionHistory:
    def test_student_can_view_own_history(self, client, student_token, problem_with_testcases):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post(
                "/api/submissions",
                json={
                    "problem_id": problem_with_testcases["id"],
                    "language": "python",
                    "source_code": CORRECT_CODE,
                },
                headers=auth_header(student_token),
            )
        resp = client.get("/api/submissions/my", headers=auth_header(student_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["problem"] == "Add Two Numbers"
        assert data[0]["language"] == "python"
        assert data[0]["status"] == "ACCEPTED"

    def test_teacher_cannot_view_submission_history(self, client, teacher_token):
        resp = client.get("/api/submissions/my", headers=auth_header(teacher_token))
        assert resp.status_code == 403

    def test_empty_history(self, client, student_token):
        resp = client.get("/api/submissions/my", headers=auth_header(student_token))
        assert resp.status_code == 200
        assert resp.json() == []
