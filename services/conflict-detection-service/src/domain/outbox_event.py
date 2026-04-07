from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OutboxEvent:
    id: int
    stream: str
    payload: dict
    created_at: datetime
    published: bool = False
