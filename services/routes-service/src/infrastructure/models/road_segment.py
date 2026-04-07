from infrastructure.database import BaseDBModel
from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import mapped_column


class RoadSegment(BaseDBModel):
    __tablename__ = 'road_segments'

    segment_id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default='gen_random_uuid()',
    )
    osm_way_id = mapped_column(Text, nullable=True)
    name = mapped_column(Text, nullable=False)
    region = mapped_column(Text, nullable=False)
    capacity = mapped_column(Integer, nullable=True)
    coordinates = mapped_column(JSONB, nullable=True)
    edge_ids = mapped_column(JSONB, nullable=True)
