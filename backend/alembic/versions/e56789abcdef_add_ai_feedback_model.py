"""Add ai_feedback model

Revision ID: e56789abcdef
Revises: d43ac86092f7
Create Date: 2026-09-24 14:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e56789abcdef'
down_revision: Union[str, None] = 'd43ac86092f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'ai_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('hint_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column(
            'error_type',
            sa.Enum(
                'LOGIC_ERROR', 'SYNTAX_ERROR', 'RUNTIME_ERROR', 'ALGORITHM_ERROR',
                'EDGE_CASE', 'TIME_COMPLEXITY', 'INPUT_OUTPUT', 'DATA_STRUCTURE', 'OTHER',
                name='errorcategory'
            ),
            nullable=False
        ),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('hint', sa.Text(), nullable=False),
        sa.Column('next_step', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_feedback_id'), 'ai_feedback', ['id'], unique=False)
    op.create_index(op.f('ix_ai_feedback_submission_id'), 'ai_feedback', ['submission_id'], unique=False)
    op.create_index(op.f('ix_ai_feedback_student_id'), 'ai_feedback', ['student_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_ai_feedback_student_id'), table_name='ai_feedback')
    op.drop_index(op.f('ix_ai_feedback_submission_id'), table_name='ai_feedback')
    op.drop_index(op.f('ix_ai_feedback_id'), table_name='ai_feedback')
    op.drop_table('ai_feedback')
