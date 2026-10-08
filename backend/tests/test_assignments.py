from app.core.time import utcnow
from datetime import datetime, timedelta
import pytest
from fastapi import status
from app.models.user import User, UserRole
from app.models.classroom import Classroom, ClassroomMember
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus, TestCase
from app.models.assignment import Assignment, AssignmentStatus, AssignmentProgressStatus
from app.core.security import create_access_token, get_password_hash


def create_test_user(db, email, role=UserRole.STUDENT, name="Test User"):
    user = User(
        email=email,
        password_hash=get_password_hash("password123"),
        name=name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(user):
    role_str = user.role.value if hasattr(user.role, 'value') else user.role
    token = create_access_token(subject=user.id, role=role_str)
    return {"Authorization": f"Bearer {token}"}


def setup_assignment_test_environment(db):
    teacher = create_test_user(db, "teacher_assign@test.com", UserRole.TEACHER, "Teacher Assign")
    student1 = create_test_user(db, "student1_assign@test.com", UserRole.STUDENT, "Student 1")
    student2 = create_test_user(db, "student2_assign@test.com", UserRole.STUDENT, "Student 2")

    classroom = Classroom(
        name="CS101 Assignments",
        description="Assignment Testing Classroom",
        join_code="ASSGN1",
        teacher_id=teacher.id
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    # Enroll students
    db.add(ClassroomMember(classroom_id=classroom.id, student_id=student1.id))
    db.add(ClassroomMember(classroom_id=classroom.id, student_id=student2.id))
    db.commit()

    # Verified problem 1
    prob1 = Problem(
        title="Sum Two Numbers",
        description="Return sum of a and b",
        difficulty=ProblemDifficulty.EASY,
        status=ProblemStatus.VERIFIED,
        created_by=teacher.id
    )
    db.add(prob1)
    db.commit()
    db.refresh(prob1)

    tc1 = TestCase(
        problem_id=prob1.id,
        input="3 5\n",
        expected_output="8"
    )
    db.add(tc1)

    # Verified problem 2
    prob2 = Problem(
        title="Multiply Two Numbers",
        description="Return product of a and b",
        difficulty=ProblemDifficulty.MEDIUM,
        status=ProblemStatus.VERIFIED,
        created_by=teacher.id
    )
    db.add(prob2)
    db.commit()
    db.refresh(prob2)

    tc2 = TestCase(
        problem_id=prob2.id,
        input="3 5\n",
        expected_output="15"
    )
    db.add(tc2)

    # Unverified problem
    prob_unverified = Problem(
        title="Unverified Problem",
        description="Draft problem",
        difficulty=ProblemDifficulty.EASY,
        status=ProblemStatus.DRAFT,
        created_by=teacher.id
    )
    db.add(prob_unverified)
    db.commit()
    db.refresh(prob_unverified)

    return {
        "teacher": teacher,
        "student1": student1,
        "student2": student2,
        "classroom": classroom,
        "prob1": prob1,
        "prob2": prob2,
        "prob_unverified": prob_unverified
    }


def test_create_assignment_success(client, db_session):
    env = setup_assignment_test_environment(db_session)
    headers = get_auth_headers(env["teacher"])

    payload = {
        "classroom_id": env["classroom"].id,
        "title": "Homework 1",
        "description": "First problem set",
        "due_at": (utcnow() + timedelta(days=7)).isoformat(),
        "problems": [
            {"problem_id": env["prob1"].id, "points": 50, "order": 1},
            {"problem_id": env["prob2"].id, "points": 100, "order": 2}
        ]
    }

    res = client.post("/api/assignments", json=payload, headers=headers)
    assert res.status_code == status.HTTP_201_CREATED
    data = res.json()
    assert data["title"] == "Homework 1"
    assert data["status"] == "DRAFT"
    assert data["total_points"] == 150
    assert len(data["problems"]) == 2


def test_create_assignment_rejects_unverified_problem(client, db_session):
    env = setup_assignment_test_environment(db_session)
    headers = get_auth_headers(env["teacher"])

    payload = {
        "classroom_id": env["classroom"].id,
        "title": "Invalid Homework",
        "problems": [
            {"problem_id": env["prob_unverified"].id, "points": 50, "order": 1}
        ]
    }

    res = client.post("/api/assignments", json=payload, headers=headers)
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Only verified problems can be added to assignments" in res.json()["detail"]


def test_create_assignment_unauthorized_teacher(client, db_session):
    env = setup_assignment_test_environment(db_session)
    other_teacher = create_test_user(db_session, "other_teacher@test.com", UserRole.TEACHER)
    headers = get_auth_headers(other_teacher)

    payload = {
        "classroom_id": env["classroom"].id,
        "title": "Stolen Assignment",
        "problems": [{"problem_id": env["prob1"].id, "points": 50, "order": 1}]
    }

    res = client.post("/api/assignments", json=payload, headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_student_cannot_create_assignment(client, db_session):
    env = setup_assignment_test_environment(db_session)
    headers = get_auth_headers(env["student1"])

    payload = {
        "classroom_id": env["classroom"].id,
        "title": "Student Assignment",
        "problems": [{"problem_id": env["prob1"].id, "points": 50, "order": 1}]
    }

    res = client.post("/api/assignments", json=payload, headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_assignment_lifecycle_and_student_visibility(client, db_session):
    env = setup_assignment_test_environment(db_session)
    t_headers = get_auth_headers(env["teacher"])
    s_headers = get_auth_headers(env["student1"])

    # 1. Create DRAFT assignment
    res_create = client.post("/api/assignments", json={
        "classroom_id": env["classroom"].id,
        "title": "Quiz 1",
        "problems": [{"problem_id": env["prob1"].id, "points": 100, "order": 1}]
    }, headers=t_headers)
    assign_id = res_create.json()["id"]

    # Student cannot see DRAFT assignment in list or detail
    res_s_list = client.get(f"/api/assignments/classroom/{env['classroom'].id}", headers=s_headers)
    assert res_s_list.status_code == status.HTTP_200_OK
    assert len(res_s_list.json()) == 0

    res_s_detail = client.get(f"/api/assignments/{assign_id}", headers=s_headers)
    assert res_s_detail.status_code == status.HTTP_403_FORBIDDEN

    # 2. Teacher publishes assignment
    res_pub = client.post(f"/api/assignments/{assign_id}/publish", headers=t_headers)
    assert res_pub.status_code == status.HTTP_200_OK
    assert res_pub.json()["status"] == "PUBLISHED"

    # Student can now see assignment
    res_s_list2 = client.get(f"/api/assignments/classroom/{env['classroom'].id}", headers=s_headers)
    assert res_s_list2.status_code == status.HTTP_200_OK
    assert len(res_s_list2.json()) == 1

    res_s_detail2 = client.get(f"/api/assignments/{assign_id}", headers=s_headers)
    assert res_s_detail2.status_code == status.HTTP_200_OK
    assert res_s_detail2.json()["my_progress"]["status"] == "NOT_STARTED"

    # 3. Teacher closes assignment
    res_close = client.post(f"/api/assignments/{assign_id}/close", headers=t_headers)
    assert res_close.status_code == status.HTTP_200_OK
    assert res_close.json()["status"] == "CLOSED"


def test_assignment_submission_and_progress_sync(client, db_session):
    from unittest.mock import patch
    env = setup_assignment_test_environment(db_session)
    t_headers = get_auth_headers(env["teacher"])
    s_headers = get_auth_headers(env["student1"])

    # Create & Publish assignment
    res_create = client.post("/api/assignments", json={
        "classroom_id": env["classroom"].id,
        "title": "Lab 1",
        "problems": [{"problem_id": env["prob1"].id, "points": 100, "order": 1}]
    }, headers=t_headers)
    assign_id = res_create.json()["id"]
    client.post(f"/api/assignments/{assign_id}/publish", headers=t_headers)

    # Student submits solution with mocked runner returning success
    def mock_run(language, source, input_data):
        return "8\n", "", 0, False

    sub_payload = {
        "problem_id": env["prob1"].id,
        "language": "python",
        "source_code": "print(8)",
        "assignment_id": assign_id
    }
    with patch("app.services.submission_service.run_code", side_effect=mock_run):
        res_sub = client.post("/api/submissions", json=sub_payload, headers=s_headers)

    assert res_sub.status_code == status.HTTP_201_CREATED
    assert res_sub.json()["status"] == "ACCEPTED"

    # Check updated progress
    res_detail = client.get(f"/api/assignments/{assign_id}", headers=s_headers)
    assert res_detail.status_code == status.HTTP_200_OK
    prog = res_detail.json()["my_progress"]
    assert prog["completed_problems"] == 1
    assert prog["score"] == 100
    assert prog["status"] == "COMPLETED"


def test_deadline_enforcement_rejects_past_due(client, db_session):
    env = setup_assignment_test_environment(db_session)
    t_headers = get_auth_headers(env["teacher"])
    s_headers = get_auth_headers(env["student1"])

    # Create assignment with past deadline
    past_due = (utcnow() - timedelta(hours=2)).isoformat()
    res_create = client.post("/api/assignments", json={
        "classroom_id": env["classroom"].id,
        "title": "Overdue Lab",
        "due_at": past_due,
        "problems": [{"problem_id": env["prob1"].id, "points": 100, "order": 1}]
    }, headers=t_headers)
    assign_id = res_create.json()["id"]
    client.post(f"/api/assignments/{assign_id}/publish", headers=t_headers)

    # Submitting should fail due to deadline
    code = "print(8)"
    sub_payload = {
        "problem_id": env["prob1"].id,
        "language": "python",
        "source_code": code,
        "assignment_id": assign_id
    }
    res_sub = client.post("/api/submissions", json=sub_payload, headers=s_headers)
    assert res_sub.status_code == status.HTTP_400_BAD_REQUEST
    assert "Assignment deadline has passed" in res_sub.json()["detail"]


def test_delete_assignment(client, db_session):
    env = setup_assignment_test_environment(db_session)
    t_headers = get_auth_headers(env["teacher"])

    res_create = client.post("/api/assignments", json={
        "classroom_id": env["classroom"].id,
        "title": "To Delete",
        "problems": []
    }, headers=t_headers)
    assign_id = res_create.json()["id"]

    res_del = client.delete(f"/api/assignments/{assign_id}", headers=t_headers)
    assert res_del.status_code == status.HTTP_204_NO_CONTENT

    res_get = client.get(f"/api/assignments/{assign_id}", headers=t_headers)
    assert res_get.status_code == status.HTTP_404_NOT_FOUND
