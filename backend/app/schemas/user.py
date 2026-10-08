from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole

class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["John"])
    email: EmailStr = Field(..., examples=["john@gmail.com"])
    password: str = Field(..., min_length=6, examples=["password"])
    role: UserRole = Field(..., examples=[UserRole.STUDENT])

class UserLogin(BaseModel):
    email: EmailStr = Field(..., examples=["john@gmail.com"])
    password: str = Field(..., examples=["password"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True
