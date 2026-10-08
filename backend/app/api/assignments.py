from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    AssignmentStudentProgressResponse
)
from app.dependencies.auth import get_current_user, get_current_teacher
from app.services.assignment_service import AssignmentService

router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"]
)

@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_in: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher creates a new assignment for a classroom.
    """
    return AssignmentService.create_assignment(db, current_user.id, assignment_in)

@router.get("/classroom/{classroom_id}", response_model=List[AssignmentResponse])
def get_classroom_assignments(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List assignments for a classroom.
    Teachers see all draft/published/closed assignments.
    Students see only published or closed assignments.
    """
    return AssignmentService.list_assignments_for_classroom(db, classroom_id, current_user)

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed assignment info (includes problems and student progress context).
    """
    return AssignmentService.get_assignment_detail(db, assignment_id, current_user)

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    assignment_in: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher updates an existing assignment.
    """
    return AssignmentService.update_assignment(db, assignment_id, current_user.id, assignment_in)

@router.post("/{assignment_id}/publish", response_model=AssignmentResponse)
def publish_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher publishes an assignment (changes status DRAFT -> PUBLISHED).
    """
    return AssignmentService.publish_assignment(db, assignment_id, current_user.id)

@router.post("/{assignment_id}/close", response_model=AssignmentResponse)
def close_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher closes an assignment (changes status -> CLOSED).
    """
    return AssignmentService.close_assignment(db, assignment_id, current_user.id)

@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher deletes an assignment.
    """
    AssignmentService.delete_assignment(db, assignment_id, current_user.id)

@router.get("/{assignment_id}/progress", response_model=List[AssignmentStudentProgressResponse])
def get_assignment_progress(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Teacher views progress of all students for an assignment.
    """
    detail = AssignmentService.get_assignment_detail(db, assignment_id, current_user)
    return detail.get("student_progress_list", [])
