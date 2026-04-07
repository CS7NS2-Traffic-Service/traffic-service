from dataclasses import dataclass


@dataclass(frozen=True)
class RoadSegment:
    segment_id: str
    osm_way_id: str | None
    name: str
    region: str
    capacity: int | None
    coordinates: dict | None
    edge_ids: list[str] | None
