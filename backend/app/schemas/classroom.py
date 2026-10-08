from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ClassroomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, examples=["Python Basics"])
    description: Optional[str] = Field(None, examples=["Learning Python"])

class ClassroomJoin(BaseModel):
    join_code: str = Field(..., examples=["PY10192"])

class ClassroomSettingsUpdate(BaseModel):
    disable_paste: bool

class StudentOut(BaseModel):
    id: int
    name: str
    email: str
    joined_at: datetime

    class Config:
        from_attributes = True

class ClassroomResponse(BaseModel):
    id: int
    teacher_id: int
    name: str
    description: Optional[str] = None
    join_code: str
    disable_paste: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class ClassroomDetailResponse(BaseModel):
    id: int
    teacher_id: int
    name: str
    description: Optional[str] = None
    join_code: str
    disable_paste: bool = False
    created_at: datetime
    students: List[StudentOut] = []

    class Config:
        from_attributes = True
