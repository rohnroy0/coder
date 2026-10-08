from app.core.time import utcnow
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.assignment import Assignment, AssignmentStatus

class DeadlineService:

    @staticmethod
    def is_assignment_overdue(assignment: Assignment, now: Optional[datetime] = None) -> bool:
        if assignment.status == AssignmentStatus.CLOSED:
            return True
        if assignment.due_at is None:
            return False
        
        current_time = now or utcnow()
        due_at = assignment.due_at
        if due_at.tzinfo is not None:
            due_at = due_at.replace(tzinfo=None)
        if current_time.tzinfo is not None:
            current_time = current_time.replace(tzinfo=None)
            
        return current_time > due_at

    @staticmethod
    def check_submission_allowed(assignment: Assignment):
        if assignment.status == AssignmentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment is not published."
            )
        if DeadlineService.is_assignment_overdue(assignment):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed."
            )
