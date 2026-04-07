from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Route:
    route_id: str
    origin: str
    destination: str
    segment_ids: list[str] | None
    geometry: dict | None
    estimated_duration: int | None
    created_at: datetime
