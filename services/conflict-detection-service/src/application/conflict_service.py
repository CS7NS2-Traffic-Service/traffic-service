import logging
from datetime import datetime, timedelta

from domain.assessment import AssessmentResult
from domain.reservation import Reservation

from application.interfaces import (
    ReservationRepository,
    RouteRepository,
    SegmentRepository,
)

logger = logging.getLogger(__name__)

SEGMENT_OFFSET_SECONDS = 300


class ConflictService:
    def __init__(
        self,
        route_repo: RouteRepository,
        segment_repo: SegmentRepository,
        reservation_repo: ReservationRepository,
    ) -> None:
        self._routes = route_repo
        self._segments = segment_repo
        self._reservations = reservation_repo

    def assess_and_reserve(
        self,
        booking_id: str,
        route_id: str,
        departure_time: datetime,
    ) -> AssessmentResult:
        route = self._routes.get_by_id(route_id)
        if route is None:
            logger.warning('Route %s not found', route_id)
            return AssessmentResult(
                booking_id=booking_id,
                route_id=route_id,
                segments_available=False,
            )

        segment_ids = route.segment_ids
        duration = route.estimated_duration

        if not segment_ids:
            return AssessmentResult(
                booking_id=booking_id,
                route_id=route_id,
                segments_available=True,
            )

        sorted_ids = sorted(segment_ids)
        capacities = self._segments.get_capacities(sorted_ids)

        if len(capacities) != len(segment_ids):
            return AssessmentResult(
                booking_id=booking_id,
                route_id=route_id,
                segments_available=False,
            )

        for index, segment_id in enumerate(segment_ids):
            offset = timedelta(seconds=SEGMENT_OFFSET_SECONDS * index)
            start = departure_time + offset
            end = start + timedelta(seconds=duration)
            overlap = self._reservations.count_overlapping(segment_id, start, end)
            if overlap >= capacities[segment_id]:
                return AssessmentResult(
                    booking_id=booking_id,
                    route_id=route_id,
                    segments_available=False,
                )

        for index, segment_id in enumerate(segment_ids):
            offset = timedelta(seconds=SEGMENT_OFFSET_SECONDS * index)
            start = departure_time + offset
            end = start + timedelta(seconds=duration)
            self._reservations.create(booking_id, segment_id, start, end)

        return AssessmentResult(
            booking_id=booking_id,
            route_id=route_id,
            segments_available=True,
        )

    def release_reservations(self, booking_id: str) -> int:
        return self._reservations.delete_by_booking(booking_id)

    def get_segment_utilization(
        self,
        segment_ids: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, int]:
        return self._reservations.get_utilization(segment_ids, window_start, window_end)

    def get_reservations_by_booking(self, booking_id: str) -> list[Reservation]:
        return self._reservations.get_by_booking(booking_id)
