from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.classroom import ClassroomMember
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomJoin,
    ClassroomResponse,
    ClassroomDetailResponse,
    ClassroomSettingsUpdate,
    StudentOut
)
from app.schemas.student_profile import RosterEntry, StudentProfileResponse, SubmissionCodeResponse
from app.dependencies.auth import get_current_user, get_current_teacher, get_current_student
from app.services.classroom_service import ClassroomService
from app.services.student_profile_service import StudentProfileService

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


# Teacher → Student Performance Profile (read-only).
# Every endpoint verifies: user is a teacher AND owns the classroom AND the student is enrolled.
@router.get("/{classroom_id}/students", response_model=List[RosterEntry])
def get_classroom_student_roster(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    classroom, _ = StudentProfileService.authorize(db, current_user, classroom_id)
    return StudentProfileService.get_roster(db, classroom)


@router.get("/{classroom_id}/students/{student_id}/profile", response_model=StudentProfileResponse)
def get_student_profile(
    classroom_id: int,
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    classroom, membership = StudentProfileService.authorize(db, current_user, classroom_id, student_id)
    return StudentProfileService.get_profile(db, classroom, membership)


@router.get("/{classroom_id}/students/{student_id}/submissions/{submission_id}", response_model=SubmissionCodeResponse)
def get_student_submission_code(
    classroom_id: int,
    student_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    classroom, _ = StudentProfileService.authorize(db, current_user, classroom_id, student_id)
    return StudentProfileService.get_submission_code(db, classroom, student_id, submission_id)

# Teacher Endpoints
@router.post("", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
def create_classroom(
    schema: ClassroomCreate,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    return ClassroomService.create_classroom(db, current_teacher.id, schema)

@router.get("/my", response_model=List[ClassroomResponse])
def get_teacher_classrooms(
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    return ClassroomService.get_teacher_classrooms(db, current_teacher.id)

# Student Endpoints
@router.post("/join", response_model=ClassroomResponse)
def join_classroom(
    schema: ClassroomJoin,
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    return ClassroomService.join_classroom(db, current_student.id, schema)

@router.get("/joined", response_model=List[ClassroomResponse])
def get_student_joined_classrooms(
    db: Session = Depends(get_db),
    current_student: User = Depends(get_current_student)
):
    return ClassroomService.get_student_joined_classrooms(db, current_student.id)

# Shared / Detail Endpoints
@router.get("/{classroom_id}", response_model=ClassroomDetailResponse)
def get_classroom_detail(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    classroom = ClassroomService.get_classroom_by_id(db, classroom_id)
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    
    # Permission check: User must be the teacher owner OR an enrolled student
    if current_user.role == UserRole.TEACHER:
        if classroom.teacher_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this classroom")
    else:
        membership = db.query(ClassroomMember).filter(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.student_id == current_user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not enrolled in this classroom")
    
    # Fetch enrolled students
    members = db.query(ClassroomMember).filter(ClassroomMember.classroom_id == classroom.id).all()
    students_list = []
    for m in members:
        if m.student:
            students_list.append(StudentOut(
                id=m.student.id,
                name=m.student.name,
                email=m.student.email,
                joined_at=m.joined_at
            ))

    return ClassroomDetailResponse(
        id=classroom.id,
        teacher_id=classroom.teacher_id,
        name=classroom.name,
        description=classroom.description,
        join_code=classroom.join_code,
        disable_paste=classroom.disable_paste,
        created_at=classroom.created_at,
        students=students_list
    )

@router.patch("/{classroom_id}/settings", response_model=ClassroomResponse)
def update_classroom_settings(
    classroom_id: int,
    schema: ClassroomSettingsUpdate,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    """Teacher-only. Currently controls whether students can paste into the code editor for this classroom."""
    return ClassroomService.update_settings(db, classroom_id, current_teacher.id, schema)

@router.delete("/{classroom_id}", status_code=status.HTTP_200_OK)
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: User = Depends(get_current_teacher)
):
    ClassroomService.delete_classroom(db, classroom_id, current_teacher.id)
    return {"message": f"Classroom {classroom_id} deleted successfully"}
