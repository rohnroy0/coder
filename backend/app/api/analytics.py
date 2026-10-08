from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.classroom import Classroom, ClassroomMember
from app.dependencies.auth import get_current_user, get_current_student, get_current_teacher
from app.schemas.analytics import (
    StudentAnalyticsResponse,
    ClassroomAnalyticsResponse,
    LeaderboardEntrySchema
)
from app.services.analytics_service import AnalyticsService
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Leaderboard"]
)

@router.get("/student/me", response_model=StudentAnalyticsResponse)
def get_my_analytics(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    """
    Returns performance analytics for the currently authenticated student.
    """
    return AnalyticsService.get_student_analytics(db, current_student.id)

@router.get("/student/{student_id}", response_model=StudentAnalyticsResponse)
def get_student_analytics_by_id(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns performance analytics for a specific student.
    - Students can ONLY access their own analytics.
    - Teachers can ONLY access analytics for students in classrooms they manage.
    """
    if current_user.role == UserRole.STUDENT:
        if current_user.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view another student's analytics."
            )
    elif current_user.role == UserRole.TEACHER:
        # Check if student is in any classroom owned by teacher
        teacher_classroom_tuples = db.query(Classroom.id).filter(Classroom.teacher_id == current_user.id).all()
        teacher_classroom_ids = [c[0] for c in teacher_classroom_tuples]

        is_student_in_classroom = False
        if teacher_classroom_ids:
            is_student_in_classroom = db.query(ClassroomMember).filter(
                ClassroomMember.student_id == student_id,
                ClassroomMember.classroom_id.in_(teacher_classroom_ids)
            ).first() is not None

        if not is_student_in_classroom:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Student is not enrolled in any of your classrooms."
            )

    return AnalyticsService.get_student_analytics(db, student_id)

@router.get("/classroom/{classroom_id}", response_model=ClassroomAnalyticsResponse)
def get_classroom_analytics(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns class overview analytics, topic strength analysis, struggling students, and leaderboard.
    - Teachers can access their owned classrooms.
    - Students can access classrooms they are enrolled in.
    - Unrelated users are rejected with 403 Forbidden.
    """
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    if current_user.role == UserRole.TEACHER:
        if classroom.teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this classroom's analytics")
    else:
        membership = db.query(ClassroomMember).filter(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.student_id == current_user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You are not enrolled in this classroom")

    return AnalyticsService.get_classroom_analytics(db, classroom_id)

@router.get("/classroom/{classroom_id}/leaderboard", response_model=List[LeaderboardEntrySchema])
def get_classroom_leaderboard(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns deterministic rank-ordered leaderboard for a classroom.
    - Teachers can access their owned classrooms.
    - Students can access classrooms they are enrolled in.
    - Unrelated users are rejected with 403 Forbidden.
    """
    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    if current_user.role == UserRole.TEACHER:
        if classroom.teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this classroom leaderboard")
    else:
        membership = db.query(ClassroomMember).filter(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.student_id == current_user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You are not enrolled in this classroom")

    return LeaderboardService.get_classroom_leaderboard(db, classroom_id)
