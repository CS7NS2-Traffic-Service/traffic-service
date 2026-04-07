from datetime import datetime
from typing import Protocol

from domain.reservation import Reservation
from domain.route import Route


class RouteRepository(Protocol):
    def get_by_id(self, route_id: str) -> Route | None: ...


class SegmentRepository(Protocol):
    def get_capacities(self, segment_ids: list[str]) -> dict[str, int]: ...


class ReservationRepository(Protocol):
    def count_overlapping(
        self, segment_id: str, start: datetime, end: datetime
    ) -> int: ...

    def create(
        self,
        booking_id: str,
        segment_id: str,
        start: datetime,
        end: datetime,
    ) -> None: ...

    def delete_by_booking(self, booking_id: str) -> int: ...

    def get_by_booking(self, booking_id: str) -> list[Reservation]: ...

    def get_utilization(
        self,
        segment_ids: list[str],
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, int]: ...


class ProcessedEventRepository(Protocol):
    def mark_processed(
        self, event_id: str, consumer_name: str, stream_name: str
    ) -> None: ...


class OutboxRepository(Protocol):
    def enqueue(self, stream: str, payload: dict, correlation_id: str) -> None: ...
