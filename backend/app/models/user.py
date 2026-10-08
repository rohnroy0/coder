from app.core.time import utcnow
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database.base import Base

class UserRole(str, enum.Enum):
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Relationships
    classrooms_created = relationship("Classroom", back_populates="teacher", cascade="all, delete-orphan")
    classroom_memberships = relationship("ClassroomMember", back_populates="student", cascade="all, delete-orphan")
