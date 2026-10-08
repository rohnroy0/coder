from datetime import timedelta

import pytest
from app.core.time import utcnow
from fastapi.testclient import TestClient
from app.models.user import User, UserRole
from app.models.classroom import Classroom, ClassroomMember
from app.models.problem import Problem, ProblemDifficulty, ProblemStatus
from app.models.assignment import Assignment, AssignmentStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.points import StudentPointsEvent, PointEventType
from app.models.feedback import AIFeedback, ErrorCategory
from app.services.scoring_service import ScoringService
from app.services.leaderboard_service import LeaderboardService
from app.services.analytics_service import AnalyticsService
from app.services.streak_service import StreakService


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
def teacher1_token(client: TestClient) -> str:
    return register_and_login(client, "teacher1@analytics.com", "pass1234", "TEACHER")


@pytest.fixture
def teacher2_token(client: TestClient) -> str:
    return register_and_login(client, "teacher2@analytics.com", "pass1234", "TEACHER")


@pytest.fixture
def student1_token(client: TestClient) -> str:
    return register_and_login(client, "student1@analytics.com", "pass1234", "STUDENT")


@pytest.fixture
def student2_token(client: TestClient) -> str:
    return register_and_login(client, "student2@analytics.com", "pass1234", "STUDENT")


class TestScoringAndPoints:

    def test_point_calculation_accepted_fast_quality(self, db_session):
        user = User(name="Alex", email="alex@test.com", password_hash="hash", role=UserRole.STUDENT)
        prob = Problem(title="P1", description="desc", difficulty=ProblemDifficulty.EASY, created_by=1)
        db_session.add_all([user, prob])
        db_session.commit()

        sub = Submission(user_id=user.id, problem_id=prob.id, language="python", source_code="print(1)", status=SubmissionStatus.ACCEPTED, execution_time=0.01)
        db_session.add(sub)
        db_session.commit()

        events = ScoringService.process_submission_scoring(db_session, sub, prob)
        assert len(events) == 3
        types = [e.event_type for e in events]
        assert PointEventType.ACCEPTED in types
        assert PointEventType.FAST_BONUS in types
        assert PointEventType.QUALITY_BONUS in types

        total_pts = sum(e.points for e in events)
        assert total_pts == 130  # 100 + 20 + 10

    def test_duplicate_accepted_does_not_duplicate_base_points(self, db_session):
        user = User(name="Alex", email="alex2@test.com", password_hash="hash", role=UserRole.STUDENT)
        prob = Problem(title="P1", description="desc", difficulty=ProblemDifficulty.EASY, created_by=1)
        db_session.add_all([user, prob])
        db_session.commit()

        # First accepted submission
        sub1 = Submission(user_id=user.id, problem_id=prob.id, language="python", source_code="print(1)", status=SubmissionStatus.ACCEPTED, execution_time=0.02)
        db_session.add(sub1)
        db_session.commit()
        ScoringService.process_submission_scoring(db_session, sub1, prob)

        # Second accepted submission for same problem
        sub2 = Submission(user_id=user.id, problem_id=prob.id, language="python", source_code="print(1)", status=SubmissionStatus.ACCEPTED, execution_time=0.02)
        db_session.add(sub2)
        db_session.commit()
        events2 = ScoringService.process_submission_scoring(db_session, sub2, prob)

        # Base accepted points (+100) should NOT be re-awarded
        base_events = [e for e in events2 if e.event_type == PointEventType.ACCEPTED]
        assert len(base_events) == 0

    def test_wrong_answer_and_penalties(self, db_session):
        user = User(name="Alex", email="alex3@test.com", password_hash="hash", role=UserRole.STUDENT)
        prob = Problem(title="P1", description="desc", difficulty=ProblemDifficulty.EASY, created_by=1)
        db_session.add_all([user, prob])
        db_session.commit()

        sub = Submission(user_id=user.id, problem_id=prob.id, language="python", source_code="print(999)", status=SubmissionStatus.WRONG_ANSWER)
        db_session.add(sub)
        db_session.commit()

        events = ScoringService.process_submission_scoring(db_session, sub, prob)
        assert len(events) == 1
        assert events[0].event_type == PointEventType.WRONG_ANSWER
        assert events[0].points == -5


