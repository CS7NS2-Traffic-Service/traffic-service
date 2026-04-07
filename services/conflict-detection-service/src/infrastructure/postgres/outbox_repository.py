from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from infrastructure.postgres.models.outbox_event import OutboxEvent


class PostgresOutboxRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def enqueue(self, stream: str, payload: dict, correlation_id: str) -> None:
        envelope = {
            'event_id': str(uuid4()),
            'correlation_id': correlation_id,
            'event_type': stream,
            'created_at': datetime.now(UTC).isoformat(),
            'data': payload,
        }
        self._db.add(OutboxEvent(stream=stream, payload=envelope))
