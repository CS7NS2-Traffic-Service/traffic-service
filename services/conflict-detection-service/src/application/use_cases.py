from datetime import datetime

from domain.assessment import AssessmentResult

from application.interfaces import (
    OutboxRepository,
    ProcessedEventRepository,
    ReservationRepository,
    RouteRepository,
    SegmentRepository,
)


class AssessRouteUseCase:
    def __init__(
        self,
        route_repo: RouteRepository,
        segment_repo: SegmentRepository,
        reservation_repo: ReservationRepository,
        processed_event_repo: ProcessedEventRepository,
        outbox_repo: OutboxRepository,
    ) -> None:
        self._route_repo = route_repo
        self._segment_repo = segment_repo
        self._reservation_repo = reservation_repo
        self._processed_event_repo = processed_event_repo
        self._outbox_repo = outbox_repo

    def execute(
        self,
        booking_id: str,
        route_id: str,
        departure_time: datetime,
        event_id: str,
        consumer_name: str,
        stream_name: str,
        correlation_id: str,
    ) -> AssessmentResult:
        from application.conflict_service import ConflictService

        service = ConflictService(
            route_repo=self._route_repo,
            segment_repo=self._segment_repo,
            reservation_repo=self._reservation_repo,
        )

        result = service.assess_and_reserve(
            booking_id=booking_id,
            route_id=route_id,
            departure_time=departure_time,
        )

        self._processed_event_repo.mark_processed(event_id, consumer_name, stream_name)
        self._outbox_repo.enqueue(
            'route.assessed',
            {
                'booking_id': result.booking_id,
                'route_id': result.route_id,
                'segments_available': result.segments_available,
            },
            correlation_id,
        )

        return result


class ReleaseReservationsUseCase:
    def __init__(
        self,
        reservation_repo: ReservationRepository,
        processed_event_repo: ProcessedEventRepository,
    ) -> None:
        self._reservation_repo = reservation_repo
        self._processed_event_repo = processed_event_repo

    def execute(
        self,
        booking_id: str,
        event_id: str,
        consumer_name: str,
        stream_name: str,
    ) -> int:
        count = self._reservation_repo.delete_by_booking(booking_id)
        self._processed_event_repo.mark_processed(event_id, consumer_name, stream_name)
        return count
