"""merge edge_ids and reliability migrations

Revision ID: b3be682de187
Revises: d4e5f6a7b8c9, d9e2f4a7c1b0
Create Date: 2026-04-07 00:07:45.159934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3be682de187'
down_revision: Union[str, Sequence[str], None] = ('d4e5f6a7b8c9', 'd9e2f4a7c1b0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
