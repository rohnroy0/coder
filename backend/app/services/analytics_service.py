import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.classroom import Classroom, ClassroomMember
from app.models.assignment import Assignment
from app.models.problem import Problem, ProblemStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.feedback import AIFeedback, ErrorCategory
from app.models.points import StudentPointsEvent
from app.services.leaderboard_service import LeaderboardService
from app.services.streak_service import StreakService
from app.services.level_service import LevelService

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Performance Analytics Engine for AI Code Classroom.
    Provides SQL-aggregated analytics for students and teachers.
    """

    @staticmethod
    def classify_strength(accuracy: float) -> str:
        if accuracy >= settings.STRENGTH_THRESHOLD_STRONG:
            return "Strong"
        elif accuracy >= settings.STRENGTH_THRESHOLD_DEVELOPING:
            return "Developing"
        else:
            return "Needs Practice"

    @staticmethod
    def get_student_analytics(db: Session, student_id: int) -> Dict[str, Any]:
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            return {}

        # Fetch submissions
        submissions = db.query(Submission).filter(
            Submission.user_id == student_id,
            Submission.status.in_([
                SubmissionStatus.ACCEPTED,
                SubmissionStatus.WRONG_ANSWER,
                SubmissionStatus.RUNTIME_ERROR,
                SubmissionStatus.TIME_LIMIT_EXCEEDED
            ])
        ).order_by(Submission.created_at.desc()).all()

        total_submissions = len(submissions)
        accepted_subs = [s for s in submissions if s.status == SubmissionStatus.ACCEPTED]

        # Problems attempted vs solved
        attempted_problem_ids = list(set(s.problem_id for s in submissions))
        solved_problem_ids = list(set(s.problem_id for s in accepted_subs))

        problems_attempted = len(attempted_problem_ids)
        problems_solved = len(solved_problem_ids)
        problems_failed = problems_attempted - problems_solved

        # Metrics
        submission_accuracy = round((len(accepted_subs) / total_submissions * 100.0), 1) if total_submissions > 0 else 0.0
        problem_completion_rate = round((problems_solved / problems_attempted * 100.0), 1) if problems_attempted > 0 else 0.0

        avg_attempts_per_solved = round(total_submissions / problems_solved, 1) if problems_solved > 0 else 0.0

        exec_times = [s.execution_time for s in submissions if s.execution_time is not None]
        avg_exec_time = round(sum(exec_times) / len(exec_times), 3) if exec_times else 0.0
        best_exec_time = round(min(exec_times), 3) if exec_times else None

        # Total points
        total_points = db.query(func.coalesce(func.sum(StudentPointsEvent.points), 0)).filter(
            StudentPointsEvent.student_id == student_id
        ).scalar() or 0

        # AI Hints count
        ai_hints_count = db.query(AIFeedback).filter(AIFeedback.student_id == student_id).count()

        # Learning streak (consecutive days with at least one submission)
        streak = StreakService.compute_streak(db, student_id)

        # Level, derived transparently from total points
        level = LevelService.compute_level(int(total_points))

        # Classroom Rank
        rank_in_classroom = None
        membership = db.query(ClassroomMember).filter(ClassroomMember.student_id == student_id).first()
        if membership:
            leaderboard = LeaderboardService.get_classroom_leaderboard(db, membership.classroom_id)
            for entry in leaderboard:
                if entry["student_id"] == student_id:
                    rank_in_classroom = entry["rank"]
                    break

        # Topic Breakdown
        topic_stats: Dict[str, Dict[str, Any]] = {}
        for sub in submissions:
            prob = db.query(Problem).filter(Problem.id == sub.problem_id).first()
            topic_name = (prob.topic or "general").strip().capitalize() if prob else "General"

            if topic_name not in topic_stats:
                topic_stats[topic_name] = {
                    "topic": topic_name,
                    "attempted_set": set(),
                    "solved_set": set(),
                    "total_subs": 0,
                    "accepted_subs": 0,
                    "errors": []
                }
            topic_stats[topic_name]["attempted_set"].add(sub.problem_id)
            topic_stats[topic_name]["total_subs"] += 1
            if sub.status == SubmissionStatus.ACCEPTED:
                topic_stats[topic_name]["solved_set"].add(sub.problem_id)
                topic_stats[topic_name]["accepted_subs"] += 1

        # Add AI feedback error categories to topic stats
        feedbacks = db.query(AIFeedback).filter(AIFeedback.student_id == student_id).all()
        error_distribution: Dict[str, int] = {}
        for fb in feedbacks:
            err_type = fb.error_type.value if hasattr(fb.error_type, 'value') else str(fb.error_type)
            error_distribution[err_type] = error_distribution.get(err_type, 0) + 1

        formatted_topics = []
        for t_name, t_data in topic_stats.items():
            t_attempted = len(t_data["attempted_set"])
            t_solved = len(t_data["solved_set"])
            t_acc = round((t_data["accepted_subs"] / t_data["total_subs"] * 100.0), 1) if t_data["total_subs"] > 0 else 0.0
            formatted_topics.append({
                "topic": t_name,
                "attempted": t_attempted,
                "solved": t_solved,
                "accuracy": t_acc,
                "classification": AnalyticsService.classify_strength(t_acc)
            })

        # Recent Activity
        recent_activity = []
        for sub in submissions[:10]:
            prob = db.query(Problem).filter(Problem.id == sub.problem_id).first()
            recent_activity.append({
                "id": sub.id,
                "problem": prob.title if prob else "Problem",
                "status": sub.status.value,
                "execution_time": sub.execution_time,
                "created_at": sub.created_at
            })

        # Points Events Progress History
        point_events = db.query(StudentPointsEvent).filter(
            StudentPointsEvent.student_id == student_id
        ).order_by(StudentPointsEvent.created_at.asc()).all()

        progress_events = []
        running_total = 0
        for pe in point_events:
            running_total += pe.points
            progress_events.append({
                "id": pe.id,
                "event_type": pe.event_type.value,
                "points": pe.points,
                "total_points": running_total,
                "description": pe.description,
                "created_at": pe.created_at
            })

        return {
            "overview": {
                "points": int(total_points),
                "problems_attempted": problems_attempted,
                "problems_solved": problems_solved,
                "problems_failed": problems_failed,
                "submission_accuracy": submission_accuracy,
                "problem_completion_rate": problem_completion_rate,
                "total_submissions": total_submissions,
                "avg_attempts_per_solved": avg_attempts_per_solved,
                "avg_execution_time": avg_exec_time,
                "best_execution_time": best_exec_time,
                "rank_in_classroom": rank_in_classroom,
                "ai_hints_requested": ai_hints_count,
                "current_streak": streak["current_streak"],
                "longest_streak": streak["longest_streak"],
                "last_active_date": streak["last_active_date"],
                "level": level["level"],
                "level_title": level["level_title"],
                "points_in_level": level["points_in_level"],
                "points_per_level": level["points_per_level"],
                "level_progress_pct": level["level_progress_pct"],
            },
            "topics": formatted_topics,
            "error_distribution": error_distribution,
            "progress": progress_events,
            "recent_activity": recent_activity
        }

    @staticmethod
    def get_classroom_analytics(db: Session, classroom_id: int) -> Dict[str, Any]:
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            return {}

        leaderboard = LeaderboardService.get_classroom_leaderboard(db, classroom_id)
        total_students = len(leaderboard)

        if total_students == 0:
            return {
                "overview": {
                    "total_students": 0,
                    "total_submissions": 0,
                    "problems_solved": 0,
                    "avg_class_score": 0.0,
                    "avg_class_accuracy": 0.0
                },
                "topics": [],
                "struggling_students": [],
                "leaderboard": []
            }

        total_points = sum(e["points"] for e in leaderboard)
        total_solved = sum(e["problems_solved"] for e in leaderboard)
        avg_score = round(total_points / total_students, 1)
        avg_accuracy = round(sum(e["accuracy"] for e in leaderboard) / total_students, 1)

        student_ids = [e["student_id"] for e in leaderboard]
        assignment_ids = [a.id for a in db.query(Assignment.id).filter(Assignment.classroom_id == classroom_id)]

        # Total submissions made under THIS classroom's assignments (problems are
        # shared across classrooms, so other classrooms'/practice submissions are excluded)
        if assignment_ids:
            total_submissions = db.query(Submission).filter(
                Submission.user_id.in_(student_ids),
                Submission.assignment_id.in_(assignment_ids)
            ).count()
        else:
            total_submissions = 0

        # Class-wide Topic Analytics, scoped to this classroom's assignments
        topic_map: Dict[str, Dict[str, Any]] = {}
        submissions = db.query(Submission).filter(
            Submission.user_id.in_(student_ids),
            Submission.assignment_id.in_(assignment_ids)
        ).all() if assignment_ids else []

        for sub in submissions:
            prob = db.query(Problem).filter(Problem.id == sub.problem_id).first()
            topic_name = (prob.topic or "general").strip().capitalize() if prob else "General"

            if topic_name not in topic_map:
                topic_map[topic_name] = {
                    "topic": topic_name,
                    "students_set": set(),
                    "total_subs": 0,
                    "accepted_subs": 0
                }
            topic_map[topic_name]["students_set"].add(sub.user_id)
            topic_map[topic_name]["total_subs"] += 1
            if sub.status == SubmissionStatus.ACCEPTED:
                topic_map[topic_name]["accepted_subs"] += 1

        topic_list = []
        for t_name, t_data in topic_map.items():
            t_acc = round((t_data["accepted_subs"] / t_data["total_subs"] * 100.0), 1) if t_data["total_subs"] > 0 else 0.0
            t_avg_attempts = round(t_data["total_subs"] / len(t_data["students_set"]), 1) if t_data["students_set"] else 0.0
            topic_list.append({
                "topic": t_name,
                "students_attempting": len(t_data["students_set"]),
                "avg_accuracy": t_acc,
                "avg_attempts": t_avg_attempts,
                "classification": AnalyticsService.classify_strength(t_acc)
            })

        # Identify struggling students (accuracy < 50% or avg_attempts > 3.0 with at least 1 submission)
        struggling_students = [
            e for e in leaderboard if e["accuracy"] < 50.0 or (e["avg_attempts"] > 3.0 and e["problems_solved"] > 0)
        ]

        return {
            "overview": {
                "total_students": total_students,
                "total_submissions": total_submissions,
                "problems_solved": total_solved,
                "avg_class_score": avg_score,
                "avg_class_accuracy": avg_accuracy
            },
            "topics": topic_list,
            "struggling_students": struggling_students,
            "leaderboard": leaderboard
        }
