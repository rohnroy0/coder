"""
Teacher → Student Performance Profile tests.

Covers the profile content, and the security rules:
- only a teacher who owns the classroom can view its students
- the student must be enrolled in that classroom
- students cannot use these endpoints
- hidden test cases, reference solutions and AI hint text never appear in the profile
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.models.feedback import AIFeedback, ErrorCategory
from app.models.problem import Problem

RUNNER_PATH = "app.services.submission_service.run_code"
HIDDEN_EXPECTED = "987654321"
REFERENCE_SOLUTION = "print('REFERENCE_SOLUTION_MARKER')"
HINT_TEXT = "SECRET_HINT_TEXT_MARKER"
CORRECT_CODE = "a,b=map(int,input().split());print(a*b if False else a+b)"
WRONG_CODE = "print(0)"


def register_and_login(client: TestClient, email: str, role: str, name: str) -> str:
    client.post("/api/auth/register", json={"name": name, "email": email, "password": "pass1234", "role": role})
    resp = client.post("/api/auth/login", json={"email": email, "password": "pass1234"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def fake_runner(language, source_code, input_data):
    # Correct code prints the hidden expected output; anything else prints a wrong answer.
    if source_code == CORRECT_CODE:
        return HIDDEN_EXPECTED + "\n", "", 0, False
    return "0\n", "", 0, False


@pytest.fixture
def setup(client: TestClient, db_session):
    t1 = register_and_login(client, "t1@profile.com", "TEACHER", "Teacher One")
    t2 = register_and_login(client, "t2@profile.com", "TEACHER", "Teacher Two")
    s1 = register_and_login(client, "rahul@profile.com", "STUDENT", "Rahul Kumar")
    s2 = register_and_login(client, "anu@profile.com", "STUDENT", "Anu")

    cls_a = client.post("/api/classrooms", json={"name": "Python Programming"}, headers=auth(t1)).json()
    cls_b = client.post("/api/classrooms", json={"name": "Other Class"}, headers=auth(t2)).json()
    client.post("/api/classrooms/join", json={"join_code": cls_a["join_code"]}, headers=auth(s1))
    client.post("/api/classrooms/join", json={"join_code": cls_b["join_code"]}, headers=auth(s2))

    prob = client.post("/api/problems", json={
        "title": "Two Sum", "description": "Add numbers", "difficulty": "EASY", "topic": "arrays",
    }, headers=auth(t1)).json()
    client.post(f"/api/problems/{prob['id']}/testcases",
                json={"input": "1 2", "expected_output": HIDDEN_EXPECTED}, headers=auth(t1))
    # Give the problem a reference solution, as AI-generated problems have
    db_prob = db_session.query(Problem).filter(Problem.id == prob["id"]).first()
    db_prob.reference_solution = REFERENCE_SOLUTION
    db_session.commit()

    asg = client.post("/api/assignments", json={
        "classroom_id": cls_a["id"], "title": "Arrays Assignment",
        "problems": [{"problem_id": prob["id"], "points": 100}],
    }, headers=auth(t1)).json()
    client.post(f"/api/assignments/{asg['id']}/publish", headers=auth(t1))

    s1_id = client.get("/api/auth/me", headers=auth(s1)).json()["id"]
    s2_id = client.get("/api/auth/me", headers=auth(s2)).json()["id"]

    with patch(RUNNER_PATH, side_effect=fake_runner):
        wrong = client.post("/api/submissions", json={
            "problem_id": prob["id"], "language": "python", "source_code": WRONG_CODE, "assignment_id": asg["id"],
        }, headers=auth(s1)).json()
        right = client.post("/api/submissions", json={
            "problem_id": prob["id"], "language": "python", "source_code": CORRECT_CODE, "assignment_id": asg["id"],
        }, headers=auth(s1)).json()
        other = client.post("/api/submissions", json={
            "problem_id": prob["id"], "language": "python", "source_code": WRONG_CODE,
        }, headers=auth(s2)).json()

    # An AI tutor hint on the wrong submission (inserted directly; no Ollama in tests)
    db_session.add(AIFeedback(
        submission_id=wrong["id"], student_id=s1_id, hint_level=1, summary=HINT_TEXT,
        error_type=ErrorCategory.LOGIC_ERROR, explanation=HINT_TEXT, hint=HINT_TEXT, next_step=HINT_TEXT,
    ))
    db_session.commit()

    return {
        "t1": t1, "t2": t2, "s1": s1, "s2": s2, "s1_id": s1_id, "s2_id": s2_id,
        "cls_a": cls_a, "cls_b": cls_b, "prob": prob, "asg": asg,
        "wrong": wrong, "right": right, "other": other,
    }


def profile_url(d, classroom_key="cls_a", student_key="s1_id"):
    return f"/api/classrooms/{d[classroom_key]['id']}/students/{d[student_key]}/profile"


class TestRoster:
    def test_roster_lists_students_with_rank_points_accuracy_progress(self, client, setup):
        resp = client.get(f"/api/classrooms/{setup['cls_a']['id']}/students", headers=auth(setup["t1"]))
        assert resp.status_code == 200, resp.text
        roster = resp.json()
        assert len(roster) == 1
        row = roster[0]
        assert row["name"] == "Rahul Kumar"
        assert row["email"] == "rahul@profile.com"
        assert row["rank"] == 1
        assert row["accuracy"] == 50.0
        assert row["progress"] == 100.0
        assert row["points"] > 0

    def test_other_teacher_cannot_list_roster(self, client, setup):
        resp = client.get(f"/api/classrooms/{setup['cls_a']['id']}/students", headers=auth(setup["t2"]))
        assert resp.status_code == 403

    def test_student_cannot_list_roster(self, client, setup):
        resp = client.get(f"/api/classrooms/{setup['cls_a']['id']}/students", headers=auth(setup["s1"]))
        assert resp.status_code == 403


class TestProfileContent:
    def test_full_profile(self, client, setup):
        resp = client.get(profile_url(setup), headers=auth(setup["t1"]))
        assert resp.status_code == 200, resp.text
        p = resp.json()

        h = p["header"]
        assert h["name"] == "Rahul Kumar" and h["email"] == "rahul@profile.com"
        assert h["classroom_name"] == "Python Programming"
        assert h["rank"] == 1 and h["total_students"] == 1

        o = p["overall"]
        assert o["problems_solved"] == 1 and o["problems_attempted"] == 1
        assert o["submission_accuracy"] == 50.0 and o["completion_rate"] == 100.0
        assert o["assignments_completed"] == 1 and o["assignments_total"] == 1
        assert o["total_points"] == h["total_points"] == p["leaderboard"]["points"]

        a = p["assignments"][0]
        assert a["title"] == "Arrays Assignment" and a["progress_status"] == "COMPLETED"
        assert a["completed_problems"] == 1 and a["total_problems"] == 1
        assert a["score"] == 100 and a["max_score"] == 100 and a["percentage"] == 100.0
        assert a["attempts"] == 2
        assert a["problems"][0]["solved"] is True

        pr = p["problems"][0]
        assert pr["title"] == "Two Sum" and pr["topic"] == "Arrays" and pr["difficulty"] == "EASY"
        assert pr["attempts"] == 2
        assert pr["first_result"] == "WRONG_ANSWER" and pr["latest_result"] == "ACCEPTED" and pr["best_result"] == "ACCEPTED"
        assert pr["hints_requested"] == 1 and pr["completion_status"] == "Solved"
        assert pr["assignments"] == ["Arrays Assignment"]

        subs = p["submissions"]
        assert [s["attempt_number"] for s in subs] == [2, 1]  # newest first
        assert subs[0]["result"] == "ACCEPTED" and subs[0]["assignment"] == "Arrays Assignment"
        assert subs[0]["memory_used_mb"] is None

        ai = p["ai_tutor"]
        assert ai["total_hints"] == 1 and ai["most_common_error"] == "LOGIC_ERROR"
        assert ai["hints_by_problem"] == [{"name": "Two Sum", "count": 1}]
        assert ai["progression"][0]["levels"] == [1]

        err = p["errors"]["ai_categories"][0]
        assert err["category"] == "LOGIC_ERROR" and err["percentage"] == 100.0 and err["topics"] == ["Arrays"]
        assert {"name": "WRONG_ANSWER", "count": 1} in p["errors"]["judge_outcomes"]

        assert p["topics"][0]["topic"] == "Arrays" and p["topics"][0]["classification"] == "Developing"
        assert p["trends"] and p["trends"][-1]["problems_solved"] == 1
        assert p["points_history"] and p["points_history"][0]["running_total"] == o["total_points"]

        types = {a["type"] for a in p["recent_activity"]}
        assert {"JOINED", "ACCEPTED", "WRONG_ANSWER", "HINT", "ASSIGNMENT_STARTED", "ASSIGNMENT_COMPLETED"} <= types

        assert p["summary"]["developing_topics"] == ["Arrays"]
        assert any("Logic error" in line for line in p["summary"]["lines"])
        assert p["limitations"]

    def test_profile_never_leaks_hidden_data(self, client, setup):
        resp = client.get(profile_url(setup), headers=auth(setup["t1"]))
        body = resp.text
        assert HIDDEN_EXPECTED not in body  # hidden test case output
        assert "REFERENCE_SOLUTION_MARKER" not in body
        assert HINT_TEXT not in body  # AI tutor text is aggregated, not exposed
        assert CORRECT_CODE not in body  # source code only via the single-submission endpoint
        assert "reference_solution" not in body and "expected_output" not in body

    def test_teacher_can_view_submission_code(self, client, setup):
        url = f"/api/classrooms/{setup['cls_a']['id']}/students/{setup['s1_id']}/submissions/{setup['right']['id']}"
        resp = client.get(url, headers=auth(setup["t1"]))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["source_code"] == CORRECT_CODE
        assert data["attempt_number"] == 2 and data["result"] == "ACCEPTED"
        assert HIDDEN_EXPECTED not in resp.text and "REFERENCE_SOLUTION_MARKER" not in resp.text


class TestProfileSecurity:
    def test_other_teacher_cannot_view_profile(self, client, setup):
        assert client.get(profile_url(setup), headers=auth(setup["t2"])).status_code == 403

    def test_teacher_cannot_view_student_outside_classroom(self, client, setup):
        # Anu is enrolled only in teacher 2's class
        assert client.get(profile_url(setup, "cls_a", "s2_id"), headers=auth(setup["t1"])).status_code == 404
        # Teacher 2 cannot reach Rahul through their own classroom either
        assert client.get(profile_url(setup, "cls_b", "s1_id"), headers=auth(setup["t2"])).status_code == 404

    def test_students_cannot_view_profiles(self, client, setup):
        assert client.get(profile_url(setup), headers=auth(setup["s1"])).status_code == 403  # even their own
        assert client.get(profile_url(setup), headers=auth(setup["s2"])).status_code == 403
        code_url = f"/api/classrooms/{setup['cls_a']['id']}/students/{setup['s1_id']}/submissions/{setup['right']['id']}"
        assert client.get(code_url, headers=auth(setup["s2"])).status_code == 403

    def test_cannot_read_other_students_code_via_own_student(self, client, setup):
        # Anu's submission id requested through Rahul's (authorised) profile path
        url = f"/api/classrooms/{setup['cls_a']['id']}/students/{setup['s1_id']}/submissions/{setup['other']['id']}"
        assert client.get(url, headers=auth(setup["t1"])).status_code == 404

    def test_other_teacher_cannot_read_code(self, client, setup):
        url = f"/api/classrooms/{setup['cls_a']['id']}/students/{setup['s1_id']}/submissions/{setup['right']['id']}"
        assert client.get(url, headers=auth(setup["t2"])).status_code == 403

    def test_unauthenticated_rejected(self, client, setup):
        assert client.get(profile_url(setup)).status_code in (401, 403)

    def test_unknown_classroom(self, client, setup):
        assert client.get(f"/api/classrooms/99999/students/{setup['s1_id']}/profile", headers=auth(setup["t1"])).status_code == 404

    def test_profile_is_read_only(self, client, setup):
        for method in ("post", "put", "patch", "delete"):
            resp = getattr(client, method)(profile_url(setup), headers=auth(setup["t1"]))
            assert resp.status_code == 405, method


class TestCrossClassroomScoping:
    """
    A student can join several classrooms taught by the same teacher. Viewing
    their profile from one classroom must reflect only that classroom's
    assignments - not the other classroom's work, and not unassigned practice.
    """

    @pytest.fixture
    def two_classrooms(self, client: TestClient):
        teacher = register_and_login(client, "t@multi.com", "TEACHER", "Teacher")
        student = register_and_login(client, "s@multi.com", "STUDENT", "Student")

        cls_a = client.post("/api/classrooms", json={"name": "Class A"}, headers=auth(teacher)).json()
        cls_b = client.post("/api/classrooms", json={"name": "Class B"}, headers=auth(teacher)).json()
        client.post("/api/classrooms/join", json={"join_code": cls_a["join_code"]}, headers=auth(student))
        client.post("/api/classrooms/join", json={"join_code": cls_b["join_code"]}, headers=auth(student))

        # Two distinct problems: scoring awards base ACCEPTED points once per
        # problem regardless of classroom (anti point-farming), so reusing the
        # same problem in both assignments would confound that with classroom
        # scoping. Separate problems isolate the two concerns.
        def make_problem(title):
            prob = client.post("/api/problems", json={
                "title": title, "description": "desc", "difficulty": "EASY", "topic": "basics",
            }, headers=auth(teacher)).json()
            client.post(f"/api/problems/{prob['id']}/testcases",
                        json={"input": "1 2", "expected_output": "3"}, headers=auth(teacher))
            return prob

        prob_a = make_problem("Problem A")
        prob_b = make_problem("Problem B")

        asg_a = client.post("/api/assignments", json={
            "classroom_id": cls_a["id"], "title": "Assignment A",
            "problems": [{"problem_id": prob_a["id"], "points": 100}],
        }, headers=auth(teacher)).json()
        client.post(f"/api/assignments/{asg_a['id']}/publish", headers=auth(teacher))

        asg_b = client.post("/api/assignments", json={
            "classroom_id": cls_b["id"], "title": "Assignment B",
            "problems": [{"problem_id": prob_b["id"], "points": 100}],
        }, headers=auth(teacher)).json()
        client.post(f"/api/assignments/{asg_b['id']}/publish", headers=auth(teacher))

        student_id = client.get("/api/auth/me", headers=auth(student)).json()["id"]

        def correct(language, source_code, input_data):
            a, b = map(int, input_data.split())
            return f"{a + b}\n", "", 0, False

        with patch(RUNNER_PATH, side_effect=correct):
            sub_a = client.post("/api/submissions", json={
                "problem_id": prob_a["id"], "language": "python", "source_code": "a",
                "assignment_id": asg_a["id"],
            }, headers=auth(student)).json()
            sub_b = client.post("/api/submissions", json={
                "problem_id": prob_b["id"], "language": "python", "source_code": "b",
                "assignment_id": asg_b["id"],
            }, headers=auth(student)).json()
            practice = client.post("/api/submissions", json={
                "problem_id": prob_a["id"], "language": "python", "source_code": "c",
            }, headers=auth(student)).json()

        return {
            "teacher": teacher, "student": student, "student_id": student_id,
            "cls_a": cls_a, "cls_b": cls_b, "sub_a": sub_a, "sub_b": sub_b, "practice": practice,
        }

    def test_profile_from_classroom_a_excludes_classroom_b_and_practice(self, client, two_classrooms):
        d = two_classrooms
        resp = client.get(
            f"/api/classrooms/{d['cls_a']['id']}/students/{d['student_id']}/profile",
            headers=auth(d["teacher"]),
        )
        assert resp.status_code == 200, resp.text
        p = resp.json()

        # Only the one submission made under Assignment A counts here
        assert p["overall"]["total_submissions"] == 1
        assert p["overall"]["problems_solved"] == 1
        assert p["overall"]["total_points"] == p["leaderboard"]["points"] > 0
        assert len(p["submissions"]) == 1
        assert p["submissions"][0]["submission_id"] == d["sub_a"]["id"]
        assert [a["title"] for a in p["assignments"]] == ["Assignment A"]

    def test_profile_from_classroom_b_excludes_classroom_a_and_practice(self, client, two_classrooms):
        d = two_classrooms
        resp = client.get(
            f"/api/classrooms/{d['cls_b']['id']}/students/{d['student_id']}/profile",
            headers=auth(d["teacher"]),
        )
        assert resp.status_code == 200, resp.text
        p = resp.json()

        assert p["overall"]["total_submissions"] == 1
        assert len(p["submissions"]) == 1
        assert p["submissions"][0]["submission_id"] == d["sub_b"]["id"]
        assert [a["title"] for a in p["assignments"]] == ["Assignment B"]

    def test_leaderboard_points_scoped_per_classroom(self, client, two_classrooms):
        d = two_classrooms
        lb_a = client.get(f"/api/analytics/classroom/{d['cls_a']['id']}/leaderboard",
                           headers=auth(d["teacher"])).json()
        lb_b = client.get(f"/api/analytics/classroom/{d['cls_b']['id']}/leaderboard",
                           headers=auth(d["teacher"])).json()
        # Same student in both, but each classroom only counts its own assignment's points
        assert lb_a[0]["points"] == lb_b[0]["points"] > 0
        assert lb_a[0]["problems_solved"] == 1
        assert lb_b[0]["problems_solved"] == 1

    def test_cannot_view_other_classrooms_submission_code(self, client, two_classrooms):
        d = two_classrooms
        # Classroom A's teacher cannot read the code the student submitted under
        # Classroom B's assignment, or their unassigned practice submission,
        # even though it's the same student enrolled in classroom A.
        for submission_id in (d["sub_b"]["id"], d["practice"]["id"]):
            url = f"/api/classrooms/{d['cls_a']['id']}/students/{d['student_id']}/submissions/{submission_id}"
            assert client.get(url, headers=auth(d["teacher"])).status_code == 404

        url = f"/api/classrooms/{d['cls_a']['id']}/students/{d['student_id']}/submissions/{d['sub_a']['id']}"
        assert client.get(url, headers=auth(d["teacher"])).status_code == 200
