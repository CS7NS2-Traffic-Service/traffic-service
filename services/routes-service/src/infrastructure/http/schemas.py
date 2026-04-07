from datetime import datetime

from pydantic import BaseModel


class RouteQueryParams(BaseModel):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


class RouteResponse(BaseModel):
    route_id: str
    origin: str
    destination: str
    segment_ids: list[str] | None
    geometry: dict | None
    estimated_duration: int | None
    created_at: datetime


class SegmentResponse(BaseModel):
    segment_id: str
    osm_way_id: str | None
    name: str
    region: str
    capacity: int | None
    coordinates: dict | None
