"""Add student_points_events model

Revision ID: f6789abcdef0
Revises: e56789abcdef
Create Date: 2026-09-25 07:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6789abcdef0'
down_revision: Union[str, None] = 'e56789abcdef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'student_points_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('classroom_id', sa.Integer(), nullable=True),
        sa.Column('submission_id', sa.Integer(), nullable=True),
        sa.Column(
            'event_type',
            sa.Enum(
                'ACCEPTED', 'FAST_BONUS', 'QUALITY_BONUS',
                'WRONG_ANSWER', 'RUNTIME_ERROR', 'TIME_LIMIT_EXCEEDED',
                name='pointeventtype'
            ),
            nullable=False
        ),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_points_events_id'), 'student_points_events', ['id'], unique=False)
    op.create_index(op.f('ix_student_points_events_student_id'), 'student_points_events', ['student_id'], unique=False)
    op.create_index(op.f('ix_student_points_events_classroom_id'), 'student_points_events', ['classroom_id'], unique=False)
    op.create_index(op.f('ix_student_points_events_submission_id'), 'student_points_events', ['submission_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_student_points_events_submission_id'), table_name='student_points_events')
    op.drop_index(op.f('ix_student_points_events_classroom_id'), table_name='student_points_events')
    op.drop_index(op.f('ix_student_points_events_student_id'), table_name='student_points_events')
    op.drop_index(op.f('ix_student_points_events_id'), table_name='student_points_events')
    op.drop_table('student_points_events')
