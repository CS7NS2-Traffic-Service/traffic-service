from datetime import datetime

from pydantic import BaseModel


class AssessRouteRequest(BaseModel):
    booking_id: str
    route_id: str
    segment_ids: list[str]
    departure_time: datetime
    estimated_duration: int  # seconds


class AssessRouteResponse(BaseModel):
    booking_id: str
    route_id: str
    segments_available: bool


class SegmentUtilizationRequest(BaseModel):
    segment_ids: list[str]
    window_start: datetime
    window_end: datetime


class SegmentUtilizationItem(BaseModel):
    segment_id: str
    active_reservations: int


class SegmentUtilizationResponse(BaseModel):
    utilization: list[SegmentUtilizationItem]
