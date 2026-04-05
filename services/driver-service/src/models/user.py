from database import BaseDBModel
from sqlalchemy import DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column


class Driver(BaseDBModel):
    __tablename__ = 'drivers'

    driver_id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default='gen_random_uuid()',
    )
    name = mapped_column(Text, nullable=False)
    email = mapped_column(Text, unique=True, nullable=False)
    password_hash = mapped_column(Text, nullable=False)
    license_number = mapped_column(Text, nullable=False)
    vehicle_type = mapped_column(Text, nullable=True)
    region = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default='now()')
