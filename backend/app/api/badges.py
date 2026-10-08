from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user, get_current_student
from app.schemas.badge import BadgeCatalogItem, BadgeStatus
from app.services.badge_service import BadgeService

router = APIRouter(
    prefix="/badges",
    tags=["Badges"]
)


@router.get("", response_model=List[BadgeCatalogItem])
def list_badge_catalog(current_user: User = Depends(get_current_user)):
    """Full badge catalog (earned or not), for rendering a locked/unlocked badge case."""
    return BadgeService.get_catalog()


@router.get("/me", response_model=List[BadgeStatus])
def get_my_badges(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """
    Full badge catalog merged with the current student's progress: earned
    badges carry earned_at; locked ones carry a short unlock_hint showing how
    close the student is (e.g. "7/10 problems solved").
    """
    return BadgeService.get_status_for_student(db, current_student.id)
