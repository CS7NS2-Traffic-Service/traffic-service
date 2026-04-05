"""use timestamptz for all datetime columns

Revision ID: c3f7a9b2d1e4
Revises: a1b2c3d4e5f6
Create Date: 2026-04-05 14:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3f7a9b2d1e4"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = [
    ("bookings", "departure_time"),
    ("bookings", "estimated_arrival"),
    ("bookings", "created_at"),
    ("bookings", "expires_at"),
    ("segment_reservations", "time_window_start"),
    ("segment_reservations", "time_window_end"),
    ("routes", "created_at"),
    ("drivers", "created_at"),
    ("messages", "created_at"),
]


def upgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(
            table,
            column,
            type_=op.get_bind().dialect.type_descriptor(
                __import__("sqlalchemy").DateTime(timezone=True)
            ),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    for table, column in COLUMNS:
        op.alter_column(
            table,
            column,
            type_=op.get_bind().dialect.type_descriptor(
                __import__("sqlalchemy").DateTime(timezone=False)
            ),
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