class TestLeaderboardAndRanking:

    def test_deterministic_leaderboard_ranking(self, db_session):
        # Create 3 students
        s1 = User(name="Student 1", email="s1@lb.com", password_hash="h", role=UserRole.STUDENT)
        s2 = User(name="Student 2", email="s2@lb.com", password_hash="h", role=UserRole.STUDENT)
        s3 = User(name="Student 3", email="s3@lb.com", password_hash="h", role=UserRole.STUDENT)
        t = User(name="Teacher", email="t@lb.com", password_hash="h", role=UserRole.TEACHER)
        db_session.add_all([s1, s2, s3, t])
        db_session.commit()

        cr = Classroom(name="Class 1", teacher_id=t.id, join_code="LB101")
        db_session.add(cr)
        db_session.commit()

        # Enroll all students
        db_session.add_all([
            ClassroomMember(classroom_id=cr.id, student_id=s1.id),
            ClassroomMember(classroom_id=cr.id, student_id=s2.id),
            ClassroomMember(classroom_id=cr.id, student_id=s3.id)
        ])
        db_session.commit()

        # Leaderboard points are scoped to submissions made under this classroom's
        # assignments, so each student needs a submission tied to one.
        prob = Problem(title="P1", description="d", difficulty=ProblemDifficulty.EASY,
                        status=ProblemStatus.VERIFIED, created_by=t.id)
        db_session.add(prob)
        db_session.commit()

        asg = Assignment(classroom_id=cr.id, teacher_id=t.id, title="A1", status=AssignmentStatus.PUBLISHED)
        db_session.add(asg)
        db_session.commit()

        def make_submission(student):
            sub = Submission(user_id=student.id, problem_id=prob.id, language="python", source_code="x",
                              status=SubmissionStatus.ACCEPTED, assignment_id=asg.id)
            db_session.add(sub)
            db_session.commit()
            return sub

        sub_s1, sub_s2, sub_s3 = make_submission(s1), make_submission(s2), make_submission(s3)

        # Assign points events: s2 has 200 pts, s1 has 100 pts, s3 has 100 pts
        db_session.add_all([
            StudentPointsEvent(student_id=s2.id, classroom_id=cr.id, submission_id=sub_s2.id, event_type=PointEventType.ACCEPTED, points=200, description="P1"),
            StudentPointsEvent(student_id=s1.id, classroom_id=cr.id, submission_id=sub_s1.id, event_type=PointEventType.ACCEPTED, points=100, description="P1"),
            StudentPointsEvent(student_id=s3.id, classroom_id=cr.id, submission_id=sub_s3.id, event_type=PointEventType.ACCEPTED, points=100, description="P1"),
        ])
        db_session.commit()

        lb = LeaderboardService.get_classroom_leaderboard(db_session, cr.id)
        assert len(lb) == 3
        # Rank 1: s2 (200 pts)
        assert lb[0]["student_id"] == s2.id
        assert lb[0]["rank"] == 1

        # s1 and s3 tied on points (100) -> Tie-breaker student_id ASC (s1 < s3)
        assert lb[1]["student_id"] == s1.id
        assert lb[1]["rank"] == 2
        assert lb[2]["student_id"] == s3.id
        assert lb[2]["rank"] == 3


