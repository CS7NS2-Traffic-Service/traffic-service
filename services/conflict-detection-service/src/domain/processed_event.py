from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProcessedEvent:
    event_id: str
    consumer_name: str
    stream_name: str
    processed_at: datetime | None = None
