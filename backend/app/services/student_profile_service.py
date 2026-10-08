"""
Teacher → Student Performance Profile.

Aggregates everything the system records about one student's coding activity into a
single payload for the teacher's profile page. Reuses the existing Phase 6 engines
(LeaderboardService for ranking, AnalyticsService for overview metrics and topic
classification) instead of re-implementing them, so numbers match the rest of the app.

Authorization is enforced by `authorize` and must be called by every endpoint:
current user is a teacher AND owns the classroom AND the student is enrolled in it.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.assignment import Assignment, AssignmentStudentProgress, AssignmentStatus
from app.models.classroom import Classroom, ClassroomMember
from app.models.feedback import AIFeedback
from app.models.points import StudentPointsEvent
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.services.analytics_service import AnalyticsService
from app.services.leaderboard_service import LeaderboardService

JUDGED_STATUSES = (
    SubmissionStatus.ACCEPTED,
    SubmissionStatus.WRONG_ANSWER,
    SubmissionStatus.RUNTIME_ERROR,
    SubmissionStatus.TIME_LIMIT_EXCEEDED,
)

# Lower is better; used to pick a problem's "best result".
RESULT_RANK = {
    SubmissionStatus.ACCEPTED.value: 0,
    SubmissionStatus.WRONG_ANSWER.value: 1,
    SubmissionStatus.TIME_LIMIT_EXCEEDED.value: 2,
    SubmissionStatus.RUNTIME_ERROR.value: 3,
}

LIMITATIONS = [
    "Memory usage is not measured by the code sandbox, so 'Memory Used' is not available.",
    "Opening a problem is not tracked; activity starts from the first submission.",
    "Points, accuracy and problem counts below cover only this classroom's assignments. "
    "Practice submissions outside any assignment, and work done in other classrooms, are excluded.",
    "AI tutor conversations are summarised as counts and categories; hint text is not shown.",
]


def _naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalise aware/naive datetimes (assignments are tz-aware, the rest naive UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _pct(part: float, whole: float) -> float:
    return round(part / whole * 100.0, 1) if whole else 0.0


def _status_value(s: Any) -> str:
    return s.value if hasattr(s, "value") else str(s)


def _label(category: str) -> str:
    """LOGIC_ERROR -> 'Logic error'."""
    return category.replace("_", " ").capitalize()


class StudentProfileService:

    # ─── Authorization ────────────────────────────────────────────────────────

    @staticmethod
    def authorize(db: Session, user: User, classroom_id: int, student_id: Optional[int] = None
                  ) -> Tuple[Classroom, Optional[ClassroomMember]]:
        if user.role != UserRole.TEACHER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can view student profiles")

        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
        if classroom.teacher_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: you do not own this classroom")

        membership = None
        if student_id is not None:
            membership = db.query(ClassroomMember).filter(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.student_id == student_id,
            ).first()
            if not membership:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this classroom")
        return classroom, membership

    # ─── Roster ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_roster(db: Session, classroom: Classroom) -> List[Dict[str, Any]]:
        leaderboard = LeaderboardService.get_classroom_leaderboard(db, classroom.id)
        members = {m.student_id: m for m in db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom.id)}

        assignments = StudentProfileService._student_visible_assignments(db, classroom.id)
        total_problems = sum(len(a.problems) for a in assignments)
        assignment_ids = [a.id for a in assignments]

        completed_by_student: Dict[int, int] = defaultdict(int)
        if assignment_ids:
            for prog in db.query(AssignmentStudentProgress).filter(AssignmentStudentProgress.assignment_id.in_(assignment_ids)):
                completed_by_student[prog.student_id] += prog.completed_problems

        roster = []
        for entry in leaderboard:
            sid = entry["student_id"]
            user = db.query(User).filter(User.id == sid).first()
            roster.append({
                "student_id": sid,
                "name": entry["student_name"],
                "email": user.email if user else "",
                "joined_at": members[sid].joined_at,
                "rank": entry["rank"],
                "points": entry["points"],
                "problems_solved": entry["problems_solved"],
                "accuracy": entry["accuracy"],
                "progress": _pct(completed_by_student[sid], total_problems) if total_problems else None,
            })
        return roster

    @staticmethod
    def _student_visible_assignments(db: Session, classroom_id: int) -> List[Assignment]:
        return db.query(Assignment).filter(
            Assignment.classroom_id == classroom_id,
            Assignment.status.in_([AssignmentStatus.PUBLISHED, AssignmentStatus.CLOSED]),
        ).all()

    # ─── Full profile ─────────────────────────────────────────────────────────

    @staticmethod
    def get_profile(db: Session, classroom: Classroom, membership: ClassroomMember) -> Dict[str, Any]:
        student = db.query(User).filter(User.id == membership.student_id).first()
        sid = student.id

        # Problems are shared across classrooms, so everything below is scoped to
        # submissions made under THIS classroom's own assignments — a student's
        # practice submissions and other classrooms' work must not leak in here.
        assignment_ids = [a.id for a in db.query(Assignment.id).filter(Assignment.classroom_id == classroom.id)]

        if assignment_ids:
            submissions = db.query(Submission).filter(
                Submission.user_id == sid,
                Submission.assignment_id.in_(assignment_ids),
                Submission.status.in_(JUDGED_STATUSES)
            ).order_by(Submission.created_at.asc(), Submission.id.asc()).all()

            scoped_submission_ids: Set[int] = {
                row[0] for row in db.query(Submission.id).filter(
                    Submission.user_id == sid, Submission.assignment_id.in_(assignment_ids)
                )
            }
        else:
            submissions = []
            scoped_submission_ids = set()

        leaderboard = LeaderboardService.get_classroom_leaderboard(db, classroom.id)
        lb_entry = next((e for e in leaderboard if e["student_id"] == sid), None)

        problem_ids = {s.problem_id for s in submissions}
        problems = {p.id: p for p in db.query(Problem).filter(Problem.id.in_(problem_ids))} if problem_ids else {}
        assignment_titles = {a.id: a.title for a in db.query(Assignment).filter(Assignment.classroom_id == classroom.id)}

        feedbacks = (
            db.query(AIFeedback).filter(
                AIFeedback.student_id == sid, AIFeedback.submission_id.in_(scoped_submission_ids)
            ).order_by(AIFeedback.created_at.asc()).all()
            if scoped_submission_ids else []
        )
        sub_by_id = {s.id: s for s in submissions}
        # Feedback may point at in-scope submissions filtered out above (e.g. PENDING); load those too
        missing = {fb.submission_id for fb in feedbacks} - set(sub_by_id)
        if missing:
            for s in db.query(Submission).filter(Submission.id.in_(missing)):
                sub_by_id[s.id] = s
                if s.problem_id not in problems:
                    p = db.query(Problem).filter(Problem.id == s.problem_id).first()
                    if p:
                        problems[p.id] = p

        ov, topics_raw = StudentProfileService._compute_overview_and_topics(
            db, sid, submissions, assignment_ids, problems, feedbacks
        )

        def problem_title(pid: int) -> str:
            return problems[pid].title if pid in problems else f"Problem #{pid}"

        def problem_topic(pid: int) -> str:
            p = problems.get(pid)
            return (p.topic or "general").strip().capitalize() if p else "General"

        # Attempt numbers (per problem, chronological)
        attempt_no: Dict[int, int] = {}
        counter: Dict[int, int] = defaultdict(int)
        for s in submissions:
            counter[s.problem_id] += 1
            attempt_no[s.id] = counter[s.problem_id]

        assignments = StudentProfileService._build_assignments(db, classroom, sid, submissions, problems)
        problem_rows = StudentProfileService._build_problems(db, classroom, submissions, problems, feedbacks, sub_by_id)

        submission_rows = [{
            "submission_id": s.id,
            "created_at": s.created_at,
            "problem_id": s.problem_id,
            "problem": problem_title(s.problem_id),
            "assignment": assignment_titles.get(s.assignment_id) if s.assignment_id else None,
            "language": s.language,
            "result": _status_value(s.status),
            "execution_time": s.execution_time,
            "memory_used_mb": None,
            "attempt_number": attempt_no[s.id],
        } for s in reversed(submissions)]

        ai_tutor, errors = StudentProfileService._build_ai_and_errors(feedbacks, sub_by_id, problem_title, problem_topic, submissions)

        topics = sorted(topics_raw, key=lambda t: (-t["accuracy"], t["topic"]))
        trends = StudentProfileService._build_trends(db, sid, submissions, scoped_submission_ids)
        points_history = StudentProfileService._build_points_history(db, sid, sub_by_id, problem_title, scoped_submission_ids)
        activity = StudentProfileService._build_activity(membership, classroom, submissions, feedbacks, sub_by_id,
                                                        assignments, problem_title, db, sid, scoped_submission_ids)

        assignments_completed = sum(1 for a in assignments if a["progress_status"] == "COMPLETED")
        visible_assignments = [a for a in assignments if a["assignment_status"] != AssignmentStatus.DRAFT.value]

        overall = {
            "total_points": ov["points"],
            "problems_solved": ov["problems_solved"],
            "problems_attempted": ov["problems_attempted"],
            "submission_accuracy": ov["submission_accuracy"],
            "completion_rate": ov["problem_completion_rate"],
            "avg_attempts": ov["avg_attempts_per_solved"],
            "avg_execution_time": ov["avg_execution_time"],
            "total_submissions": ov["total_submissions"],
            "assignments_completed": assignments_completed,
            "assignments_total": len(visible_assignments),
        }

        summary = StudentProfileService._build_summary(overall, topics, ai_tutor, errors)

        return {
            "header": {
                "student_id": sid,
                "name": student.name,
                "email": student.email,
                "classroom_id": classroom.id,
                "classroom_name": classroom.name,
                "joined_at": membership.joined_at,
                "rank": lb_entry["rank"] if lb_entry else None,
                "total_students": len(leaderboard),
                "total_points": ov["points"],
            },
            "summary": summary,
            "overall": overall,
            "leaderboard": {
                "rank": lb_entry["rank"] if lb_entry else None,
                "total_students": len(leaderboard),
                "points": lb_entry["points"] if lb_entry else ov["points"],
                "problems_solved": lb_entry["problems_solved"] if lb_entry else ov["problems_solved"],
                "accuracy": lb_entry["accuracy"] if lb_entry else ov["submission_accuracy"],
            },
            "assignments": assignments,
            "problems": problem_rows,
            "submissions": submission_rows,
            "ai_tutor": ai_tutor,
            "errors": errors,
            "topics": topics,
            "trends": trends,
            "points_history": points_history,
            "recent_activity": activity,
            "limitations": LIMITATIONS,
        }

    # ─── Overview & topics (classroom-scoped) ─────────────────────────────────

    @staticmethod
    def _compute_overview_and_topics(
        db: Session, sid: int, submissions: List[Submission], assignment_ids: List[int],
        problems: Dict[int, Problem], feedbacks: List[AIFeedback]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Mirrors AnalyticsService.get_student_analytics' overview/topic shape, but
        computed only from submissions made under THIS classroom's assignments.
        """
        total_submissions = len(submissions)
        accepted_subs = [s for s in submissions if s.status == SubmissionStatus.ACCEPTED]

        attempted_ids = {s.problem_id for s in submissions}
        solved_ids = {s.problem_id for s in accepted_subs}
        problems_attempted = len(attempted_ids)
        problems_solved = len(solved_ids)

        submission_accuracy = _pct(len(accepted_subs), total_submissions)
        completion_rate = _pct(problems_solved, problems_attempted)
        avg_attempts = round(total_submissions / problems_solved, 1) if problems_solved else 0.0

        exec_times = [s.execution_time for s in submissions if s.execution_time is not None]
        avg_exec_time = round(sum(exec_times) / len(exec_times), 3) if exec_times else 0.0

        if assignment_ids:
            total_points = db.query(func.coalesce(func.sum(StudentPointsEvent.points), 0)).join(
                Submission, StudentPointsEvent.submission_id == Submission.id
            ).filter(
                StudentPointsEvent.student_id == sid,
                Submission.assignment_id.in_(assignment_ids)
            ).scalar()
        else:
            total_points = 0

        topic_stats: Dict[str, Dict[str, Any]] = {}
        for s in submissions:
            p = problems.get(s.problem_id)
            topic_name = (p.topic or "general").strip().capitalize() if p else "General"
            t = topic_stats.setdefault(topic_name, {"attempted": set(), "solved": set(), "total": 0, "accepted": 0})
            t["attempted"].add(s.problem_id)
            t["total"] += 1
            if s.status == SubmissionStatus.ACCEPTED:
                t["solved"].add(s.problem_id)
                t["accepted"] += 1

        topics = [{
            "topic": name,
            "attempted": len(t["attempted"]),
            "solved": len(t["solved"]),
            "accuracy": _pct(t["accepted"], t["total"]),
            "classification": AnalyticsService.classify_strength(_pct(t["accepted"], t["total"])),
        } for name, t in topic_stats.items()]

        overview = {
            "points": int(total_points),
            "problems_attempted": problems_attempted,
            "problems_solved": problems_solved,
            "submission_accuracy": submission_accuracy,
            "problem_completion_rate": completion_rate,
            "total_submissions": total_submissions,
            "avg_attempts_per_solved": avg_attempts,
            "avg_execution_time": avg_exec_time,
            "ai_hints_requested": len(feedbacks),
        }
        return overview, topics

    # ─── Sections ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_assignments(db, classroom, sid, submissions, problems) -> List[Dict[str, Any]]:
        rows = []
        all_assignments = db.query(Assignment).filter(Assignment.classroom_id == classroom.id).order_by(Assignment.created_at.asc()).all()
        for a in all_assignments:
            prog = db.query(AssignmentStudentProgress).filter(
                AssignmentStudentProgress.assignment_id == a.id,
                AssignmentStudentProgress.student_id == sid,
            ).first()
            a_subs = [s for s in submissions if s.assignment_id == a.id]

            problem_details = []
            for ap in a.problems:
                p_subs = [s for s in a_subs if s.problem_id == ap.problem_id]
                results = [_status_value(s.status) for s in p_subs]
                best = min(results, key=lambda r: RESULT_RANK.get(r, 9)) if results else None
                problem_details.append({
                    "problem_id": ap.problem_id,
                    "title": ap.problem.title if ap.problem else f"Problem #{ap.problem_id}",
                    "points": ap.points,
                    "attempts": len(p_subs),
                    "best_result": best,
                    "solved": best == SubmissionStatus.ACCEPTED.value,
                })

            max_score = a.total_points or sum(ap.points for ap in a.problems)
            score = prog.score if prog else 0
            rows.append({
                "assignment_id": a.id,
                "title": a.title,
                "assignment_status": _status_value(a.status),
                "progress_status": _status_value(prog.status) if prog else "NOT_STARTED",
                "completed_problems": prog.completed_problems if prog else 0,
                "total_problems": prog.total_problems if prog and prog.total_problems else len(a.problems),
                "score": score,
                "max_score": max_score,
                "percentage": _pct(score, max_score),
                "attempts": len(a_subs),
                "due_at": a.due_at,
                "completed_at": prog.completed_at if prog else None,
                "last_activity_at": prog.last_activity_at if prog else None,
                "problems": problem_details,
            })
        return rows

    @staticmethod
    def _build_problems(db, classroom, submissions, problems, feedbacks, sub_by_id) -> List[Dict[str, Any]]:
        # Assignments in THIS classroom that contain each problem
        in_assignments: Dict[int, List[str]] = defaultdict(list)
        for a in db.query(Assignment).filter(Assignment.classroom_id == classroom.id):
            for ap in a.problems:
                in_assignments[ap.problem_id].append(a.title)

        hints_per_problem: Counter = Counter()
        for fb in feedbacks:
            s = sub_by_id.get(fb.submission_id)
            if s:
                hints_per_problem[s.problem_id] += 1

        by_problem: Dict[int, List[Submission]] = defaultdict(list)
        for s in submissions:
            by_problem[s.problem_id].append(s)

        rows = []
        for pid, subs in by_problem.items():
            p = problems.get(pid)
            results = [_status_value(s.status) for s in subs]
            best = min(results, key=lambda r: RESULT_RANK.get(r, 9))
            accepted_times = [s.execution_time for s in subs if s.status == SubmissionStatus.ACCEPTED and s.execution_time is not None]
            rows.append({
                "problem_id": pid,
                "title": p.title if p else f"Problem #{pid}",
                "topic": (p.topic or "General").strip().capitalize() if p else "General",
                "difficulty": _status_value(p.difficulty) if p else "UNKNOWN",
                "assignments": in_assignments.get(pid, []),
                "attempts": len(subs),
                "first_result": results[0],
                "latest_result": results[-1],
                "best_result": best,
                "best_execution_time": round(min(accepted_times), 3) if accepted_times else None,
                "last_submission_at": subs[-1].created_at,
                "hints_requested": hints_per_problem.get(pid, 0),
                "completion_status": "Solved" if best == SubmissionStatus.ACCEPTED.value else "Attempted",
            })
        rows.sort(key=lambda r: r["last_submission_at"], reverse=True)
        return rows

    @staticmethod
    def _build_ai_and_errors(feedbacks, sub_by_id, problem_title, problem_topic, submissions):
        hints_by_problem: Counter = Counter()
        categories: Counter = Counter()
        topics_by_category: Dict[str, set] = defaultdict(set)
        levels_by_problem: Dict[str, List[int]] = defaultdict(list)

        for fb in feedbacks:
            s = sub_by_id.get(fb.submission_id)
            title = problem_title(s.problem_id) if s else "Unknown problem"
            cat = _status_value(fb.error_type)
            hints_by_problem[title] += 1
            categories[cat] += 1
            levels_by_problem[title].append(fb.hint_level)
            if s:
                topics_by_category[cat].add(problem_topic(s.problem_id))

        most_common = categories.most_common(1)[0][0] if categories else None
        total = sum(categories.values())

        ai_tutor = {
            "total_hints": len(feedbacks),
            "hints_by_problem": [{"name": n, "count": c} for n, c in hints_by_problem.most_common()],
            "categories": [{"name": n, "count": c} for n, c in categories.most_common()],
            "most_common_error": most_common,
            "progression": [
                {"problem": n, "levels": lv, "max_level": max(lv)}
                for n, lv in sorted(levels_by_problem.items(), key=lambda kv: -len(kv[1]))
            ],
        }

        judge = Counter(_status_value(s.status) for s in submissions if s.status != SubmissionStatus.ACCEPTED)
        errors = {
            "ai_categories": [{
                "category": cat,
                "count": c,
                "percentage": _pct(c, total),
                "topics": sorted(topics_by_category[cat]),
            } for cat, c in categories.most_common()],
            "judge_outcomes": [{"name": n, "count": c} for n, c in judge.most_common()],
        }
        return ai_tutor, errors

    @staticmethod
    def _build_trends(db, sid, submissions, submission_ids: Set[int]) -> List[Dict[str, Any]]:
        days: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "accepted": 0, "newly_solved": 0, "points": 0})
        solved = set()
        for s in submissions:
            d = s.created_at.date().isoformat()
            days[d]["total"] += 1
            if s.status == SubmissionStatus.ACCEPTED:
                days[d]["accepted"] += 1
                if s.problem_id not in solved:
                    solved.add(s.problem_id)
                    days[d]["newly_solved"] += 1

        if submission_ids:
            for pe in db.query(StudentPointsEvent).filter(
                StudentPointsEvent.student_id == sid, StudentPointsEvent.submission_id.in_(submission_ids)
            ):
                days[pe.created_at.date().isoformat()]["points"] += pe.points

        trend, pts, solved_n, tot, acc = [], 0, 0, 0, 0
        for d in sorted(days):
            day = days[d]
            pts += day["points"]
            solved_n += day["newly_solved"]
            tot += day["total"]
            acc += day["accepted"]
            trend.append({
                "date": d,
                "points": pts,
                "problems_solved": solved_n,
                "accuracy": _pct(acc, tot),
                "daily_accuracy": _pct(day["accepted"], day["total"]),
            })
        return trend

    @staticmethod
    def _build_points_history(db, sid, sub_by_id, problem_title, submission_ids: Set[int]) -> List[Dict[str, Any]]:
        if not submission_ids:
            return []
        events = db.query(StudentPointsEvent).filter(
            StudentPointsEvent.student_id == sid, StudentPointsEvent.submission_id.in_(submission_ids)
        ).order_by(StudentPointsEvent.created_at.asc(), StudentPointsEvent.id.asc()).all()
        rows, running = [], 0
        for pe in events:
            running += pe.points
            s = sub_by_id.get(pe.submission_id) if pe.submission_id else None
            if pe.submission_id and not s:
                s = db.query(Submission).filter(Submission.id == pe.submission_id).first()
            rows.append({
                "id": pe.id,
                "created_at": pe.created_at,
                "event_type": _status_value(pe.event_type),
                "reason": pe.description,
                "problem": problem_title(s.problem_id) if s else None,
                "points": pe.points,
                "running_total": running,
            })
        rows.reverse()  # newest first
        return rows

    @staticmethod
    def _build_activity(membership, classroom, submissions, feedbacks, sub_by_id, assignments, problem_title, db, sid,
                        submission_ids: Set[int], limit: int = 30) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = [{
            "type": "JOINED",
            "description": f"Joined classroom {classroom.name}",
            "created_at": membership.joined_at,
            "points": None,
        }]

        points_by_sub: Dict[int, int] = defaultdict(int)
        if submission_ids:
            for pe in db.query(StudentPointsEvent).filter(
                StudentPointsEvent.student_id == sid, StudentPointsEvent.submission_id.in_(submission_ids)
            ):
                points_by_sub[pe.submission_id] += pe.points

        verbs = {
            "ACCEPTED": "Accepted solution for",
            "WRONG_ANSWER": "Wrong answer on",
            "RUNTIME_ERROR": "Runtime error on",
            "TIME_LIMIT_EXCEEDED": "Time limit exceeded on",
        }
        started = {}
        for s in submissions:
            result = _status_value(s.status)
            items.append({
                "type": result,
                "description": f"{verbs.get(result, 'Submitted code for')} {problem_title(s.problem_id)}",
                "created_at": s.created_at,
                "points": points_by_sub.get(s.id) or None,
            })
            if s.assignment_id and s.assignment_id not in started:
                started[s.assignment_id] = s.created_at

        titles = {a["assignment_id"]: a["title"] for a in assignments}
        for aid, at in started.items():
            if aid in titles:
                items.append({"type": "ASSIGNMENT_STARTED", "description": f"Started assignment {titles[aid]}",
                              "created_at": at, "points": None})
        for a in assignments:
            if a["completed_at"]:
                items.append({"type": "ASSIGNMENT_COMPLETED", "description": f"Completed assignment {a['title']}",
                              "created_at": a["completed_at"], "points": None})

        for fb in feedbacks:
            s = sub_by_id.get(fb.submission_id)
            items.append({
                "type": "HINT",
                "description": f"Requested AI hint (level {fb.hint_level}) for {problem_title(s.problem_id) if s else 'a problem'}",
                "created_at": fb.created_at,
                "points": None,
            })

        for it in items:
            it["created_at"] = _naive_utc(it["created_at"])
        items.sort(key=lambda it: it["created_at"], reverse=True)
        return items[:limit]

    @staticmethod
    def _build_summary(overall, topics, ai_tutor, errors) -> Dict[str, Any]:
        """Plain factual statements derived from the metrics — no LLM involved."""
        strong = [t["topic"] for t in topics if t["classification"] == "Strong"]
        developing = [t["topic"] for t in topics if t["classification"] == "Developing"]
        needs = [t["topic"] for t in topics if t["classification"] == "Needs Practice"]
        most_common = ai_tutor["most_common_error"]

        lines = [
            f"Problems solved: {overall['problems_solved']} / {overall['problems_attempted']} attempted",
            f"Submission accuracy: {overall['submission_accuracy']}% over {overall['total_submissions']} submissions",
        ]
        if overall["assignments_total"]:
            lines.append(f"Assignments completed: {overall['assignments_completed']} / {overall['assignments_total']}")
        if ai_tutor["total_hints"]:
            lines.append(f"AI hints requested: {ai_tutor['total_hints']}")
        if most_common:
            lines.append(f"Most common error: {_label(most_common)}")
        elif errors["judge_outcomes"]:
            top = errors["judge_outcomes"][0]
            lines.append(f"Most frequent failed verdict: {_label(top['name'])} ({top['count']})")

        return {
            "lines": lines,
            "strong_topics": strong,
            "developing_topics": developing,
            "needs_practice_topics": needs,
            "most_common_error": most_common,
        }

    # ─── Single submission (source code) ──────────────────────────────────────

    @staticmethod
    def get_submission_code(db: Session, classroom: Classroom, student_id: int, submission_id: int) -> Dict[str, Any]:
        sub = db.query(Submission).filter(Submission.id == submission_id, Submission.user_id == student_id).first()

        # The submission must belong to one of THIS classroom's assignments - otherwise
        # it's either another classroom's work or unassigned practice, neither of which
        # this teacher is entitled to view from here.
        assignment = None
        if sub and sub.assignment_id:
            a = db.query(Assignment).filter(Assignment.id == sub.assignment_id, Assignment.classroom_id == classroom.id).first()
            if a:
                assignment = a.title
            else:
                sub = None
        elif sub:
            sub = None

        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found for this student")

        problem = db.query(Problem).filter(Problem.id == sub.problem_id).first()

        attempt = db.query(Submission).filter(
            Submission.user_id == student_id,
            Submission.problem_id == sub.problem_id,
            Submission.status.in_(JUDGED_STATUSES),
            Submission.id <= sub.id,
        ).count()

        return {
            "submission_id": sub.id,
            "student_id": student_id,
            "problem": problem.title if problem else f"Problem #{sub.problem_id}",
            "assignment": assignment,
            "language": sub.language,
            "result": _status_value(sub.status),
            "execution_time": sub.execution_time,
            "created_at": sub.created_at,
            "attempt_number": attempt,
            "source_code": sub.source_code,
        }
