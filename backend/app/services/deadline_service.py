from app.core.time import utcnow, to_naive_utc
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

        current_time = to_naive_utc(now or utcnow())
        due_at = to_naive_utc(assignment.due_at)

        return current_time > due_at

    @staticmethod
    def is_assignment_open(assignment: Assignment, now: Optional[datetime] = None) -> bool:
        """True only when submissions should count toward this assignment:
        published, started (start_at reached, if set), and not past due."""
        if assignment.status != AssignmentStatus.PUBLISHED:
            return False
        if assignment.start_at is not None:
            current_time = to_naive_utc(now or utcnow())
            if current_time < to_naive_utc(assignment.start_at):
                return False
        return not DeadlineService.is_assignment_overdue(assignment, now)

    @staticmethod
    def check_submission_allowed(assignment: Assignment):
        if assignment.status == AssignmentStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment is not published."
            )
        if assignment.start_at is not None and to_naive_utc(utcnow()) < to_naive_utc(assignment.start_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment has not started yet."
            )
        if DeadlineService.is_assignment_overdue(assignment):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment deadline has passed."
            )
