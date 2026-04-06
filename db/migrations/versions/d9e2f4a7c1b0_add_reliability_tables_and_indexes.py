"""add reliability tables and indexes

Revision ID: d9e2f4a7c1b0
Revises: c3f7a9b2d1e4
Create Date: 2026-04-06 18:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d9e2f4a7c1b0"
down_revision: str | Sequence[str] | None = "c3f7a9b2d1e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processed_events",
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("consumer_name", sa.Text(), nullable=False),
        sa.Column("stream_name", sa.Text(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("event_id", "consumer_name"),
    )

    op.create_index(
        "ix_bookings_driver_created_at",
        "bookings",
        ["driver_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_bookings_driver_status",
        "bookings",
        ["driver_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_segment_reservations_segment_window",
        "segment_reservations",
        ["segment_id", "time_window_start", "time_window_end"],
        unique=False,
    )
    op.create_index(
        "ix_processed_events_processed_at",
        "processed_events",
        ["processed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_processed_events_processed_at", table_name="processed_events")
    op.drop_index("ix_segment_reservations_segment_window", table_name="segment_reservations")
    op.drop_index("ix_bookings_driver_status", table_name="bookings")
    op.drop_index("ix_bookings_driver_created_at", table_name="bookings")
    op.drop_table("processed_events")
