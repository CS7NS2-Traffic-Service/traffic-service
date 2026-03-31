from database import BaseDBModel
from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column


class Message(BaseDBModel):
    __tablename__ = 'messages'

    message_id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default='gen_random_uuid()',
    )
    driver_id = mapped_column(UUID(as_uuid=True), nullable=False)
    booking_id = mapped_column(UUID(as_uuid=True), nullable=False)
    content = mapped_column(Text, nullable=False)
    is_read = mapped_column('read', Boolean, server_default='false')
    created_at = mapped_column(DateTime, server_default='now()')
