"""create all service tables

Revision ID: a1b2c3d4e5f6
Revises: b5e8a1c3d7f9
Create Date: 2026-03-20 10:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "b5e8a1c3d7f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column(
            "route_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("origin", sa.Text, nullable=False),
        sa.Column("destination", sa.Text, nullable=False),
        sa.Column("segment_ids", postgresql.ARRAY(sa.UUID), nullable=True),
        sa.Column("geometry", postgresql.JSONB, nullable=True),
        sa.Column("estimated_duration", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "road_segments",
        sa.Column(
            "segment_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("osm_way_id", sa.Text, nullable=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("region", sa.Text, nullable=False),
        sa.Column("capacity", sa.Integer, nullable=True),
        sa.Column("coordinates", postgresql.JSONB, nullable=True),
    )

    op.create_table(
        "bookings",
        sa.Column(
            "booking_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "driver_id",
            sa.UUID,
            sa.ForeignKey("drivers.driver_id"),
            nullable=False,
        ),
        sa.Column(
            "route_id",
            sa.UUID,
            sa.ForeignKey("routes.route_id"),
            nullable=False,
        ),
        sa.Column("departure_time", sa.DateTime, nullable=False),
        sa.Column("estimated_arrival", sa.DateTime, nullable=True),
        sa.Column(
            "status",
            sa.Text,
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "segment_reservations",
        sa.Column(
            "reservation_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "booking_id",
            sa.UUID,
            sa.ForeignKey("bookings.booking_id"),
            nullable=False,
        ),
        sa.Column(
            "segment_id",
            sa.UUID,
            sa.ForeignKey("road_segments.segment_id"),
            nullable=False,
        ),
        sa.Column("time_window_start", sa.DateTime, nullable=False),
        sa.Column("time_window_end", sa.DateTime, nullable=False),
    )

    op.create_table(
        "messages",
        sa.Column(
            "message_id",
            sa.UUID,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "driver_id",
            sa.UUID,
            sa.ForeignKey("drivers.driver_id"),
            nullable=False,
        ),
        sa.Column(
            "booking_id",
            sa.UUID,
            sa.ForeignKey("bookings.booking_id"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("read", sa.Boolean, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("segment_reservations")
    op.drop_table("bookings")
    op.drop_table("road_segments")
    op.drop_table("routes")
