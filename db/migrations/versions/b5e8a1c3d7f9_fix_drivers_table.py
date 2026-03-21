"""fix drivers table schema

Revision ID: b5e8a1c3d7f9
Revises: 8c79182d1e1a
Create Date: 2026-03-20 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b5e8a1c3d7f9"
down_revision: str | Sequence[str] | None = "8c79182d1e1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("drivers")
    op.create_table(
        "drivers",
        sa.Column(
            "driver_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("email", sa.Text, nullable=False, unique=True),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("license_number", sa.Text, nullable=False),
        sa.Column("vehicle_type", sa.Text, nullable=True),
        sa.Column("region", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("drivers")
    op.create_table(
        "drivers",
        sa.Column("driver_id", sa.UUID, primary_key=True),
        sa.Column("username", sa.String, nullable=False),
        sa.Column("password", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
