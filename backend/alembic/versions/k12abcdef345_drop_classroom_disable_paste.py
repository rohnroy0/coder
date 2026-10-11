"""Drop disable_paste column from classrooms

Revision ID: k12abcdef345
Revises: j01abcdef234
Create Date: 2026-10-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'k12abcdef345'
down_revision: Union[str, None] = 'j01abcdef234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.drop_column('classrooms', 'disable_paste')

def downgrade() -> None:
    op.add_column(
        'classrooms',
        sa.Column('disable_paste', sa.Boolean(), nullable=False, server_default=sa.false())
    )
