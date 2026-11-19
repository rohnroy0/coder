import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Teacher accounts see every student's work in their classrooms, so when a
    # signup code is configured, becoming one requires it. compare_digest, not
    # ==, to avoid leaking the code through response timing.
    if user_in.role == UserRole.TEACHER and settings.TEACHER_SIGNUP_CODE:
        supplied = user_in.teacher_code or ""
        if not secrets.compare_digest(supplied, settings.TEACHER_SIGNUP_CODE):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A valid teacher signup code is required to register a teacher account."
            )

    # Validate unique email
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        name=user_in.name,
        email=user_in.email.lower(),
        password_hash=hashed_pwd,
        role=user_in.role
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two concurrent registrations of the same email both passed the check
        # above; the unique constraint catches the loser - report it as the
        # normal duplicate-email error instead of a 500.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email.lower()).first()
    if not user or not verify_password(login_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
