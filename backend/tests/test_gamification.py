"""
Gamification: Levels (derived from points) and Badges (persisted achievements).
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.badge import StudentBadge
from app.services.level_service import LevelService
from app.services.badge_service import BadgeService, BADGE_CATALOG


def register_and_login(client: TestClient, email: str, password: str, role: str) -> str:
    client.post("/api/auth/register", json={
        "name": email.split("@")[0], "email": email, "password": password, "role": role,
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


RUNNER_PATH = "app.services.submission_service.run_code"


def mock_correct(language, source_code, input_data):
    return "15\n", "", 0, False


def mock_wrong(language, source_code, input_data):
    return "999\n", "", 0, False


class TestLevelService:
    def test_level_one_at_zero_points(self):
        result = LevelService.compute_level(0)
        assert result["level"] == 1
        assert result["level_title"] == "Novice"
        assert result["points_in_level"] == 0
        assert result["level_progress_pct"] == 0.0

    def test_level_floors_at_one_for_negative_points(self):
        result = LevelService.compute_level(-50)
        assert result["level"] == 1
        assert result["points_in_level"] == 0

    def test_level_advances_at_threshold(self):
        per_level = settings.POINTS_PER_LEVEL
        just_under = LevelService.compute_level(per_level - 1)
        at_threshold = LevelService.compute_level(per_level)
        assert just_under["level"] == 1
        assert at_threshold["level"] == 2
        assert at_threshold["points_in_level"] == 0

    def test_level_progress_pct_midway(self):
        per_level = settings.POINTS_PER_LEVEL
        result = LevelService.compute_level(per_level // 2)
        assert result["level"] == 1
        assert result["level_progress_pct"] == 50.0

    def test_title_reflects_higher_level(self):
        # Level 6 maps to "Coder" per LEVEL_TITLES
        points = settings.POINTS_PER_LEVEL * 5  # level 6
        result = LevelService.compute_level(points)
        assert result["level"] == 6
        assert result["level_title"] == "Coder"


@pytest.fixture
def student_token(client: TestClient) -> str:
    return register_and_login(client, "badge_student@test.com", "pass1234", "STUDENT")


@pytest.fixture
def teacher_token(client: TestClient) -> str:
    return register_and_login(client, "badge_teacher@test.com", "pass1234", "TEACHER")


@pytest.fixture
def problem(client: TestClient, teacher_token: str) -> dict:
    prob = client.post("/api/problems", json={
        "title": "Add Two Numbers", "description": "Print sum", "difficulty": "EASY",
    }, headers=auth(teacher_token)).json()
    client.post(f"/api/problems/{prob['id']}/testcases",
                json={"input": "5 10", "expected_output": "15"}, headers=auth(teacher_token))
    return prob


class TestBadgeCatalogApi:
    def test_catalog_lists_all_badges(self, client, student_token):
        resp = client.get("/api/badges", headers=auth(student_token))
        assert resp.status_code == 200, resp.text
        codes = {b["code"] for b in resp.json()}
        assert codes == {b["code"] for b in BADGE_CATALOG}

    def test_catalog_requires_auth(self, client):
        resp = client.get("/api/badges")
        assert resp.status_code in (401, 403)

    def test_my_badges_all_locked_for_new_student(self, client, student_token):
        resp = client.get("/api/badges/me", headers=auth(student_token))
        assert resp.status_code == 200
        statuses = resp.json()
        assert {b["code"] for b in statuses} == {b["code"] for b in BADGE_CATALOG}
        assert all(b["earned"] is False for b in statuses)
        assert all(b["earned_at"] is None for b in statuses)
        assert all(b["unlock_hint"] for b in statuses)  # every locked badge explains how close they are

    def test_teacher_cannot_view_my_badges(self, client, teacher_token):
        resp = client.get("/api/badges/me", headers=auth(teacher_token))
        assert resp.status_code == 403


class TestBadgeAwarding:
    def test_first_accepted_submission_awards_first_blood(self, client, student_token, problem):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            resp = client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        codes = {b["code"] for b in data["newly_earned_badges"]}
        assert "FIRST_SOLVE" in codes

        my_badges = client.get("/api/badges/me", headers=auth(student_token)).json()
        first_solve = next(b for b in my_badges if b["code"] == "FIRST_SOLVE")
        assert first_solve["earned"] is True
        assert first_solve["earned_at"] is not None
        assert first_solve["unlock_hint"] is None

    def test_badge_not_awarded_twice(self, client, student_token, problem, db_session):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))
            second = client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))
        assert second.json()["newly_earned_badges"] == []

        from app.models.user import User
        student = db_session.query(User).filter(User.email == "badge_student@test.com").first()
        first_solve_rows = db_session.query(StudentBadge).filter(
            StudentBadge.student_id == student.id, StudentBadge.badge_code == "FIRST_SOLVE"
        ).count()
        assert first_solve_rows == 1

    def test_wrong_answer_does_not_award_first_solve(self, client, student_token, problem):
        with patch(RUNNER_PATH, side_effect=mock_wrong):
            resp = client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))
        assert resp.json()["newly_earned_badges"] == []

    def test_speed_demon_badge_awarded_with_fast_bonus(self, client, student_token, problem, db_session):
        def fast_correct(language, source_code, input_data):
            return "15\n", "", 0, False

        with patch(RUNNER_PATH, side_effect=fast_correct):
            resp = client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))
        # Execution is effectively instant in tests (mocked), so the fast-execution
        # bonus threshold is met and SPEED_DEMON should unlock alongside FIRST_SOLVE.
        codes = {b["code"] for b in resp.json()["newly_earned_badges"]}
        assert "SPEED_DEMON" in codes

    def test_unlock_hint_reflects_partial_progress(self, client, student_token, problem):
        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))

        my_badges = client.get("/api/badges/me", headers=auth(student_token)).json()
        solved_10 = next(b for b in my_badges if b["code"] == "SOLVED_10")
        assert solved_10["earned"] is False
        assert solved_10["unlock_hint"] == "1/10 problems solved"

    def test_evaluate_and_award_is_idempotent_at_service_level(self, db_session, client, student_token, problem):
        from app.models.user import User
        student = db_session.query(User).filter(User.email == "badge_student@test.com").first()

        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post("/api/submissions", json={
                "problem_id": problem["id"], "language": "python", "source_code": "x",
            }, headers=auth(student_token))

        # Calling the service directly again should award nothing new
        second_call = BadgeService.evaluate_and_award(db_session, student.id)
        assert second_call == []

        count = db_session.query(StudentBadge).filter(StudentBadge.student_id == student.id).count()
        assert count >= 1
