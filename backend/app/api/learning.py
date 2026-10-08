from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.dependencies.auth import get_current_student
from app.schemas.learning import ChapterPathItem
from app.services.learning_service import LearningService

router = APIRouter(
    prefix="/learning",
    tags=["Learning Paths"]
)


@router.get("/path/{language}", response_model=List[ChapterPathItem])
def get_learning_path(
    language: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    Student's view of one language's full chapter sequence (fixed, built-in
    curriculum), with per-chapter progress and lock state - chapter N unlocks
    once chapter N-1 is fully solved.
    """
    return LearningService.get_path_for_student(db, current_user.id, language)


@router.get("/chapters/{chapter_id}/detail", response_model=ChapterPathItem)
def get_chapter_detail(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Single chapter detail for a student. 403 if the chapter is still locked."""
    return LearningService.get_chapter_detail_for_student(db, current_user.id, chapter_id)
