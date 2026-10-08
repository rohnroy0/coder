"""
Self-paced learning paths (Duolingo-style chapters per language).

Chapters are fixed, built-in curriculum content (see
app/core/seed_learning_curriculum.py), not teacher-editable - so these tests
seed LearningChapter/LearningChapterProblem rows directly via the ORM, the
same way the real seed script does, rather than through any API.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.learning import LearningChapter, LearningChapterProblem


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
CORRECT_CODE = "a,b=map(int,input().split())\nprint(a+b)"
WRONG_CODE = "print(0)"


def mock_correct(language, source_code, input_data):
    if source_code == WRONG_CODE:
        return "0\n", "", 0, False
    a, b = map(int, input_data.split())
    return f"{a + b}\n", "", 0, False


@pytest.fixture
def teacher_token(client: TestClient) -> str:
    return register_and_login(client, "learn_teacher@test.com", "pass1234", "TEACHER")


@pytest.fixture
def student_token(client: TestClient) -> str:
    return register_and_login(client, "learn_student@test.com", "pass1234", "STUDENT")


@pytest.fixture
def two_python_problems(client: TestClient, teacher_token: str):
    probs = []
    for i in range(2):
        prob = client.post("/api/problems", json={
            "title": f"Problem {i}", "description": "Add two ints", "difficulty": "EASY",
        }, headers=auth(teacher_token)).json()
        client.post(f"/api/problems/{prob['id']}/testcases",
                    json={"input": "1 2", "expected_output": "3"}, headers=auth(teacher_token))
        probs.append(prob)
    return probs


def make_chapter(db_session, teacher_id, language, title, order, problems):
    """Seeds one LearningChapter + its LearningChapterProblem rows directly, as
    the real curriculum seed script does - no authoring API exists for this."""
    chapter = LearningChapter(language=language, title=title, order=order, created_by=teacher_id)
    db_session.add(chapter)
    db_session.flush()
    for i, prob in enumerate(problems):
        db_session.add(LearningChapterProblem(chapter_id=chapter.id, problem_id=prob["id"], order=i))
    db_session.commit()
    db_session.refresh(chapter)
    return chapter


class TestLearningPathProgress:
    def test_first_chapter_unlocked_second_locked(self, client, teacher_token, student_token, two_python_problems, db_session):
        from app.models.user import User
        teacher = db_session.query(User).filter(User.email == "learn_teacher@test.com").first()
        p1, p2 = two_python_problems

        make_chapter(db_session, teacher.id, "python", "Chapter 1", 1, [p1])
        make_chapter(db_session, teacher.id, "python", "Chapter 2", 2, [p2])

        resp = client.get("/api/learning/path/python", headers=auth(student_token))
        assert resp.status_code == 200, resp.text
        path = resp.json()
        assert len(path) == 2
        assert path[0]["title"] == "Chapter 1" and path[0]["is_unlocked"] is True
        assert path[1]["title"] == "Chapter 2" and path[1]["is_unlocked"] is False

    def test_completing_chapter_unlocks_next(self, client, teacher_token, student_token, two_python_problems, db_session):
        from app.models.user import User
        teacher = db_session.query(User).filter(User.email == "learn_teacher@test.com").first()
        p1, p2 = two_python_problems

        ch1 = make_chapter(db_session, teacher.id, "python", "Chapter 1", 1, [p1])
        make_chapter(db_session, teacher.id, "python", "Chapter 2", 2, [p2])

        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post("/api/submissions", json={
                "problem_id": p1["id"], "language": "python", "source_code": CORRECT_CODE,
            }, headers=auth(student_token))

        path = client.get("/api/learning/path/python", headers=auth(student_token)).json()
        assert path[0]["is_completed"] is True
        assert path[0]["completed_problems"] == 1
        assert path[1]["is_unlocked"] is True

        # Chapter detail for the now-unlocked chapter should be reachable
        detail = client.get(f"/api/learning/chapters/{ch1.id}/detail", headers=auth(student_token))
        assert detail.status_code == 200

    def test_locked_chapter_detail_returns_403(self, client, teacher_token, student_token, two_python_problems, db_session):
        from app.models.user import User
        teacher = db_session.query(User).filter(User.email == "learn_teacher@test.com").first()
        p1, p2 = two_python_problems

        make_chapter(db_session, teacher.id, "python", "Chapter 1", 1, [p1])
        ch2 = make_chapter(db_session, teacher.id, "python", "Chapter 2", 2, [p2])

        resp = client.get(f"/api/learning/chapters/{ch2.id}/detail", headers=auth(student_token))
        assert resp.status_code == 403

    def test_wrong_answer_does_not_complete_chapter(self, client, teacher_token, student_token, two_python_problems, db_session):
        from app.models.user import User
        teacher = db_session.query(User).filter(User.email == "learn_teacher@test.com").first()
        p1, _ = two_python_problems

        make_chapter(db_session, teacher.id, "python", "Chapter 1", 1, [p1])

        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post("/api/submissions", json={
                "problem_id": p1["id"], "language": "python", "source_code": WRONG_CODE,
            }, headers=auth(student_token))

        path = client.get("/api/learning/path/python", headers=auth(student_token)).json()
        assert path[0]["is_completed"] is False

    def test_languages_are_independent(self, client, teacher_token, student_token, two_python_problems, db_session):
        from app.models.user import User
        teacher = db_session.query(User).filter(User.email == "learn_teacher@test.com").first()
        p1, _ = two_python_problems

        c_prob = client.post("/api/problems", json={
            "title": "C Problem", "description": "d", "difficulty": "EASY", "language": "c",
        }, headers=auth(teacher_token)).json()
        client.post(f"/api/problems/{c_prob['id']}/testcases",
                    json={"input": "1 2", "expected_output": "3"}, headers=auth(teacher_token))

        make_chapter(db_session, teacher.id, "python", "Py Chapter 1", 1, [p1])
        make_chapter(db_session, teacher.id, "c", "C Chapter 1", 1, [c_prob])

        # Solving the Python chapter's problem must not affect the C path
        with patch(RUNNER_PATH, side_effect=mock_correct):
            client.post("/api/submissions", json={
                "problem_id": p1["id"], "language": "python", "source_code": CORRECT_CODE,
            }, headers=auth(student_token))

        python_path = client.get("/api/learning/path/python", headers=auth(student_token)).json()
        c_path = client.get("/api/learning/path/c", headers=auth(student_token)).json()
        assert python_path[0]["is_completed"] is True
        assert c_path[0]["is_completed"] is False

    def test_empty_path_for_language_with_no_chapters(self, client, student_token):
        resp = client.get("/api/learning/path/cpp", headers=auth(student_token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_unsupported_language_rejected(self, client, student_token):
        resp = client.get("/api/learning/path/java", headers=auth(student_token))
        assert resp.status_code == 400

    def test_teacher_cannot_view_student_path_endpoint(self, client, teacher_token):
        resp = client.get("/api/learning/path/python", headers=auth(teacher_token))
        assert resp.status_code == 403

    def test_unknown_chapter_detail_404s(self, client, student_token):
        resp = client.get("/api/learning/chapters/99999/detail", headers=auth(student_token))
        assert resp.status_code == 404


def _expected_chapter_titles(language):
    from app.core.seed_learning_curriculum import full_curriculum_for
    return [c["title"] for c in full_curriculum_for(language)]


def _expected_problem_count(language):
    from app.core.seed_learning_curriculum import full_curriculum_for
    return sum(len(c["problems"]) for c in full_curriculum_for(language))


class TestCurriculumSeeding:
    def test_seed_covers_all_languages_with_their_own_chapter_set(self, db_session):
        from app.core.seed_learning_curriculum import seed_learning_curriculum, LANGUAGES
        from app.models.problem import Problem

        seed_learning_curriculum(db_session)

        for language in LANGUAGES:
            chapters = db_session.query(LearningChapter).filter(LearningChapter.language == language).order_by(
                LearningChapter.order
            ).all()
            assert [c.title for c in chapters] == _expected_chapter_titles(language)
            assert [c.order for c in chapters] == list(range(1, len(chapters) + 1))

        total_problems = sum(_expected_problem_count(l) for l in LANGUAGES)
        assert db_session.query(Problem).count() == total_problems

    def test_seed_is_idempotent(self, db_session):
        from app.core.seed_learning_curriculum import seed_learning_curriculum

        seed_learning_curriculum(db_session)
        chapter_count_first = db_session.query(LearningChapter).count()

        # Running it again must not duplicate anything or touch anything
        seed_learning_curriculum(db_session)
        assert db_session.query(LearningChapter).count() == chapter_count_first

    def test_stale_system_curriculum_gets_replaced(self, db_session):
        """Simulates the curriculum module's content having changed since the
        last seed: a stale system-owned chapter set must be fully replaced
        (and reordered correctly), not incrementally patched."""
        from app.core.seed_learning_curriculum import seed_learning_curriculum, SYSTEM_TEACHER_EMAIL
        from app.models.user import User
        from app.models.problem import Problem

        # Simulate a previous, now-outdated seed: one system-owned chapter
        # with a title that doesn't exist in the current curriculum at all.
        system_teacher = User(
            name="Learning Path Curriculum", email=SYSTEM_TEACHER_EMAIL,
            password_hash="x", role="TEACHER",
        )
        db_session.add(system_teacher)
        db_session.commit()

        stale_prob = Problem(title="Stale", description="d", difficulty="EASY", status="VERIFIED",
                              language="python", created_by=system_teacher.id)
        db_session.add(stale_prob)
        db_session.commit()
        make_chapter(db_session, system_teacher.id, "python", "An Old Removed Chapter", 1, [{"id": stale_prob.id}])

        seed_learning_curriculum(db_session)

        titles = [c.title for c in db_session.query(LearningChapter).filter(
            LearningChapter.language == "python"
        ).order_by(LearningChapter.order).all()]
        assert titles == _expected_chapter_titles("python")
        assert "An Old Removed Chapter" not in titles
        assert db_session.query(Problem).filter(Problem.title == "Stale").first() is None

    def test_reseeding_never_touches_a_real_teachers_content(self, db_session, teacher_token, two_python_problems):
        """A teacher's own chapter/problem must survive a system curriculum
        replacement untouched."""
        from app.models.user import User
        from app.models.problem import Problem
        teacher = db_session.query(User).filter(User.email == "learn_teacher@test.com").first()
        teachers_chapter = make_chapter(db_session, teacher.id, "python", "My Own Chapter", 999, [two_python_problems[0]])

        from app.core.seed_learning_curriculum import seed_learning_curriculum
        seed_learning_curriculum(db_session)

        db_session.refresh(teachers_chapter)
        assert teachers_chapter.title == "My Own Chapter"
        assert teachers_chapter.problems[0].problem_id == two_python_problems[0]["id"]
        assert db_session.query(Problem).filter(Problem.id == two_python_problems[0]["id"]).first() is not None

    def test_seeded_chapters_are_sequential_and_locked_correctly(self, db_session, client, student_token):
        from app.core.seed_learning_curriculum import seed_learning_curriculum
        seed_learning_curriculum(db_session)

        resp = client.get("/api/learning/path/python", headers=auth(student_token))
        assert resp.status_code == 200, resp.text
        path = resp.json()
        assert path[0]["is_unlocked"] is True
        assert all(not c["is_unlocked"] for c in path[1:])
        assert [c["order"] for c in path] == sorted(c["order"] for c in path)

    def test_c_and_cpp_get_pointers_chapter_python_does_not(self, db_session, client, student_token):
        from app.core.seed_learning_curriculum import seed_learning_curriculum
        seed_learning_curriculum(db_session)

        py_titles = [c["title"] for c in client.get("/api/learning/path/python", headers=auth(student_token)).json()]
        c_titles = [c["title"] for c in client.get("/api/learning/path/c", headers=auth(student_token)).json()]
        cpp_titles = [c["title"] for c in client.get("/api/learning/path/cpp", headers=auth(student_token)).json()]

        assert "Pointers & Memory" not in py_titles
        assert "Pointers & Memory" in c_titles
        assert "Pointers & Memory" in cpp_titles

        assert "Object-Oriented Programming" in py_titles
        assert "Object-Oriented Programming" not in c_titles
        assert "Object-Oriented Programming" in cpp_titles
