"""add edge_ids to road_segments

Revision ID: d4e5f6a7b8c9
Revises: c3f7a9b2d1e4
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = 'd4e5f6a7b8c9'
down_revision = 'c3f7a9b2d1e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('road_segments', sa.Column('edge_ids', JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column('road_segments', 'edge_ids')
