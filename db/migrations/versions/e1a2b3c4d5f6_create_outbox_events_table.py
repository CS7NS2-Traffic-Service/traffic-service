"""create outbox_events table

Revision ID: e1a2b3c4d5f6
Revises: b3be682de187
Create Date: 2026-04-07 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = 'e1a2b3c4d5f6'
down_revision: str | Sequence[str] | None = 'b3be682de187'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('stream', sa.Text, nullable=False),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published', sa.Boolean, server_default=sa.text('false'), nullable=False),
    )
    op.create_index(
        'idx_outbox_events_unpublished',
        'outbox_events',
        ['id'],
        postgresql_where=sa.text('published = false'),
    )


def downgrade() -> None:
    op.drop_index('idx_outbox_events_unpublished', table_name='outbox_events')
    op.drop_table('outbox_events')
