from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    route_id: str
    segment_ids: list[str]
    estimated_duration: int
