"""
tests/test_problems.py
======================
Phase 2 – Problem Management Tests
"""
import pytest
from fastapi.testclient import TestClient


# ─── Helpers ──────────────────────────────────────────────────────────────────

def register_and_login(client: TestClient, email: str, password: str, role: str) -> str:
    """Register a user and return their JWT access token."""
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
    return register_and_login(client, "teacher@test.com", "pass1234", "TEACHER")


@pytest.fixture
def student_token(client: TestClient) -> str:
    return register_and_login(client, "student@test.com", "pass1234", "STUDENT")


PROBLEM_PAYLOAD = {
    "title": "Two Sum",
    "description": "Find two numbers whose sum equals target",
    "difficulty": "EASY",
}


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestCreateProblem:
    def test_teacher_can_create_problem(self, client, teacher_token):
        resp = client.post(
            "/api/problems",
            json=PROBLEM_PAYLOAD,
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "Two Sum"
        assert data["difficulty"] == "EASY"
        assert data["test_case_count"] == 0

    def test_student_cannot_create_problem(self, client, student_token):
        resp = client.post(
            "/api/problems",
            json=PROBLEM_PAYLOAD,
            headers=auth_header(student_token),
        )
        assert resp.status_code == 403, resp.text

    def test_unauthenticated_cannot_create_problem(self, client):
        resp = client.post("/api/problems", json=PROBLEM_PAYLOAD)
        assert resp.status_code == 403, resp.text


class TestGetProblems:
    def _create_problem(self, client, teacher_token):
        resp = client.post(
            "/api/problems",
            json=PROBLEM_PAYLOAD,
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 201
        return resp.json()

    def test_list_problems_authenticated(self, client, teacher_token, student_token):
        self._create_problem(client, teacher_token)
        resp = client.get("/api/problems", headers=auth_header(student_token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_problem_detail(self, client, teacher_token, student_token):
        created = self._create_problem(client, teacher_token)
        pid = created["id"]
        resp = client.get(f"/api/problems/{pid}", headers=auth_header(student_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == pid
        assert data["title"] == "Two Sum"

    def test_get_nonexistent_problem_returns_404(self, client, student_token):
        resp = client.get("/api/problems/99999", headers=auth_header(student_token))
        assert resp.status_code == 404


class TestTestCases:
    def _create_problem(self, client, teacher_token):
        resp = client.post(
            "/api/problems",
            json=PROBLEM_PAYLOAD,
            headers=auth_header(teacher_token),
        )
        return resp.json()

    def test_teacher_can_add_testcase(self, client, teacher_token):
        prob = self._create_problem(client, teacher_token)
        tc_payload = {"input": "5 10", "expected_output": "15"}
        resp = client.post(
            f"/api/problems/{prob['id']}/testcases",
            json=tc_payload,
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["input"] == "5 10"
        assert data["expected_output"] == "15"

    def test_student_cannot_add_testcase(self, client, teacher_token, student_token):
        prob = self._create_problem(client, teacher_token)
        resp = client.post(
            f"/api/problems/{prob['id']}/testcases",
            json={"input": "1 2", "expected_output": "3"},
            headers=auth_header(student_token),
        )
        assert resp.status_code == 403

    def test_testcase_count_updates_in_detail(self, client, teacher_token, student_token):
        prob = self._create_problem(client, teacher_token)
        pid = prob["id"]
        # add 2 test cases
        for i in range(2):
            client.post(
                f"/api/problems/{pid}/testcases",
                json={"input": f"{i} {i}", "expected_output": str(i + i)},
                headers=auth_header(teacher_token),
            )
        resp = client.get(f"/api/problems/{pid}", headers=auth_header(student_token))
        assert resp.status_code == 200
        assert resp.json()["test_case_count"] == 2

    def test_add_testcase_to_nonexistent_problem(self, client, teacher_token):
        resp = client.post(
            "/api/problems/99999/testcases",
            json={"input": "1", "expected_output": "1"},
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 404

    def test_other_teacher_cannot_add_testcase(self, client, teacher_token):
        prob = self._create_problem(client, teacher_token)
        other_teacher = register_and_login(client, "other_tc_teacher@test.com", "pass1234", "TEACHER")
        resp = client.post(
            f"/api/problems/{prob['id']}/testcases",
            json={"input": "1", "expected_output": "1"},
            headers=auth_header(other_teacher),
        )
        assert resp.status_code == 403

    def test_other_teacher_cannot_view_testcases(self, client, teacher_token):
        prob = self._create_problem(client, teacher_token)
        client.post(f"/api/problems/{prob['id']}/testcases",
                    json={"input": "5 10", "expected_output": "15"}, headers=auth_header(teacher_token))
        other_teacher = register_and_login(client, "other_tc_viewer@test.com", "pass1234", "TEACHER")
        resp = client.get(f"/api/problems/{prob['id']}/testcases", headers=auth_header(other_teacher))
        assert resp.status_code == 403

    def test_other_teacher_cannot_delete_testcase(self, client, teacher_token):
        prob = self._create_problem(client, teacher_token)
        tc = client.post(f"/api/problems/{prob['id']}/testcases",
                          json={"input": "5 10", "expected_output": "15"}, headers=auth_header(teacher_token)).json()
        other_teacher = register_and_login(client, "other_tc_deleter@test.com", "pass1234", "TEACHER")
        resp = client.delete(f"/api/problems/{prob['id']}/testcases/{tc['id']}", headers=auth_header(other_teacher))
        assert resp.status_code == 403
        # The test case must survive the forbidden attempt
        still_there = client.get(f"/api/problems/{prob['id']}/testcases", headers=auth_header(teacher_token)).json()
        assert any(t["id"] == tc["id"] for t in still_there)


class TestDeleteProblem:
    def _create_problem(self, client, teacher_token, title="Two Sum"):
        resp = client.post(
            "/api/problems",
            json={**PROBLEM_PAYLOAD, "title": title},
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 201
        return resp.json()

    def test_teacher_can_delete_own_problem(self, client, teacher_token):
        prob = self._create_problem(client, teacher_token)
        resp = client.delete(f"/api/problems/{prob['id']}", headers=auth_header(teacher_token))
        assert resp.status_code == 200, resp.text
        assert client.get(f"/api/problems/{prob['id']}", headers=auth_header(teacher_token)).status_code == 404

    def test_other_teacher_cannot_delete_problem(self, client, teacher_token):
        prob = self._create_problem(client, teacher_token)
        other_teacher = register_and_login(client, "other_teacher@test.com", "pass1234", "TEACHER")
        resp = client.delete(f"/api/problems/{prob['id']}", headers=auth_header(other_teacher))
        assert resp.status_code == 403

    def test_student_cannot_delete_problem(self, client, teacher_token, student_token):
        prob = self._create_problem(client, teacher_token)
        resp = client.delete(f"/api/problems/{prob['id']}", headers=auth_header(student_token))
        assert resp.status_code == 403

    def test_delete_nonexistent_problem_returns_404(self, client, teacher_token):
        resp = client.delete("/api/problems/99999", headers=auth_header(teacher_token))
        assert resp.status_code == 404

    def test_delete_problem_with_testcases_and_submissions_still_works(self, client, teacher_token, student_token):
        """Baseline: the cascade this endpoint already relied on (test_cases,
        submissions) must keep working alongside the new one."""
        from unittest.mock import patch
        prob = self._create_problem(client, teacher_token)
        client.post(f"/api/problems/{prob['id']}/testcases",
                    json={"input": "5 10", "expected_output": "15"}, headers=auth_header(teacher_token))
        with patch("app.services.submission_service.run_code", side_effect=lambda l, s, i: ("15\n", "", 0, False)):
            client.post("/api/submissions", json={
                "problem_id": prob["id"], "language": "python", "source_code": "print(15)",
            }, headers=auth_header(student_token))

        resp = client.delete(f"/api/problems/{prob['id']}", headers=auth_header(teacher_token))
        assert resp.status_code == 200, resp.text

    def test_delete_problem_attached_to_an_assignment(self, client, teacher_token):
        """
        Regression test: deleting a problem that's attached to an assignment
        used to raise an unhandled IntegrityError (SQLAlchemy tries to null
        the NOT NULL assignment_problems.problem_id since Problem had no
        cascade configured for that relationship) - it must now succeed and
        remove the problem from the assignment.
        """
        prob = self._create_problem(client, teacher_token)
        classroom = client.post("/api/classrooms", json={"name": "Class A"},
                                 headers=auth_header(teacher_token)).json()
        assignment = client.post("/api/assignments", json={
            "classroom_id": classroom["id"], "title": "Week 1",
            "problems": [{"problem_id": prob["id"], "points": 100}],
        }, headers=auth_header(teacher_token)).json()

        resp = client.delete(f"/api/problems/{prob['id']}", headers=auth_header(teacher_token))
        assert resp.status_code == 200, resp.text

        detail = client.get(f"/api/assignments/{assignment['id']}", headers=auth_header(teacher_token)).json()
        assert detail["problems"] == []

    def test_delete_problem_attached_to_a_learning_chapter(self, client, teacher_token, db_session):
        """Same regression as above, for the learning_chapter_problems join table."""
        from app.models.learning import LearningChapter, LearningChapterProblem
        from app.models.user import User

        prob = self._create_problem(client, teacher_token)
        teacher = db_session.query(User).filter(User.email == "teacher@test.com").first()

        chapter = LearningChapter(language="python", title="Test Chapter", order=1, created_by=teacher.id)
        db_session.add(chapter)
        db_session.flush()
        db_session.add(LearningChapterProblem(chapter_id=chapter.id, problem_id=prob["id"], order=0))
        db_session.commit()

        resp = client.delete(f"/api/problems/{prob['id']}", headers=auth_header(teacher_token))
        assert resp.status_code == 200, resp.text
        assert db_session.query(LearningChapterProblem).filter(
            LearningChapterProblem.problem_id == prob["id"]
        ).first() is None
