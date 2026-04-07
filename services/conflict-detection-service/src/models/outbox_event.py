from datetime import UTC, datetime

from database import BaseDBModel
from sqlalchemy import BigInteger, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class OutboxEvent(BaseDBModel):
    __tablename__ = 'outbox_events'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stream: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
