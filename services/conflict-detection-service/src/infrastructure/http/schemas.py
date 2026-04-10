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


class SegmentWindow(BaseModel):
    segment_id: str
    window_start: datetime
    window_end: datetime


class SegmentUtilizationRequest(BaseModel):
    segments: list[SegmentWindow]


class SegmentUtilizationItem(BaseModel):
    segment_id: str
    active_reservations: int


class SegmentUtilizationResponse(BaseModel):
    utilization: list[SegmentUtilizationItem]


class ReservationItem(BaseModel):
    reservation_id: str
    segment_id: str
    time_window_start: datetime
    time_window_end: datetime


class RouteCandidate(BaseModel):
    route_id: str
    segment_ids: list[str]
    estimated_duration: int


class RouteAvailabilityRequest(BaseModel):
    routes: list[RouteCandidate]
    departure_time: datetime


class RouteAvailabilityItem(BaseModel):
    route_id: str
    available: bool


class RouteAvailabilityResponse(BaseModel):
    routes: list[RouteAvailabilityItem]