class TestStreak:
    """
    Streaks are personal to the student across all activity (not classroom-scoped):
    a day counts as active if the student made at least one submission, of any result.
    """

    @pytest.fixture
    def student_and_problem(self, db_session):
        s = User(name="Streaker", email="streak@test.com", password_hash="h", role=UserRole.STUDENT)
        t = User(name="Teacher", email="streak_t@test.com", password_hash="h", role=UserRole.TEACHER)
        db_session.add_all([s, t])
        db_session.commit()
        prob = Problem(title="P", description="d", difficulty=ProblemDifficulty.EASY,
                        status=ProblemStatus.VERIFIED, created_by=t.id)
        db_session.add(prob)
        db_session.commit()
        return s, prob

    def make_submission(self, db_session, student, prob, days_ago: int):
        sub = Submission(
            user_id=student.id, problem_id=prob.id, language="python", source_code="x",
            status=SubmissionStatus.ACCEPTED,
            created_at=utcnow() - timedelta(days=days_ago),
        )
        db_session.add(sub)
        db_session.commit()
        return sub

    def test_no_submissions_has_zero_streak(self, db_session, student_and_problem):
        student, _ = student_and_problem
        result = StreakService.compute_streak(db_session, student.id)
        assert result == {"current_streak": 0, "longest_streak": 0, "last_active_date": None}

    def test_activity_today_counts_as_streak_of_one(self, db_session, student_and_problem):
        student, prob = student_and_problem
        self.make_submission(db_session, student, prob, days_ago=0)
        result = StreakService.compute_streak(db_session, student.id)
        assert result["current_streak"] == 1
        assert result["longest_streak"] == 1

    def test_consecutive_days_ending_today(self, db_session, student_and_problem):
        student, prob = student_and_problem
        for d in (0, 1, 2, 3):
            self.make_submission(db_session, student, prob, days_ago=d)
        result = StreakService.compute_streak(db_session, student.id)
        assert result["current_streak"] == 4
        assert result["longest_streak"] == 4

    def test_streak_survives_until_today_if_active_yesterday(self, db_session, student_and_problem):
        """No submission yet today, but yesterday was active -> streak is still alive."""
        student, prob = student_and_problem
        for d in (1, 2, 3):
            self.make_submission(db_session, student, prob, days_ago=d)
        result = StreakService.compute_streak(db_session, student.id)
        assert result["current_streak"] == 3

    def test_streak_breaks_after_a_missed_day(self, db_session, student_and_problem):
        """Last activity was 2+ days ago -> current streak is broken (0), but history remembers the longest run."""
        student, prob = student_and_problem
        for d in (2, 3, 4):
            self.make_submission(db_session, student, prob, days_ago=d)
        result = StreakService.compute_streak(db_session, student.id)
        assert result["current_streak"] == 0
        assert result["longest_streak"] == 3

    def test_longest_streak_is_the_best_historical_run(self, db_session, student_and_problem):
        student, prob = student_and_problem
        # A 5-day run far in the past...
        for d in (20, 21, 22, 23, 24):
            self.make_submission(db_session, student, prob, days_ago=d)
        # ...then a shorter, more recent 2-day run ending today
        for d in (0, 1):
            self.make_submission(db_session, student, prob, days_ago=d)
        result = StreakService.compute_streak(db_session, student.id)
        assert result["current_streak"] == 2
        assert result["longest_streak"] == 5

    def test_student_dashboard_analytics_includes_streak(self, client, student1_token):
        res = client.get("/api/analytics/student/me", headers=auth_header(student1_token))
        assert res.status_code == 200
        overview = res.json()["overview"]
        assert "current_streak" in overview and "longest_streak" in overview
        assert overview["current_streak"] == 0  # student1 fixture has no submissions


class TestAnalyticsApiAndAuthorization:

    def test_student_can_view_own_analytics(self, client, student1_token):
        res = client.get("/api/analytics/student/me", headers=auth_header(student1_token))
        assert res.status_code == 200
        data = res.json()
        assert "overview" in data
        assert "topics" in data
        assert "error_distribution" in data
        assert data["overview"]["points"] >= 0

    def test_student_cannot_view_other_student_analytics(self, client, student1_token, student2_token, db_session):
        s2 = db_session.query(User).filter(User.email == "student2@analytics.com").first()
        res = client.get(f"/api/analytics/student/{s2.id}", headers=auth_header(student1_token))
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]

    def test_unrelated_user_cannot_view_classroom_leaderboard(self, client, student1_token, teacher1_token, db_session):
        # Teacher creates classroom
        t1 = db_session.query(User).filter(User.email == "teacher1@analytics.com").first()
        cr = Classroom(name="Private Class", teacher_id=t1.id, join_code="PRIV1")
        db_session.add(cr)
        db_session.commit()

        # student1 is NOT enrolled in cr
        res = client.get(f"/api/analytics/classroom/{cr.id}/leaderboard", headers=auth_header(student1_token))
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]

    def test_enrolled_student_and_teacher_can_view_leaderboard(self, client, student1_token, teacher1_token, db_session):
        t1 = db_session.query(User).filter(User.email == "teacher1@analytics.com").first()
        s1 = db_session.query(User).filter(User.email == "student1@analytics.com").first()
        cr = Classroom(name="Public Class", teacher_id=t1.id, join_code="PUB123")
        db_session.add(cr)
        db_session.commit()

        db_session.add(ClassroomMember(classroom_id=cr.id, student_id=s1.id))
        db_session.commit()

        # Teacher view
        res_t = client.get(f"/api/analytics/classroom/{cr.id}/leaderboard", headers=auth_header(teacher1_token))
        assert res_t.status_code == 200

        # Enrolled student view
        res_s = client.get(f"/api/analytics/classroom/{cr.id}/leaderboard", headers=auth_header(student1_token))
        assert res_s.status_code == 200

    def test_empty_classroom_analytics_returns_clean_structure(self, client, teacher1_token, db_session):
        t1 = db_session.query(User).filter(User.email == "teacher1@analytics.com").first()
        cr = Classroom(name="Empty Class", teacher_id=t1.id, join_code="EMPTY1")
        db_session.add(cr)
        db_session.commit()

        res = client.get(f"/api/analytics/classroom/{cr.id}", headers=auth_header(teacher1_token))
        assert res.status_code == 200
        data = res.json()
        assert data["overview"]["total_students"] == 0
        assert data["overview"]["avg_class_score"] == 0.0
        assert data["leaderboard"] == []
