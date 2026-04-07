from dataclasses import dataclass


@dataclass(frozen=True)
class AssessmentResult:
    booking_id: str
    route_id: str
    segments_available: bool
