from sqlalchemy.orm import Session

from infrastructure.postgres.models.processed_event import ProcessedEvent


class PostgresProcessedEventRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def mark_processed(
        self, event_id: str, consumer_name: str, stream_name: str
    ) -> None:
        self._db.add(
            ProcessedEvent(
                event_id=event_id,
                consumer_name=consumer_name,
                stream_name=stream_name,
            )
        )
