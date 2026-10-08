"""Add learning_chapters and learning_chapter_problems models

Revision ID: i90abcdef123
Revises: h89abcdef012
Create Date: 2026-10-08 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'i90abcdef123'
down_revision: Union[str, None] = 'h89abcdef012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'learning_chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('language', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_chapters_id'), 'learning_chapters', ['id'], unique=False)
    op.create_index(op.f('ix_learning_chapters_language'), 'learning_chapters', ['language'], unique=False)

    op.create_table(
        'learning_chapter_problems',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('problem_id', sa.Integer(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['learning_chapters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['problem_id'], ['problems.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chapter_id', 'problem_id', name='uq_chapter_problem')
    )
    op.create_index(op.f('ix_learning_chapter_problems_id'), 'learning_chapter_problems', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_learning_chapter_problems_id'), table_name='learning_chapter_problems')
    op.drop_table('learning_chapter_problems')
    op.drop_index(op.f('ix_learning_chapters_language'), table_name='learning_chapters')
    op.drop_index(op.f('ix_learning_chapters_id'), table_name='learning_chapters')
    op.drop_table('learning_chapters')
