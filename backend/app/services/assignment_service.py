from app.core.time import utcnow
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.assignment import (
    Assignment, AssignmentStatus, AssignmentProblem,
    AssignmentStudentProgress, AssignmentProgressStatus
)
from app.models.classroom import Classroom, ClassroomMember
from app.models.problem import Problem, ProblemStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.user import User, UserRole
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.services.deadline_service import DeadlineService


class AssignmentService:

    @staticmethod
    def _verify_teacher_classroom_ownership(db: Session, classroom_id: int, teacher_id: int) -> Classroom:
        classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classroom not found"
            )
        if classroom.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this classroom"
            )
        return classroom

    @staticmethod
    def _verify_student_classroom_membership(db: Session, classroom_id: int, student_id: int):
        member = db.query(ClassroomMember).filter(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.student_id == student_id
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not enrolled in this classroom"
            )

    @staticmethod
    def _initialize_student_progress(db: Session, assignment: Assignment):
        """Ensure AssignmentStudentProgress records exist for all classroom members."""
        members = db.query(ClassroomMember).filter(
            ClassroomMember.classroom_id == assignment.classroom_id
        ).all()
        total_problems = len(assignment.problems)

        for m in members:
            prog = db.query(AssignmentStudentProgress).filter(
                AssignmentStudentProgress.assignment_id == assignment.id,
                AssignmentStudentProgress.student_id == m.student_id
            ).first()
            if not prog:
                prog = AssignmentStudentProgress(
                    assignment_id=assignment.id,
                    student_id=m.student_id,
                    completed_problems=0,
                    total_problems=total_problems,
                    score=0,
                    status=AssignmentProgressStatus.NOT_STARTED
                )
                db.add(prog)
            else:
                prog.total_problems = total_problems
        db.flush()

    @staticmethod
    def create_assignment(db: Session, teacher_id: int, schema: AssignmentCreate) -> Assignment:
        AssignmentService._verify_teacher_classroom_ownership(db, schema.classroom_id, teacher_id)

        # Create base assignment
        assignment = Assignment(
            classroom_id=schema.classroom_id,
            teacher_id=teacher_id,
            title=schema.title,
            description=schema.description,
            status=AssignmentStatus.DRAFT,
            start_at=schema.start_at,
            due_at=schema.due_at,
            total_points=0,
            created_at=utcnow(),
            updated_at=utcnow()
        )
        db.add(assignment)
        db.flush()

        total_pts = 0
        for p_item in schema.problems:
            prob = db.query(Problem).filter(Problem.id == p_item.problem_id).first()
            if not prob:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Problem {p_item.problem_id} not found"
                )
            if prob.status != ProblemStatus.VERIFIED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Only verified problems can be added to assignments. Problem '{prob.title}' is unverified."
                )
            ap = AssignmentProblem(
                assignment_id=assignment.id,
                problem_id=p_item.problem_id,
                points=p_item.points,
                order=p_item.order
            )
            db.add(ap)
            total_pts += p_item.points

        assignment.total_points = total_pts
        db.commit()
        db.refresh(assignment)

        # Pre-initialize student progress
        AssignmentService._initialize_student_progress(db, assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def update_assignment(db: Session, assignment_id: int, teacher_id: int, schema: AssignmentUpdate) -> Assignment:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        AssignmentService._verify_teacher_classroom_ownership(db, assignment.classroom_id, teacher_id)

        if schema.title is not None:
            assignment.title = schema.title
        if schema.description is not None:
            assignment.description = schema.description
        if schema.start_at is not None:
            assignment.start_at = schema.start_at
        if schema.due_at is not None:
            assignment.due_at = schema.due_at

        if schema.status is not None and schema.status != assignment.status:
            if schema.status == AssignmentStatus.PUBLISHED and assignment.published_at is None:
                assignment.published_at = utcnow()
            assignment.status = schema.status

        if schema.problems is not None:
            # Delete old problems
            db.query(AssignmentProblem).filter(AssignmentProblem.assignment_id == assignment.id).delete()
            total_pts = 0
            for p_item in schema.problems:
                prob = db.query(Problem).filter(Problem.id == p_item.problem_id).first()
                if not prob:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Problem {p_item.problem_id} not found"
                    )
                if prob.status != ProblemStatus.VERIFIED:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Only verified problems can be added to assignments. Problem '{prob.title}' is unverified."
                    )
                ap = AssignmentProblem(
                    assignment_id=assignment.id,
                    problem_id=p_item.problem_id,
                    points=p_item.points,
                    order=p_item.order
                )
                db.add(ap)
                total_pts += p_item.points
            assignment.total_points = total_pts

        assignment.updated_at = utcnow()
        db.commit()
        db.refresh(assignment)

        AssignmentService._initialize_student_progress(db, assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def publish_assignment(db: Session, assignment_id: int, teacher_id: int) -> Assignment:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        AssignmentService._verify_teacher_classroom_ownership(db, assignment.classroom_id, teacher_id)

        assignment.status = AssignmentStatus.PUBLISHED
        if assignment.published_at is None:
            assignment.published_at = utcnow()
        assignment.updated_at = utcnow()

        db.commit()
        db.refresh(assignment)
        AssignmentService._initialize_student_progress(db, assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def close_assignment(db: Session, assignment_id: int, teacher_id: int) -> Assignment:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        AssignmentService._verify_teacher_classroom_ownership(db, assignment.classroom_id, teacher_id)

        assignment.status = AssignmentStatus.CLOSED
        assignment.updated_at = utcnow()

        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def delete_assignment(db: Session, assignment_id: int, teacher_id: int):
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
        AssignmentService._verify_teacher_classroom_ownership(db, assignment.classroom_id, teacher_id)
        db.delete(assignment)
        db.commit()

    @staticmethod
    def get_assignment_detail(db: Session, assignment_id: int, current_user: User) -> dict:
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )

        if current_user.role == UserRole.TEACHER:
            AssignmentService._verify_teacher_classroom_ownership(db, assignment.classroom_id, current_user.id)
        else:
            AssignmentService._verify_student_classroom_membership(db, assignment.classroom_id, current_user.id)
            if assignment.status == AssignmentStatus.DRAFT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Assignment is not available."
                )

        # Problems this student has already solved (any ACCEPTED submission),
        # so the roster can mark them solved without blocking re-attempts.
        solved_problem_ids = set()
        if current_user.role == UserRole.STUDENT:
            solved_problem_ids = {
                row[0] for row in db.query(Submission.problem_id).filter(
                    Submission.user_id == current_user.id,
                    Submission.status == SubmissionStatus.ACCEPTED
                ).distinct().all()
            }

        # Build problems list formatted
        problems_data = []
        for ap in assignment.problems:
            prob = db.query(Problem).filter(Problem.id == ap.problem_id).first()
            problems_data.append({
                "id": ap.id,
                "assignment_id": ap.assignment_id,
                "problem_id": ap.problem_id,
                "points": ap.points,
                "order": ap.order,
                "title": prob.title if prob else "Unknown",
                "difficulty": prob.difficulty.value if prob and hasattr(prob.difficulty, 'value') else (prob.difficulty if prob else None),
                "topic": prob.topic if prob else None,
                "solved": ap.problem_id in solved_problem_ids
            })

        result = {
            "id": assignment.id,
            "classroom_id": assignment.classroom_id,
            "teacher_id": assignment.teacher_id,
            "title": assignment.title,
            "description": assignment.description,
            "status": assignment.status.value,
            "start_at": assignment.start_at,
            "due_at": assignment.due_at,
            "total_points": assignment.total_points,
            "created_at": assignment.created_at,
            "updated_at": assignment.updated_at,
            "published_at": assignment.published_at,
            "problems": problems_data,
            "my_progress": None,
            "student_progress_list": None
        }

        if current_user.role == UserRole.STUDENT:
            prog = db.query(AssignmentStudentProgress).filter(
                AssignmentStudentProgress.assignment_id == assignment.id,
                AssignmentStudentProgress.student_id == current_user.id
            ).first()
            if not prog:
                prog = AssignmentStudentProgress(
                    assignment_id=assignment.id,
                    student_id=current_user.id,
                    completed_problems=0,
                    total_problems=len(assignment.problems),
                    score=0,
                    status=AssignmentProgressStatus.NOT_STARTED
                )
                db.add(prog)
                db.commit()
                db.refresh(prog)

            # Check overdue
            if DeadlineService.is_assignment_overdue(assignment) and prog.status != AssignmentProgressStatus.COMPLETED:
                prog.status = AssignmentProgressStatus.OVERDUE
                db.commit()

            result["my_progress"] = {
                "id": prog.id,
                "assignment_id": prog.assignment_id,
                "student_id": prog.student_id,
                "completed_problems": prog.completed_problems,
                "total_problems": prog.total_problems,
                "score": prog.score,
                "status": prog.status.value,
                "last_activity_at": prog.last_activity_at,
                "completed_at": prog.completed_at
            }
        else:
            # Teacher view: include progress list for all students
            progress_list = []
            progs = db.query(AssignmentStudentProgress).filter(
                AssignmentStudentProgress.assignment_id == assignment.id
            ).all()
            for p in progs:
                st = db.query(User).filter(User.id == p.student_id).first()
                if DeadlineService.is_assignment_overdue(assignment) and p.status != AssignmentProgressStatus.COMPLETED:
                    p.status = AssignmentProgressStatus.OVERDUE

                progress_list.append({
                    "id": p.id,
                    "assignment_id": p.assignment_id,
                    "student_id": p.student_id,
                    "student_name": st.name if st else "Student",
                    "completed_problems": p.completed_problems,
                    "total_problems": p.total_problems,
                    "score": p.score,
                    "status": p.status.value,
                    "last_activity_at": p.last_activity_at,
                    "completed_at": p.completed_at
                })
            result["student_progress_list"] = progress_list

        return result

    @staticmethod
    def list_assignments_for_classroom(db: Session, classroom_id: int, current_user: User) -> List[dict]:
        if current_user.role == UserRole.TEACHER:
            AssignmentService._verify_teacher_classroom_ownership(db, classroom_id, current_user.id)
            assignments = db.query(Assignment).filter(Assignment.classroom_id == classroom_id).order_by(Assignment.created_at.desc()).all()
        else:
            AssignmentService._verify_student_classroom_membership(db, classroom_id, current_user.id)
            assignments = db.query(Assignment).filter(
                Assignment.classroom_id == classroom_id,
                Assignment.status != AssignmentStatus.DRAFT
            ).order_by(Assignment.created_at.desc()).all()

        results = []
        for assign in assignments:
            item = AssignmentService.get_assignment_detail(db, assign.id, current_user)
            results.append(item)
        return results

    @staticmethod
    def sync_student_progress_on_submission(
        db: Session,
        assignment_id: int,
        student_id: int,
        problem_id: int,
        submission_status: SubmissionStatus
    ):
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            return

        prog = db.query(AssignmentStudentProgress).filter(
            AssignmentStudentProgress.assignment_id == assignment_id,
            AssignmentStudentProgress.student_id == student_id
        ).first()

        total_problems = len(assignment.problems)
        if not prog:
            prog = AssignmentStudentProgress(
                assignment_id=assignment_id,
                student_id=student_id,
                completed_problems=0,
                total_problems=total_problems,
                score=0,
                status=AssignmentProgressStatus.NOT_STARTED
            )
            db.add(prog)
            db.flush()

        prog.total_problems = total_problems
        prog.last_activity_at = utcnow()

        if prog.status == AssignmentProgressStatus.NOT_STARTED:
            prog.status = AssignmentProgressStatus.IN_PROGRESS

        # Recomputed from scratch (not incremented) so a problem counts as
        # complete for this assignment the moment the student has ANY
        # ACCEPTED submission for it - whether made through this assignment's
        # own link, a different assignment sharing the same problem, or the
        # general problem browser. This also makes the function idempotent:
        # calling it again for the same event can't double-count.
        assignment_problem_ids = [ap.problem_id for ap in assignment.problems]
        solved_ids = set()
        if assignment_problem_ids:
            solved_ids = {
                row[0] for row in db.query(Submission.problem_id).filter(
                    Submission.user_id == student_id,
                    Submission.problem_id.in_(assignment_problem_ids),
                    Submission.status == SubmissionStatus.ACCEPTED
                ).distinct()
            }

        prog.completed_problems = len(solved_ids)
        prog.score = sum(ap.points for ap in assignment.problems if ap.problem_id in solved_ids)

        if prog.completed_problems >= total_problems and total_problems > 0:
            prog.status = AssignmentProgressStatus.COMPLETED
            if not prog.completed_at:
                prog.completed_at = utcnow()

        db.commit()

    @staticmethod
    def find_student_assignments_for_problem(db: Session, student_id: int, problem_id: int) -> set:
        """
        IDs of every non-draft assignment containing this problem, in a classroom
        the student belongs to. Used to retroactively sync progress on assignments
        a solved problem belongs to even when the submission that solved it wasn't
        made through that assignment's own link.
        """
        classroom_ids = [
            row[0] for row in db.query(ClassroomMember.classroom_id).filter(
                ClassroomMember.student_id == student_id
            )
        ]
        if not classroom_ids:
            return set()

        rows = db.query(Assignment.id).join(
            AssignmentProblem, AssignmentProblem.assignment_id == Assignment.id
        ).filter(
            Assignment.classroom_id.in_(classroom_ids),
            Assignment.status != AssignmentStatus.DRAFT,
            AssignmentProblem.problem_id == problem_id
        )
        return {row[0] for row in rows}
