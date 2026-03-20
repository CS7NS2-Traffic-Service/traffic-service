"""create driver table

Revision ID: 8c79182d1e1a
Revises:
Create Date: 2026-03-19 14:39:06.345745

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c79182d1e1a"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drivers",
        sa.Column("driver_id", sa.UUID, primary_key=True),
        sa.Column("username", sa.String, nullable=False),
        sa.Column("password", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
