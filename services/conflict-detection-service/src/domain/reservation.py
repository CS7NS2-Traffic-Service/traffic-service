from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Reservation:
    reservation_id: UUID
    segment_id: UUID
    time_window_start: datetime
    time_window_end: datetime
