from database import BaseDBModel
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column


class Booking(BaseDBModel):
    __tablename__ = 'bookings'

    booking_id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default='gen_random_uuid()',
    )
    driver_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('drivers.driver_id'),
        nullable=False,
    )
    route_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('routes.route_id'),
        nullable=False,
    )
    departure_time = mapped_column(DateTime, nullable=False)
    estimated_arrival = mapped_column(DateTime, nullable=True)
    status = mapped_column(Text, nullable=False, server_default="'PENDING'")
    created_at = mapped_column(DateTime, server_default='now()')
    expires_at = mapped_column(DateTime, nullable=True)
