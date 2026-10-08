"""Add student_badges model

Revision ID: h89abcdef012
Revises: g789abcdef01
Create Date: 2026-10-08 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'h89abcdef012'
down_revision: Union[str, None] = 'g789abcdef01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'student_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('badge_code', sa.String(length=50), nullable=False),
        sa.Column('earned_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'badge_code', name='uq_student_badge')
    )
    op.create_index(op.f('ix_student_badges_id'), 'student_badges', ['id'], unique=False)
    op.create_index(op.f('ix_student_badges_student_id'), 'student_badges', ['student_id'], unique=False)
    op.create_index(op.f('ix_student_badges_badge_code'), 'student_badges', ['badge_code'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_student_badges_badge_code'), table_name='student_badges')
    op.drop_index(op.f('ix_student_badges_student_id'), table_name='student_badges')
    op.drop_index(op.f('ix_student_badges_id'), table_name='student_badges')
    op.drop_table('student_badges')
