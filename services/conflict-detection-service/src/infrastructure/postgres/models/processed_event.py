from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import BaseDBModel


class ProcessedEvent(BaseDBModel):
    __tablename__ = 'processed_events'

    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    consumer_name: Mapped[str] = mapped_column(Text, primary_key=True)
    stream_name: Mapped[str] = mapped_column(Text, nullable=False)
    processed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
