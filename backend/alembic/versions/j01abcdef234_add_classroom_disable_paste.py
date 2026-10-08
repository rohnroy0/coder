"""Add disable_paste column to classrooms

Revision ID: j01abcdef234
Revises: i90abcdef123
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'j01abcdef234'
down_revision: Union[str, None] = 'i90abcdef123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column(
        'classrooms',
        sa.Column('disable_paste', sa.Boolean(), nullable=False, server_default=sa.false())
    )

def downgrade() -> None:
    op.drop_column('classrooms', 'disable_paste')
