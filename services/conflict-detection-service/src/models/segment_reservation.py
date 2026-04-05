from database import BaseDBModel
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column


class SegmentReservation(BaseDBModel):
    __tablename__ = 'segment_reservations'

    reservation_id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default='gen_random_uuid()',
    )
    booking_id = mapped_column(UUID(as_uuid=True), nullable=False)
    segment_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('road_segments.segment_id'),
        nullable=False,
    )
    time_window_start = mapped_column(DateTime(timezone=True), nullable=False)
    time_window_end = mapped_column(DateTime(timezone=True), nullable=False)
