"""Merge heads before feedback

Revision ID: 47a545eb8e5a
Revises: 011_fees_finance, phase85c_corrections
Create Date: 2026-02-08 09:23:47.528398

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47a545eb8e5a'
down_revision: Union[str, None] = ('011_fees_finance', 'phase85c_corrections')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
