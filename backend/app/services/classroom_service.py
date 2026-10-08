import random
import string
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.classroom import Classroom, ClassroomMember
from app.models.user import User
from app.schemas.classroom import ClassroomCreate, ClassroomJoin, ClassroomSettingsUpdate

def generate_unique_join_code(db: Session, prefix: str = "PY") -> str:
    """Generate a unique 7-character join code like PY10192"""
    while True:
        # Prefix 2 chars + 5 random digits/uppercase letters
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        code = f"{prefix[:2].upper()}{random_suffix}"
        
        # Verify uniqueness in DB
        existing = db.query(Classroom).filter(Classroom.join_code == code).first()
        if not existing:
            return code

class ClassroomService:

    @staticmethod
    def create_classroom(db: Session, teacher_id: int, schema: ClassroomCreate) -> Classroom:
        join_code = generate_unique_join_code(db, prefix=schema.name[:2] if len(schema.name) >= 2 else "CR")
        classroom = Classroom(
            teacher_id=teacher_id,
            name=schema.name,
            description=schema.description,
            join_code=join_code
        )
        db.add(classroom)
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def get_teacher_classrooms(db: Session, teacher_id: int) -> List[Classroom]:
        return db.query(Classroom).filter(Classroom.teacher_id == teacher_id).order_by(Classroom.created_at.desc()).all()

    @staticmethod
    def get_classroom_by_id(db: Session, classroom_id: int) -> Optional[Classroom]:
        return db.query(Classroom).filter(Classroom.id == classroom_id).first()

    @staticmethod
    def delete_classroom(db: Session, classroom_id: int, teacher_id: int) -> bool:
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classroom not found"
            )
        if classroom.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this classroom"
            )
        db.delete(classroom)
        db.commit()
        return True

    @staticmethod
    def join_classroom(db: Session, student_id: int, schema: ClassroomJoin) -> Classroom:
        classroom = db.query(Classroom).filter(Classroom.join_code == schema.join_code.strip().upper()).first()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid join code. Classroom not found."
            )
        
        # Check if already joined
        existing_membership = db.query(ClassroomMember).filter(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.student_id == student_id
        ).first()

        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student is already enrolled in this classroom."
            )

        membership = ClassroomMember(
            classroom_id=classroom.id,
            student_id=student_id
        )
        db.add(membership)
        db.commit()
        return classroom

    @staticmethod
    def update_settings(db: Session, classroom_id: int, teacher_id: int, schema: ClassroomSettingsUpdate) -> Classroom:
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
        if classroom.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to modify this classroom"
            )
        classroom.disable_paste = schema.disable_paste
        db.commit()
        db.refresh(classroom)
        return classroom

    @staticmethod
    def get_student_joined_classrooms(db: Session, student_id: int) -> List[Classroom]:
        memberships = db.query(ClassroomMember).filter(ClassroomMember.student_id == student_id).all()
        classroom_ids = [m.classroom_id for m in memberships]
        if not classroom_ids:
            return []
        return db.query(Classroom).filter(Classroom.id.in_(classroom_ids)).order_by(Classroom.created_at.desc()).all()
