from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.learning import LearningChapter
from app.models.submission import Submission, SubmissionStatus
from app.services.code_runner import SUPPORTED_LANGUAGES

JUDGED_STATUSES = (
    SubmissionStatus.ACCEPTED,
    SubmissionStatus.WRONG_ANSWER,
    SubmissionStatus.RUNTIME_ERROR,
    SubmissionStatus.TIME_LIMIT_EXCEEDED,
)

# Difficulty ranking (for picking a chapter's overall difficulty from its
# problems) and the XP a solved problem of that difficulty is worth. This is a
# display-only currency for the learning path, independent of the classroom
# scoring/points system.
DIFFICULTY_RANK = {"EASY": 0, "MEDIUM": 1, "HARD": 2}
XP_BY_DIFFICULTY = {"EASY": 25, "MEDIUM": 50, "HARD": 100}


class LearningService:
    """
    Self-paced, Duolingo-style learning paths: one ordered sequence of chapters
    per language, each chapter a set of existing Problems. A chapter unlocks
    once the previous chapter in that language's sequence is fully solved.
    Content is a fixed, built-in curriculum (see core/seed_learning_curriculum.py),
    not teacher-editable - this service is read-only, student-facing.
    """

    @staticmethod
    def _validate_language(language: str) -> str:
        language = language.lower()
        if language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
            )
        return language

    @staticmethod
    def _problem_summaries(chapter: LearningChapter, solved_problem_ids: set) -> List[Dict[str, Any]]:
        summaries = []
        for cp in chapter.problems:
            prob = cp.problem
            summaries.append({
                "problem_id": cp.problem_id,
                "title": prob.title if prob else f"Problem #{cp.problem_id}",
                "difficulty": prob.difficulty.value if prob and hasattr(prob.difficulty, "value") else "UNKNOWN",
                "order": cp.order,
                "solved": cp.problem_id in solved_problem_ids,
            })
        return summaries

    @staticmethod
    def _chapter_difficulty(chapter: LearningChapter) -> str:
        best = "EASY"
        for cp in chapter.problems:
            if not cp.problem:
                continue
            d = cp.problem.difficulty.value if hasattr(cp.problem.difficulty, "value") else str(cp.problem.difficulty)
            if DIFFICULTY_RANK.get(d, 0) > DIFFICULTY_RANK.get(best, 0):
                best = d
        return best

    @staticmethod
    def _cleanly_solved_problem_ids(db: Session, student_id: int) -> set:
        """
        Problem ids where the student's very first judged submission was
        ACCEPTED (no wrong attempts before getting it right) - used to tell
        "merely completed" apart from "mastered".
        """
        submissions = db.query(Submission).filter(
            Submission.user_id == student_id, Submission.status.in_(JUDGED_STATUSES)
        ).order_by(Submission.created_at.asc(), Submission.id.asc()).all()

        first_status: Dict[int, SubmissionStatus] = {}
        for s in submissions:
            if s.problem_id not in first_status:
                first_status[s.problem_id] = s.status
        return {pid for pid, st in first_status.items() if st == SubmissionStatus.ACCEPTED}

    @staticmethod
    def get_path_for_student(db: Session, student_id: int, language: str) -> List[Dict[str, Any]]:
        language = LearningService._validate_language(language)
        chapters = db.query(LearningChapter).filter(
            LearningChapter.language == language
        ).order_by(LearningChapter.order, LearningChapter.id).all()

        solved_problem_ids = {
            row[0] for row in db.query(Submission.problem_id).filter(
                Submission.user_id == student_id, Submission.status == SubmissionStatus.ACCEPTED
            ).distinct()
        }
        clean_solved_ids = LearningService._cleanly_solved_problem_ids(db, student_id)

        path = []
        previous_completed = True  # the first chapter in the sequence is always unlocked
        previous_title: Optional[str] = None
        for chapter in chapters:
            problem_ids = [cp.problem_id for cp in chapter.problems]
            total = len(problem_ids)
            completed = sum(1 for pid in problem_ids if pid in solved_problem_ids)
            is_completed = total > 0 and completed == total
            is_unlocked = previous_completed
            is_mastered = is_completed and all(pid in clean_solved_ids for pid in problem_ids)

            if not is_unlocked:
                state = "LOCKED"
            elif is_mastered:
                state = "MASTERED"
            elif is_completed:
                state = "COMPLETED"
            elif completed > 0:
                state = "IN_PROGRESS"
            else:
                state = "AVAILABLE"

            difficulty = LearningService._chapter_difficulty(chapter)
            xp_per_problem = XP_BY_DIFFICULTY.get(difficulty, 25)

            path.append({
                "id": chapter.id, "language": chapter.language, "title": chapter.title,
                "description": chapter.description, "order": chapter.order,
                "difficulty": difficulty,
                "total_problems": total, "completed_problems": completed,
                "progress_pct": round(completed / total * 100.0, 1) if total else 0.0,
                "xp_reward": xp_per_problem * total,
                "xp_earned": xp_per_problem * completed,
                "state": state,
                "is_unlocked": is_unlocked, "is_completed": is_completed, "is_mastered": is_mastered,
                "prerequisite_title": previous_title if not is_unlocked else None,
                "problems": LearningService._problem_summaries(chapter, solved_problem_ids),
            })
            previous_completed = is_completed
            previous_title = chapter.title

        return path

    @staticmethod
    def get_chapter_detail_for_student(db: Session, student_id: int, chapter_id: int) -> Dict[str, Any]:
        chapter = db.query(LearningChapter).filter(LearningChapter.id == chapter_id).first()
        if not chapter:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")

        path = LearningService.get_path_for_student(db, student_id, chapter.language)
        item = next((c for c in path if c["id"] == chapter_id), None)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
        if not item["is_unlocked"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Complete the previous chapter to unlock this one."
            )
        return item
