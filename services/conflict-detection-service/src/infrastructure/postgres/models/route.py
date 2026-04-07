from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import mapped_column

from infrastructure.database import BaseDBModel


class Route(BaseDBModel):
    __tablename__ = 'routes'

    route_id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default='gen_random_uuid()',
    )
    origin = mapped_column(Text, nullable=False)
    destination = mapped_column(Text, nullable=False)
    segment_ids = mapped_column(ARRAY(UUID), nullable=True)
    geometry = mapped_column(JSONB, nullable=True)
    estimated_duration = mapped_column(Integer, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default='now()')
