"""Add assignment models

Revision ID: g789abcdef01
Revises: f6789abcdef0
Create Date: 2026-09-25 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g789abcdef01'
down_revision: Union[str, None] = 'f6789abcdef0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'PUBLISHED', 'CLOSED', name='assignmentstatus'),
            nullable=False
        ),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_id'), 'assignments', ['id'], unique=False)

    # 2. Create assignment_problems table
    op.create_table(
        'assignment_problems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignment_problems_id'), 'assignment_problems', ['id'], unique=False)

    # 3. Create assignment_student_progress table
    op.create_table(
        'assignment_student_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('completed_problems', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_problems', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column(
            'status',
            sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', name='assignmentprogressstatus'),
            nullable=False
        ),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', 'student_id', name='uq_assignment_student')
    )
    op.create_index(op.f('ix_assignment_student_progress_id'), 'assignment_student_progress', ['id'], unique=False)

    # 4. Add assignment_id to submissions table
    op.add_column('submissions', sa.Column('assignment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_submissions_assignment_id',
        'submissions', 'assignments',
        ['assignment_id'], ['id'],
        ondelete='SET NULL'
    )

def downgrade() -> None:
    op.drop_constraint('fk_submissions_assignment_id', 'submissions', type_='foreignkey')
    op.drop_column('submissions', 'assignment_id')
    op.drop_index(op.f('ix_assignment_student_progress_id'), table_name='assignment_student_progress')
    op.drop_table('assignment_student_progress')
    op.drop_index(op.f('ix_assignment_problems_id'), table_name='assignment_problems')
    op.drop_table('assignment_problems')
    op.drop_index(op.f('ix_assignments_id'), table_name='assignments')
    op.drop_table('assignments')
